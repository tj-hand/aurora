"""InvitationService - Core service for invitation management"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import aurora_config
from ..models.invitation import Invitation, InvitationStatus
from ..schemas.invitation import (
    InvitationCreate,
    InvitationRead,
    InvitationList,
    InvitationFilter,
    InvitationStats,
)

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for managing user invitations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_provider = None
        self._reel_service = None

    @property
    def email_provider(self):
        """Lazy-load email provider from Matrix"""
        if self._email_provider is None:
            from src.providers.email import get_email_provider
            self._email_provider = get_email_provider()
        return self._email_provider

    def generate_token(self) -> str:
        """Generate a cryptographically secure invitation token"""
        return secrets.token_urlsafe(aurora_config.token_length)

    def hash_token(self, token: str) -> str:
        """Hash token using SHA-256 for secure storage"""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def create(
        self,
        *,
        email: str,
        tenant_id: UUID,
        invited_by: UUID,
        name: Optional[str] = None,
        client_ids: Optional[list[UUID]] = None,
        role_group_ids: Optional[list[UUID]] = None,
        message: Optional[str] = None,
    ) -> tuple[Invitation, str]:
        """
        Create a new invitation.

        Returns:
            Tuple of (invitation, raw_token)
        """
        # Check for existing pending invitation
        existing = await self._get_pending_by_email(email, tenant_id)
        if existing:
            raise ValueError(f"Pending invitation already exists for {email}")

        # Generate token
        raw_token = self.generate_token()
        token_hash = self.hash_token(raw_token)

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=aurora_config.invitation_expiry_days
        )

        invitation = Invitation(
            email=email.lower(),
            name=name,
            tenant_id=tenant_id,
            client_ids=client_ids,
            role_group_ids=role_group_ids,
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            token_hash=token_hash,
            expires_at=expires_at,
            message=message,
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation, raw_token

    async def get(self, invitation_id: UUID, tenant_id: UUID) -> Optional[Invitation]:
        """Get an invitation by ID (scoped to tenant)"""
        result = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.id == invitation_id,
                    Invitation.tenant_id == tenant_id,
                    Invitation.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Optional[Invitation]:
        """Get an invitation by raw token"""
        token_hash = self.hash_token(token)
        result = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.token_hash == token_hash,
                    Invitation.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_pending_by_email(
        self, email: str, tenant_id: UUID
    ) -> Optional[Invitation]:
        """Get pending invitation for email in tenant"""
        result = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.email == email.lower(),
                    Invitation.tenant_id == tenant_id,
                    Invitation.status == InvitationStatus.PENDING,
                    Invitation.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: UUID,
        filter: Optional[InvitationFilter] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> InvitationList:
        """List invitations with filtering and pagination"""
        page_size = min(page_size, aurora_config.max_page_size)
        page = max(page, 1)

        # Base query
        query = select(Invitation).where(
            and_(
                Invitation.tenant_id == tenant_id,
                Invitation.deleted_at.is_(None),
            )
        )

        # Apply filters
        if filter:
            query = self._apply_filters(query, filter)

        # Order by created_at DESC
        query = query.order_by(Invitation.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute
        result = await self.db.execute(query)
        invitations = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return InvitationList(
            items=[InvitationRead.model_validate(i) for i in invitations],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def _apply_filters(self, query, filter: InvitationFilter):
        """Apply filter conditions to query"""
        conditions = []

        if filter.status:
            conditions.append(Invitation.status == filter.status)

        if filter.email:
            conditions.append(Invitation.email.ilike(f"%{filter.email}%"))

        if filter.created_after:
            conditions.append(Invitation.created_at >= filter.created_after)

        if filter.created_before:
            conditions.append(Invitation.created_at <= filter.created_before)

        if filter.invited_by:
            conditions.append(Invitation.invited_by == filter.invited_by)

        if conditions:
            query = query.where(and_(*conditions))

        return query

    async def accept(
        self,
        token: str,
        user_id: UUID,
    ) -> Invitation:
        """
        Accept an invitation.

        Args:
            token: Raw invitation token
            user_id: ID of the user accepting the invitation

        Returns:
            Updated invitation

        Raises:
            ValueError: If invitation is invalid, expired, or already used
        """
        invitation = await self.get_by_token(token)

        if not invitation:
            raise ValueError("Invalid invitation token")

        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Invitation is {invitation.status.value.lower()}")

        if invitation.expires_at < datetime.now(timezone.utc):
            # Mark as expired
            invitation.status = InvitationStatus.EXPIRED
            await self.db.commit()
            raise ValueError("Invitation has expired")

        # Accept the invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(invitation)

        # TODO: Create user associations via Mentor
        # This would be done in the router after the service call

        return invitation

    async def revoke(
        self,
        invitation_id: UUID,
        tenant_id: UUID,
        revoked_by: UUID,
    ) -> Invitation:
        """Revoke a pending invitation"""
        invitation = await self.get(invitation_id, tenant_id)

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Cannot revoke {invitation.status.value.lower()} invitation")

        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = datetime.now(timezone.utc)
        invitation.revoked_by = revoked_by

        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation

    async def resend(
        self,
        invitation_id: UUID,
        tenant_id: UUID,
    ) -> tuple[Invitation, str]:
        """
        Resend an invitation with a new token.

        Returns:
            Tuple of (invitation, new_raw_token)
        """
        invitation = await self.get(invitation_id, tenant_id)

        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(f"Cannot resend {invitation.status.value.lower()} invitation")

        # Generate new token
        raw_token = self.generate_token()
        invitation.token_hash = self.hash_token(raw_token)

        # Reset expiry
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(
            days=aurora_config.invitation_expiry_days
        )

        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation, raw_token

    async def send_invitation_email(
        self,
        invitation: Invitation,
        token: str,
        tenant_name: str,
        inviter_name: Optional[str] = None,
    ) -> bool:
        """Send invitation email"""
        from src.providers.email import EmailMessage

        config = aurora_config
        accept_url = f"{config.app_url}/accept-invitation?token={token}"

        inviter_text = f" by {inviter_name}" if inviter_name else ""
        message_text = f"\n\n{invitation.message}" if invitation.message else ""

        subject = f"You've been invited to join {tenant_name}"

        body = f"""Hello{' ' + invitation.name if invitation.name else ''},

