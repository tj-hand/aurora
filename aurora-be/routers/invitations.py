"""Invitation management API endpoints"""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

# Use Matrix infrastructure (Layer 0)
from src.database import get_db

# Use Mentor dependencies (Layer 3) for auth and permissions
from src.modules.mentor.dependencies.auth import CurrentUser
from src.modules.mentor.dependencies.tenant import TenantContext
from src.modules.mentor.dependencies.permissions import require_permission

from ..config import aurora_config
from ..models.invitation import InvitationStatus
from ..schemas.invitation import (
    InvitationCreate,
    InvitationRead,
    InvitationList,
    InvitationFilter,
    InvitationAccept,
    InvitationAcceptResponse,
    InvitationResendResponse,
    InvitationRevokeResponse,
    InvitationStats,
)
from ..services.invitation_service import InvitationService

router = APIRouter()


@router.get(
    "",
    response_model=InvitationList,
    summary="List invitations",
    description="List invitations with filtering and pagination. Requires aurora.invitations.view permission.",
)
async def list_invitations(
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.view")),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    # Filters
    status: Optional[InvitationStatus] = Query(None, description="Filter by status"),
    email: Optional[str] = Query(None, max_length=255, description="Filter by email"),
    invited_by: Optional[UUID] = Query(None, description="Filter by inviter"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date"),
) -> InvitationList:
    """List invitations with filtering and pagination"""
    service = InvitationService(db)

    filter_obj = InvitationFilter(
        status=status,
        email=email,
        invited_by=invited_by,
        created_after=created_after,
        created_before=created_before,
    )

    return await service.list(
        tenant_id=tenant.tenant_id,
        filter=filter_obj,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats",
    response_model=InvitationStats,
    summary="Get invitation statistics",
    description="Get invitation statistics for the current tenant. Requires aurora.invitations.view permission.",
)
async def get_stats(
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.view")),
) -> InvitationStats:
    """Get invitation statistics for the tenant"""
    service = InvitationService(db)
    return await service.get_stats(tenant.tenant_id)


@router.get(
    "/{invitation_id}",
    response_model=InvitationRead,
    summary="Get invitation details",
    description="Get a single invitation by ID. Requires aurora.invitations.view permission.",
)
async def get_invitation(
    invitation_id: UUID,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.view")),
) -> InvitationRead:
    """Get a single invitation by ID"""
    service = InvitationService(db)

    invitation = await service.get(invitation_id, tenant.tenant_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    return InvitationRead.model_validate(invitation)


@router.post(
    "",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create invitation",
    description="Create a new invitation and send email. Requires aurora.invitations.create permission.",
)
async def create_invitation(
    invitation_data: InvitationCreate,
    request: Request,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.create")),
) -> InvitationRead:
    """Create a new invitation"""
    service = InvitationService(db)

    try:
        invitation, raw_token = await service.create(
            email=invitation_data.email,
            tenant_id=tenant.tenant_id,
            invited_by=current_user.id,
            name=invitation_data.name,
            client_ids=invitation_data.client_ids,
            role_group_ids=invitation_data.role_group_ids,
            message=invitation_data.message,
        )

        # Send invitation email
        await service.send_invitation_email(
            invitation=invitation,
            token=raw_token,
            tenant_name=tenant.tenant_name or "Your Organization",
            inviter_name=current_user.name,
        )

        # Log to Reel
        try:
            from src.modules.reel import get_reel_service
            reel = get_reel_service(db)
            await reel.log(
                module="aurora",
                action="invitations.create",
                tenant_id=tenant.tenant_id,
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_name=current_user.name,
                resource_type="invitation",
                resource_id=invitation.id,
                data={"email": invitation.email},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except ImportError:
            pass  # Reel not installed

        return InvitationRead.model_validate(invitation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{invitation_id}/resend",
    response_model=InvitationResendResponse,
    summary="Resend invitation",
    description="Resend invitation email with new token. Requires aurora.invitations.create permission.",
)
async def resend_invitation(
    invitation_id: UUID,
    request: Request,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.create")),
) -> InvitationResendResponse:
    """Resend invitation email"""
    service = InvitationService(db)

    try:
        invitation, raw_token = await service.resend(invitation_id, tenant.tenant_id)

        # Send email
        email_sent = await service.send_invitation_email(
            invitation=invitation,
            token=raw_token,
            tenant_name=tenant.tenant_name or "Your Organization",
            inviter_name=current_user.name,
        )

        # Log to Reel
        try:
            from src.modules.reel import get_reel_service
            reel = get_reel_service(db)
            await reel.log(
                module="aurora",
                action="invitations.resend",
                tenant_id=tenant.tenant_id,
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_name=current_user.name,
                resource_type="invitation",
                resource_id=invitation.id,
                data={"email": invitation.email},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except ImportError:
            pass

        return InvitationResendResponse(
            success=email_sent,
            message="Invitation email resent" if email_sent else "Failed to send email",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{invitation_id}/revoke",
    response_model=InvitationRevokeResponse,
    summary="Revoke invitation",
    description="Revoke a pending invitation. Requires aurora.invitations.revoke permission.",
)
async def revoke_invitation(
    invitation_id: UUID,
    request: Request,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("aurora.invitations.revoke")),
) -> InvitationRevokeResponse:
    """Revoke a pending invitation"""
    service = InvitationService(db)

    try:
        invitation = await service.revoke(
            invitation_id=invitation_id,
            tenant_id=tenant.tenant_id,
            revoked_by=current_user.id,
        )

        # Log to Reel
        try:
            from src.modules.reel import get_reel_service
            reel = get_reel_service(db)
            await reel.log(
                module="aurora",
                action="invitations.revoke",
                tenant_id=tenant.tenant_id,
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_name=current_user.name,
                resource_type="invitation",
                resource_id=invitation.id,
                data={"email": invitation.email},
                severity="WARNING",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except ImportError:
            pass

        return InvitationRevokeResponse(
            success=True,
            message="Invitation revoked",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/accept",
    response_model=InvitationAcceptResponse,
    summary="Accept invitation",
    description="Accept an invitation using the token. Requires authenticated user.",
)
async def accept_invitation(
    accept_data: InvitationAccept,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvitationAcceptResponse:
    """
    Accept an invitation.

    The user must be authenticated. After acceptance:
    - User is associated with the tenant
    - User is assigned to specified clients
    - User is assigned specified role groups
    """
    service = InvitationService(db)

    try:
        invitation = await service.accept(
            token=accept_data.token,
            user_id=current_user.id,
        )

        # Create user-tenant association via Mentor
        try:
            from src.modules.mentor.services import TenantService
            tenant_service = TenantService(db)

            # Associate user with tenant
            await tenant_service.add_user_to_tenant(
                user_id=current_user.id,
                tenant_id=invitation.tenant_id,
            )

            # Associate user with clients if specified
            if invitation.client_ids:
                for client_id in invitation.client_ids:
                    await tenant_service.add_user_to_client(
                        user_id=current_user.id,
                        client_id=client_id,
                    )

            # Assign role groups if specified
            if invitation.role_group_ids:
                from src.modules.mentor.services import RoleService
                role_service = RoleService(db)
                for role_group_id in invitation.role_group_ids:
                    await role_service.assign_role_group_to_user(
                        user_id=current_user.id,
                        role_group_id=role_group_id,
                        tenant_id=invitation.tenant_id,
                    )

            tenant = await tenant_service.get(invitation.tenant_id)
            tenant_name = tenant.name if tenant else None

        except ImportError:
            tenant_name = None

        # Log to Reel
        try:
            from src.modules.reel import get_reel_service
            reel = get_reel_service(db)
            await reel.log(
                module="aurora",
                action="invitations.accept",
                tenant_id=invitation.tenant_id,
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_name=current_user.name,
                resource_type="invitation",
                resource_id=invitation.id,
                data={"email": invitation.email},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except ImportError:
            pass

        return InvitationAcceptResponse(
            success=True,
            message="Invitation accepted successfully",
            tenant_id=invitation.tenant_id,
            tenant_name=tenant_name,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
