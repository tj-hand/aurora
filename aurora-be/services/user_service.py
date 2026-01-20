"""Aurora User Service

Orchestrates Guardian and Mentor to manage users.

Aurora Flow:
    1. Guardian: Create/manage user identity (guardian_users)
    2. Mentor: Link user to tenant (user_tenant_associations)
    3. Aurora: Coordinate the orchestration
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user management orchestrating Guardian + Mentor.

    Responsibilities:
    - Create users (Guardian identity + Mentor association)
    - List users for a tenant
    - Get user details
    - Update user (level, status)
    - Deactivate users (soft delete)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize UserService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create_user(
        self,
        email: str,
        tenant_id: UUID,
        user_level: str,
        created_by: UUID,
    ) -> Tuple["User", "UserTenantAssociation"]:
        """
        Create a new user with tenant association.

        Orchestrates:
        1. Guardian: get_or_create_user (identity)
        2. Mentor: create UserTenantAssociation (authorization)

        Args:
            email: User email address
            tenant_id: Tenant to associate user with
            user_level: User level (tenant_admin or simple_user)
            created_by: ID of user creating this user

        Returns:
            Tuple of (User, UserTenantAssociation)

        Raises:
            ValueError: If user already associated with tenant
        """
        from src.services.guardian import get_guardian_service
        from src.modules.mentor.models.user_tenant_association import (
            UserTenantAssociation,
            UserLevel,
        )

        # 1. Guardian: Create/get user identity
        guardian_service = get_guardian_service()
        user = await guardian_service.get_or_create_user(self.db, email)

        logger.info(f"Guardian user: {user.id} ({user.email})")

        # 2. Check if association already exists
        existing = await self._get_association(user.id, tenant_id)
        if existing and existing.deleted_at is None:
            raise ValueError(f"User {email} is already associated with this tenant")

        # 3. Mentor: Create tenant association
        level_enum = UserLevel(user_level)
        association = UserTenantAssociation(
            user_id=user.id,
            tenant_id=tenant_id,
            user_level=level_enum,
            created_by=created_by,
            is_active=True,
        )

        self.db.add(association)
        await self.db.commit()
        await self.db.refresh(association)

        logger.info(
            f"Created association: user={user.id}, tenant={tenant_id}, level={user_level}"
        )

        return user, association

    async def list_users(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
        include_inactive: bool = False,
    ) -> Tuple[List[dict], int]:
        """
        List users for a tenant with pagination.

        Args:
            tenant_id: Tenant ID to list users for
            page: Page number (1-indexed)
            per_page: Items per page
            include_inactive: Include deactivated users

        Returns:
            Tuple of (list of user dicts, total count)
        """
        from src.models.guardian import User
        from src.modules.mentor.models.user_tenant_association import (
            UserTenantAssociation,
        )

        # Build base query
        query = (
            select(User, UserTenantAssociation)
            .join(
                UserTenantAssociation,
                User.id == UserTenantAssociation.user_id,
            )
            .where(UserTenantAssociation.tenant_id == tenant_id)
            .where(UserTenantAssociation.deleted_at.is_(None))
        )

        if not include_inactive:
            query = query.where(UserTenantAssociation.is_active == True)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        query = query.order_by(User.email)

        result = await self.db.execute(query)
        rows = result.all()

        users = []
        for user, association in rows:
            users.append({
                "id": user.id,
                "email": user.email,
                "user_level": association.user_level.value,
                "is_active": association.is_active,
                "tenant_id": association.tenant_id,
                "association_id": association.id,
                "created_at": association.created_at,
                "updated_at": association.updated_at,
            })

        return users, total

    async def get_user(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> Optional[dict]:
        """
        Get user details for a specific tenant.

        Args:
            user_id: User ID (Guardian user ID)
            tenant_id: Tenant ID

        Returns:
            User dict if found, None otherwise
        """
        from src.models.guardian import User
        from src.modules.mentor.models.user_tenant_association import (
            UserTenantAssociation,
        )

        query = (
            select(User, UserTenantAssociation)
            .join(
                UserTenantAssociation,
                User.id == UserTenantAssociation.user_id,
            )
            .where(User.id == user_id)
            .where(UserTenantAssociation.tenant_id == tenant_id)
            .where(UserTenantAssociation.deleted_at.is_(None))
        )

        result = await self.db.execute(query)
        row = result.first()

        if not row:
            return None

        user, association = row
        return {
            "id": user.id,
            "email": user.email,
            "user_level": association.user_level.value,
            "is_active": association.is_active,
            "tenant_id": association.tenant_id,
            "association_id": association.id,
            "created_at": association.created_at,
            "updated_at": association.updated_at,
        }

    async def update_user(
        self,
        user_id: UUID,
        tenant_id: UUID,
        user_level: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[dict]:
        """
        Update user association for a tenant.

        Args:
            user_id: User ID (Guardian user ID)
            tenant_id: Tenant ID
            user_level: New user level (optional)
            is_active: New active status (optional)

        Returns:
            Updated user dict if found, None otherwise
        """
        from src.modules.mentor.models.user_tenant_association import (
            UserTenantAssociation,
            UserLevel,
        )

        association = await self._get_association(user_id, tenant_id)
        if not association or association.deleted_at is not None:
            return None

        if user_level is not None:
            association.user_level = UserLevel(user_level)

        if is_active is not None:
            association.is_active = is_active

        await self.db.commit()
        await self.db.refresh(association)

        logger.info(f"Updated user {user_id} in tenant {tenant_id}")

        return await self.get_user(user_id, tenant_id)

    async def deactivate_user(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """
        Deactivate user association (soft delete).

        Does not delete the Guardian user identity, only the
        Mentor tenant association.

        Args:
            user_id: User ID (Guardian user ID)
            tenant_id: Tenant ID

        Returns:
            True if deactivated, False if not found
        """
        from datetime import datetime, timezone

        association = await self._get_association(user_id, tenant_id)
        if not association or association.deleted_at is not None:
            return False

        association.is_active = False
        association.deleted_at = datetime.now(timezone.utc)

        await self.db.commit()

        logger.info(f"Deactivated user {user_id} from tenant {tenant_id}")

        return True

    async def _get_association(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> Optional["UserTenantAssociation"]:
        """
        Get UserTenantAssociation by user and tenant IDs.

        Args:
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            UserTenantAssociation if found, None otherwise
        """
        from src.modules.mentor.models.user_tenant_association import (
            UserTenantAssociation,
        )

        query = select(UserTenantAssociation).where(
            UserTenantAssociation.user_id == user_id,
            UserTenantAssociation.tenant_id == tenant_id,
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