You've been invited{inviter_text} to join {tenant_name}.{message_text}

Click the link below to accept your invitation:
{accept_url}

This invitation will expire in {config.invitation_expiry_days} days.

If you did not expect this invitation, please ignore this email.

--
{config.company_name}
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto;">
        <h2 style="color: #333; margin-bottom: 20px;">You're Invited!</h2>

        <p style="color: #666; font-size: 16px; line-height: 1.5;">
            Hello{' ' + invitation.name if invitation.name else ''},
        </p>

        <p style="color: #666; font-size: 16px; line-height: 1.5;">
            You've been invited{inviter_text} to join <strong>{tenant_name}</strong>.
        </p>

        {f'<p style="color: #666; font-size: 16px; line-height: 1.5; background: #f5f5f5; padding: 15px; border-radius: 8px; font-style: italic;">"{invitation.message}"</p>' if invitation.message else ''}

        <div style="text-align: center; margin: 30px 0;">
            <a href="{accept_url}" style="background: {config.brand_primary_color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                Accept Invitation
            </a>
        </div>

        <p style="color: #999; font-size: 14px;">
            This invitation will expire in <strong>{config.invitation_expiry_days} days</strong>.
        </p>

        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            If you did not expect this invitation, please ignore this email.
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

        <p style="color: #999; font-size: 12px;">
            {config.company_name}<br>
            <a href="mailto:{config.support_email}" style="color: {config.brand_primary_color};">{config.support_email}</a>
        </p>
    </div>
</body>
</html>
"""

        email_message = EmailMessage(
            to=[invitation.email],
            subject=subject,
            body=body,
            html=html,
        )

        try:
            result = await self.email_provider.send(email_message)
            if result.success:
                logger.info(f"Invitation email sent to {invitation.email}")
                return True
            else:
                logger.error(f"Failed to send invitation email: {result.error}")
                return False
        except Exception as e:
            logger.error(f"Invitation email error: {e}", exc_info=True)
            return False

    async def get_stats(self, tenant_id: UUID) -> InvitationStats:
        """Get invitation statistics for a tenant"""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        base_filter = and_(
            Invitation.tenant_id == tenant_id,
            Invitation.deleted_at.is_(None),
        )

        # Total
        total_result = await self.db.execute(
            select(func.count()).where(base_filter)
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(Invitation.status, func.count())
            .where(base_filter)
            .group_by(Invitation.status)
        )
        status_counts = {row[0].value: row[1] for row in status_result.all()}

        # Sent today
        today_result = await self.db.execute(
            select(func.count()).where(
                and_(base_filter, Invitation.created_at >= today_start)
            )
        )
        sent_today = today_result.scalar() or 0

        # Sent this week
        week_result = await self.db.execute(
            select(func.count()).where(
                and_(base_filter, Invitation.created_at >= week_start)
            )
        )
        sent_this_week = week_result.scalar() or 0

        return InvitationStats(
            total=total,
            pending=status_counts.get("PENDING", 0),
            accepted=status_counts.get("ACCEPTED", 0),
            expired=status_counts.get("EXPIRED", 0),
            revoked=status_counts.get("REVOKED", 0),
            sent_today=sent_today,
            sent_this_week=sent_this_week,
        )

    async def expire_old_invitations(self) -> int:
        """Mark expired invitations as EXPIRED. Returns count of updated."""
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.status == InvitationStatus.PENDING,
                    Invitation.expires_at < now,
                    Invitation.deleted_at.is_(None),
                )
            )
        )
        invitations = result.scalars().all()

        for invitation in invitations:
            invitation.status = InvitationStatus.EXPIRED

        if invitations:
            await self.db.commit()

        return len(invitations)


def get_invitation_service(db: AsyncSession) -> InvitationService:
    """Factory function for InvitationService (FastAPI dependency)"""
    return InvitationService(db)
