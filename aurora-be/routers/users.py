"""Aurora Users Router

Handles user CRUD operations, orchestrating Guardian and Mentor.

Endpoints:
    POST   /users         - Create user (Guardian + Mentor)
    GET    /users         - List users for tenant
    GET    /users/{id}    - Get user details
    PUT    /users/{id}    - Update user
    DELETE /users/{id}    - Deactivate user (soft delete)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

# Matrix infrastructure
from src.database import get_db

# Aurora imports
from ..dependencies import CurrentUser, TenantContext
from ..schemas import UserCreate, UserUpdate, UserResponse, UserListResponse
from ..services import UserService

router = APIRouter(prefix="/users", tags=["aurora-users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a user identity in Guardian and links them to the current tenant in Mentor.",
)
async def create_user(
    request: UserCreate,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new user for the current tenant.

    Orchestrates:
    1. Guardian: Create user identity (guardian_users)
    2. Mentor: Create tenant association (user_tenant_associations)

    Requires: Tenant admin or superadmin
    """
    # Only tenant admins can create users
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can create users",
        )

    service = UserService(db)

    try:
        user, association = await service.create_user(
            email=request.email,
            tenant_id=tenant_context.tenant_id,
            user_level=request.user_level.value,
            created_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        user_level=association.user_level.value,
        is_active=association.is_active,
        tenant_id=association.tenant_id,
        association_id=association.id,
        created_at=association.created_at,
        updated_at=association.updated_at,
    )


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="List all users for the current tenant with pagination.",
)
async def list_users(
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    include_inactive: bool = Query(default=False, description="Include deactivated users"),
):
    """
    List users for the current tenant.

    Requires: Authenticated user with tenant access
    """
    service = UserService(db)

    users, total = await service.list_users(
        tenant_id=tenant_context.tenant_id,
        page=page,
        per_page=per_page,
        include_inactive=include_inactive,
    )

    return UserListResponse(
        users=[UserResponse(**u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(page * per_page) < total,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details",
    description="Get details of a specific user in the current tenant.",
)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get user details.

    Requires: Authenticated user with tenant access
    """
    service = UserService(db)

    user = await service.get_user(
        user_id=user_id,
        tenant_id=tenant_context.tenant_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this tenant",
        )

    return UserResponse(**user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update a user's level or status in the current tenant.",
)
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update user in the current tenant.

    Requires: Tenant admin or superadmin
    """
    # Only tenant admins can update users
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can update users",
        )

    # Prevent self-demotion
    if user_id == current_user.id and request.user_level == "simple_user":
        if tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself",
            )

    service = UserService(db)

    user = await service.update_user(
        user_id=user_id,
        tenant_id=tenant_context.tenant_id,
        user_level=request.user_level.value if request.user_level else None,
        is_active=request.is_active,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this tenant",
        )

    return UserResponse(**user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user",
    description="Deactivate a user's association with the current tenant (soft delete).",
)
async def deactivate_user(
    user_id: UUID,
    current_user: CurrentUser,
    tenant_context: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Deactivate user from the current tenant.

    This soft-deletes the UserTenantAssociation, not the Guardian user.
    The user can be re-added later if needed.

    Requires: Tenant admin or superadmin
    """
    # Only tenant admins can deactivate users
    if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can deactivate users",
        )

    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    service = UserService(db)

    success = await service.deactivate_user(
        user_id=user_id,
        tenant_id=tenant_context.tenant_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this tenant",
        )

    return None
