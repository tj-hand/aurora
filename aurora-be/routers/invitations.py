"""Aurora Invitations Router

Handles invitation CRUD operations for user onboarding.

Endpoints:
    POST   /invitations              - Create invitation
    POST   /invitations/bulk         - Create multiple invitations
    GET    /invitations              - List invitations for tenant
    GET    /invitations/{id}         - Get invitation details
    GET    /invitations/token/{token} - Get invitation by token (public)
    POST   /invitations/{id}/resend  - Resend invitation email
    POST   /invitations/{id}/revoke  - Revoke invitation
    POST   /invitations/accept/{token} - Accept invitation (public)
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

# Matrix infrastructure
from src.database import get_db

# Aurora imports
from ..dependencies import CurrentUser, TenantContext, get_current_user_optional
from ..schemas import (
    InvitationCreate,
    InvitationResend,
    InvitationRevoke,
    InvitationBulkCreate,
    InvitationResponse,
    InvitationListResponse,
    InvitationBulkResult,
    InvitationTokenInfo,
    InvitationStatus,
)
from ..services import InvitationService
from ..models import Invitation

router = APIRouter(prefix="/invitations", tags=["aurora-invitations"])


@router.post(
    "",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invitation",
    description="Create a new invitation to invite a user to the current tenant.",
)
async def create_invitation(
    request: InvitationCreate,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    send_email: bool = Query(default=True, description="Send invitation email immediately"),
):
    """
    Create a new invitation for the current tenant.

    The invitation will be sent via email if send_email is True.

    Requires: Tenant admin or superadmin
    """
    # Only tenant admins can create invitations
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can create invitations",
        )

    service = InvitationService(db)

    try:
        invitation = await service.create(
            tenant_id=tenant_context.tenant_id,
            invited_by=current_user.id,
            data=request,
            tenant_slug=tenant_context.tenant_slug,
            invited_by_email=current_user.email,
            client_slug=None,  # Could be enhanced with client context
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Send invitation email
    if send_email:
        await service.send_email(invitation)

    return InvitationResponse(**invitation.to_dict())


@router.post(
    "/bulk",
    response_model=InvitationBulkResult,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple invitations",
    description="Create multiple invitations at once (max 50).",
)
async def create_invitations_bulk(
    request: InvitationBulkCreate,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    send_emails: bool = Query(default=True, description="Send invitation emails"),
):
    """
    Create multiple invitations at once.

    Returns a result object with both successful and failed invitations.

    Requires: Tenant admin or superadmin
    """
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can create invitations",
        )

    service = InvitationService(db)

    result = await service.create_bulk(
        tenant_id=tenant_context.tenant_id,
        invited_by=current_user.id,
        data=request,
        tenant_slug=tenant_context.tenant_slug,
        invited_by_email=current_user.email,
    )

    # Send emails for created invitations
    if send_emails:
        for inv_response in result.created:
            invitation = await service.get_by_id(inv_response.id)
            if invitation:
                await service.send_email(invitation)

    return result


@router.get(
    "",
    response_model=InvitationListResponse,
    summary="List invitations",
    description="List all invitations for the current tenant with pagination.",
)
async def list_invitations(
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[InvitationStatus] = Query(
        default=None,
        alias="status",
        description="Filter by invitation status"
    ),
    search: Optional[str] = Query(default=None, description="Search by email or name"),
    client_id: Optional[UUID] = Query(default=None, description="Filter by client"),
):
    """
    List invitations for the current tenant.

    Supports filtering by status and searching by email/name.
    """
    service = InvitationService(db)

    # Convert schema enum to model enum if provided
    model_status = None
    if status_filter:
        from ..models.invitation import InvitationStatus as ModelStatus
        try:
            model_status = ModelStatus(status_filter.value)
        except ValueError:
            pass  # Invalid status, ignore filter

    invitations, total = await service.list(
        tenant_id=tenant_context.tenant_id,
        page=page,
        per_page=per_page,
        status=model_status,
        search=search,
        client_id=client_id,
    )

    return InvitationListResponse(
        invitations=[InvitationResponse(**inv.to_dict()) for inv in invitations],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.get(
    "/{invitation_id}",
    response_model=InvitationResponse,
    summary="Get invitation details",
    description="Get details of a specific invitation.",
)
async def get_invitation(
    invitation_id: UUID,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get invitation details by ID.

    Only returns invitations belonging to the current tenant.
    """
    service = InvitationService(db)

    invitation = await service.get_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Verify tenant access
    if invitation.tenant_id != tenant_context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return InvitationResponse(**invitation.to_dict())


@router.get(
    "/token/{token}",
    response_model=InvitationTokenInfo,
    summary="Get invitation info by token",
    description="Get public information about an invitation from its token (no auth required).",
)
async def get_invitation_by_token(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get public invitation information by token.

    This endpoint is public and used for the invitation acceptance page.
    Returns limited information about the invitation.
    """
    service = InvitationService(db)

    invitation = await service.get_by_token(token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token",
        )

    return InvitationTokenInfo(
        email=invitation.email,
        tenant_slug=invitation.tenant_slug,
        invited_by_email=invitation.invited_by_email,
        expires_at=invitation.expires_at,
        is_valid=invitation.is_valid,
        message=invitation.message,
    )


@router.post(
    "/{invitation_id}/resend",
    response_model=InvitationResponse,
    summary="Resend invitation email",
    description="Resend the invitation email to the invitee.",
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: InvitationResend = None,
):
    """
    Resend an invitation email.

    Can optionally include a custom message override.

    Requires: Tenant admin or superadmin
    """
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can resend invitations",
        )

    service = InvitationService(db)

    invitation = await service.get_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.tenant_id != tenant_context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    try:
        custom_message = request.custom_message if request else None
        invitation = await service.resend_email(invitation, custom_message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return InvitationResponse(**invitation.to_dict())


@router.post(
    "/{invitation_id}/revoke",
    response_model=InvitationResponse,
    summary="Revoke invitation",
    description="Revoke a pending invitation.",
)
async def revoke_invitation(
    invitation_id: UUID,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: InvitationRevoke = None,
):
    """
    Revoke an invitation.

    Can optionally include a reason for the revocation.

    Requires: Tenant admin or superadmin
    """
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can revoke invitations",
        )

    service = InvitationService(db)

    invitation = await service.get_by_id(invitation_id)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.tenant_id != tenant_context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    try:
        reason = request.reason if request else None
        invitation = await service.revoke(
            invitation=invitation,
            revoked_by=current_user.id,
            reason=reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return InvitationResponse(**invitation.to_dict())


@router.post(
    "/accept/{token}",
    response_model=InvitationResponse,
    summary="Accept invitation",
    description="Accept an invitation and join the tenant.",
)
async def accept_invitation(
    token: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Accept an invitation using its token.

    This endpoint requires authentication. The authenticated user
    will be associated with the tenant specified in the invitation.

    The email of the authenticated user must match the invitation email.
    """
    service = InvitationService(db)

    invitation = await service.get_by_token(token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token",
        )

    # Verify email matches
    if current_user.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address",
        )

    try:
        invitation = await service.accept(
            invitation=invitation,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return InvitationResponse(**invitation.to_dict())
