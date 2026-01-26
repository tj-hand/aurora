"""Aurora Invitation Service

Manages user invitations for tenant onboarding.

Invitation Flow:
    1. Admin creates invitation with email and optional role/permissions
    2. System sends email with secure token via Matrix email provider
    3. User clicks link, verifies identity (via Guardian)
    4. On success, user is associated with tenant (via Mentor)
    5. Invitation marked as accepted
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.invitation import Invitation, InvitationStatus, DEFAULT_INVITATION_VALIDITY_DAYS
from ..schemas.invitations import (
    InvitationCreate,
    InvitationBulkCreate,
    InvitationBulkResult,
)

logger = logging.getLogger(__name__)


def generate_secure_token(length: int = 64) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)[:length]


class InvitationService:
    """
    Service for invitation management.

    Responsibilities:
    - Create invitations (single and bulk)
    - List invitations for a tenant
    - Get invitation details (by ID or token)
    - Accept invitations (orchestrates Guardian + Mentor)
    - Revoke invitations
    - Resend invitation emails
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize InvitationService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create(
        self,
        tenant_id: UUID,
        invited_by: UUID,
        data: InvitationCreate,
        tenant_slug: Optional[str] = None,
        invited_by_email: Optional[str] = None,
        client_slug: Optional[str] = None,
    ) -> Invitation:
        """
        Create a new invitation.

        Args:
            tenant_id: Tenant to invite user to
            invited_by: ID of user creating the invitation
            data: Invitation creation data
            tenant_slug: Optional tenant slug for display
            invited_by_email: Optional inviter email for display
            client_slug: Optional client slug for display

        Returns:
            Created Invitation

        Raises:
            ValueError: If pending invitation already exists for this email/tenant
        """
        # Check for existing pending invitation
        existing = await self._get_pending_for_email(data.email, tenant_id)
        if existing:
            raise ValueError(
                f"A pending invitation already exists for {data.email} in this tenant"
            )

        # Calculate expiration
        validity_days = data.validity_days or DEFAULT_INVITATION_VALIDITY_DAYS
        expires_at = datetime.utcnow() + timedelta(days=validity_days)

        # Create invitation
        invitation = Invitation(
            token=generate_secure_token(),
            email=data.email,
            name=data.name,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            client_id=data.client_id,
            client_slug=client_slug,
            user_level=data.user_level.value,
            role_id=data.role_id,
            status=InvitationStatus.PENDING,
            message=data.message,
            invited_by=invited_by,
            invited_by_email=invited_by_email,
            expires_at=expires_at,
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        logger.info(
            f"Created invitation: id={invitation.id}, email={data.email}, "
            f"tenant={tenant_id}"
        )

        return invitation

    async def create_bulk(
        self,
        tenant_id: UUID,
        invited_by: UUID,
        data: InvitationBulkCreate,
        tenant_slug: Optional[str] = None,
        invited_by_email: Optional[str] = None,
    ) -> InvitationBulkResult:
        """
        Create multiple invitations at once.

        Args:
            tenant_id: Tenant to invite users to
            invited_by: ID of user creating the invitations
            data: Bulk invitation creation data
            tenant_slug: Optional tenant slug for display
            invited_by_email: Optional inviter email for display

        Returns:
            BulkResult with created and failed invitations
        """
        from ..schemas.invitations import InvitationResponse

        created = []
        failed = []

        for invite_data in data.invitations:
            try:
                invitation = await self.create(
                    tenant_id=tenant_id,
                    invited_by=invited_by,
                    data=invite_data,
                    tenant_slug=tenant_slug,
                    invited_by_email=invited_by_email,
                )
                created.append(invitation)
            except Exception as e:
                failed.append({
                    "email": invite_data.email,
                    "error": str(e)
                })

        return InvitationBulkResult(
            created=[InvitationResponse(**inv.to_dict()) for inv in created],
            failed=failed,
            total_created=len(created),
            total_failed=len(failed),
        )

    async def list(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
        status: Optional[InvitationStatus] = None,
        search: Optional[str] = None,
        client_id: Optional[UUID] = None,
    ) -> Tuple[List[Invitation], int]:
        """
        List invitations for a tenant with pagination.

        Args:
            tenant_id: Tenant ID to filter by
            page: Page number (1-indexed)
            per_page: Items per page
            status: Optional status filter
            search: Optional search term (email, name)
            client_id: Optional client filter

        Returns:
            Tuple of (invitations list, total count)
        """
        # Base query
        query = select(Invitation).where(Invitation.tenant_id == tenant_id)

        # Apply filters
        if status:
            query = query.where(Invitation.status == status)
        if client_id:
            query = query.where(Invitation.client_id == client_id)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Invitation.email.ilike(search_term),
                    Invitation.name.ilike(search_term)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Apply pagination and ordering
        offset = (page - 1) * per_page
        query = query.order_by(Invitation.created_at.desc())
        query = query.offset(offset).limit(per_page)

        # Execute query
        result = await self.db.execute(query)
        invitations = list(result.scalars().all())

        return invitations, total

    async def get_by_id(self, invitation_id: UUID) -> Optional[Invitation]:
        """
        Get invitation by ID.

        Args:
            invitation_id: Invitation ID

        Returns:
            Invitation if found, None otherwise
        """
        result = await self.db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Optional[Invitation]:
        """
        Get invitation by token.

        Args:
            token: Invitation token

        Returns:
            Invitation if found, None otherwise
        """
        result = await self.db.execute(
            select(Invitation).where(Invitation.token == token)
        )
        return result.scalar_one_or_none()

    async def accept(
        self,
        invitation: Invitation,
        user_id: UUID,
    ) -> Invitation:
        """
        Accept an invitation and create user-tenant association.

        Orchestrates:
        1. Validate invitation is still valid
        2. Create user-tenant association via Mentor
        3. Mark invitation as accepted

        Args:
            invitation: Invitation to accept
            user_id: ID of user accepting (from Guardian)

        Returns:
            Updated Invitation

        Raises:
            ValueError: If invitation is not valid
        """
        if not invitation.is_valid:
            if invitation.is_expired:
                raise ValueError("This invitation has expired")
            raise ValueError(f"This invitation has already been {invitation.status.value}")

        # Import Mentor's UserTenantAssociation to create the link
        # This follows the pattern from user_service.py
        try:
            from src.modules.mentor.models.user_tenant_association import (
                UserTenantAssociation,
                UserLevel,
            )

            # Check if association already exists
            existing = await self._check_existing_association(
                user_id, invitation.tenant_id
            )
            if existing:
                # User is already associated, just mark invitation as accepted
                logger.warning(
                    f"User {user_id} already associated with tenant {invitation.tenant_id}"
                )
            else:
                # Create the association
                level_enum = UserLevel(invitation.user_level)
                association = UserTenantAssociation(
                    user_id=user_id,
                    tenant_id=invitation.tenant_id,
                    user_level=level_enum,
                    created_by=invitation.invited_by,
                    is_active=True,
                )
                self.db.add(association)

        except ImportError:
            logger.warning("Mentor module not available, skipping association creation")

        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_by = user_id
        invitation.accepted_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(invitation)

        logger.info(
            f"Invitation accepted: id={invitation.id}, user={user_id}, "
            f"tenant={invitation.tenant_id}"
        )

        return invitation

    async def revoke(
        self,
        invitation: Invitation,
        revoked_by: UUID,
        reason: Optional[str] = None,
    ) -> Invitation:
        """
        Revoke an invitation.

        Args:
            invitation: Invitation to revoke
            revoked_by: ID of user revoking
            reason: Optional reason for revocation

        Returns:
            Updated Invitation

        Raises:
            ValueError: If invitation cannot be revoked
        """
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError(
                f"Cannot revoke invitation with status: {invitation.status.value}"
            )

        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_by = revoked_by
        invitation.revoked_at = datetime.utcnow()
        invitation.revocation_reason = reason

        await self.db.commit()
        await self.db.refresh(invitation)

        logger.info(f"Invitation revoked: id={invitation.id}, by={revoked_by}")

        return invitation

    async def resend_email(
        self,
        invitation: Invitation,
        custom_message: Optional[str] = None,
    ) -> Invitation:
        """
        Resend invitation email.

        Args:
            invitation: Invitation to resend
            custom_message: Optional message override

        Returns:
            Updated Invitation

        Raises:
            ValueError: If invitation is not pending
        """
        if invitation.status != InvitationStatus.PENDING:
            raise ValueError("Can only resend emails for pending invitations")

        if invitation.is_expired:
            raise ValueError("Cannot resend email for expired invitation")

        # Send email via Matrix email provider
        await self._send_invitation_email(
            invitation,
            custom_message or invitation.message
        )

        # Update tracking
        invitation.email_sent_at = datetime.utcnow()
        invitation.email_sent_count += 1
        invitation.last_email_error = None

        await self.db.commit()
        await self.db.refresh(invitation)

        logger.info(
            f"Invitation email resent: id={invitation.id}, "
            f"count={invitation.email_sent_count}"
        )

        return invitation

    async def send_email(self, invitation: Invitation) -> bool:
        """
        Send initial invitation email.

        Args:
            invitation: Invitation to send email for

        Returns:
            True if email sent successfully
        """
        try:
            await self._send_invitation_email(invitation, invitation.message)

            invitation.email_sent_at = datetime.utcnow()
            invitation.email_sent_count += 1
            invitation.last_email_error = None

            await self.db.commit()
            return True

        except Exception as e:
            invitation.last_email_error = str(e)
            await self.db.commit()
            logger.error(f"Failed to send invitation email: {e}")
            return False

    async def _send_invitation_email(
        self,
        invitation: Invitation,
        message: Optional[str] = None,
    ) -> None:
        """
        Internal method to send invitation email via Matrix.

        Args:
            invitation: Invitation to send email for
            message: Optional custom message
        """
        try:
            from src.providers import get_email_provider

            email_provider = get_email_provider()

            # Build invitation URL
            # The actual URL would be configured in settings
            invitation_url = f"/accept-invitation?token={invitation.token}"

            # Render email template
            email_content = self._render_invitation_email(
                invitation=invitation,
                invitation_url=invitation_url,
                message=message,
            )

            # Send via Matrix email provider
            await email_provider.send(
                to=invitation.email,
                subject=f"You've been invited to join {invitation.tenant_slug or 'our team'}",
                html=email_content,
            )

            logger.info(f"Invitation email sent to {invitation.email}")

        except ImportError:
            logger.warning("Email provider not available, skipping email send")
            raise

    def _render_invitation_email(
        self,
        invitation: Invitation,
        invitation_url: str,
        message: Optional[str] = None,
    ) -> str:
        """
        Render invitation email HTML content.

        Args:
            invitation: Invitation data
            invitation_url: URL for accepting the invitation
            message: Optional custom message

        Returns:
            Rendered HTML content
        """
        # This would typically use a template engine (Jinja2)
        # For now, return a simple HTML template
        custom_message_html = ""
        if message:
            custom_message_html = f"<p>{message}</p>"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #2563eb; margin-bottom: 10px;">You're Invited!</h1>
    </div>

    <div style="background: #f8fafc; border-radius: 8px; padding: 24px; margin: 20px 0;">
        <p>Hi{' ' + invitation.name if invitation.name else ''},</p>

        <p>
            <strong>{invitation.invited_by_email or 'Someone'}</strong> has invited you to join
            <strong>{invitation.tenant_slug or 'their team'}</strong>.
        </p>

        {custom_message_html}

        <div style="text-align: center; margin: 30px 0;">
            <a href="{invitation_url}"
               style="display: inline-block; background: #2563eb; color: white; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 500;">
                Accept Invitation
            </a>
        </div>

        <p style="color: #64748b; font-size: 14px;">
            This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y') if invitation.expires_at else 'N/A'}.
        </p>
    </div>

    <div style="text-align: center; color: #94a3b8; font-size: 12px; padding: 20px 0;">
        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
    </div>
</body>
</html>
"""

    async def _get_pending_for_email(
        self,
        email: str,
        tenant_id: UUID,
    ) -> Optional[Invitation]:
        """Get pending invitation for email in tenant"""
        result = await self.db.execute(
            select(Invitation).where(
                and_(
                    Invitation.email == email,
                    Invitation.tenant_id == tenant_id,
                    Invitation.status == InvitationStatus.PENDING,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _check_existing_association(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """Check if user is already associated with tenant"""
        try:
            from src.modules.mentor.models.user_tenant_association import (
                UserTenantAssociation,
            )

            result = await self.db.execute(
                select(UserTenantAssociation).where(
                    and_(
                        UserTenantAssociation.user_id == user_id,
                        UserTenantAssociation.tenant_id == tenant_id,
                        UserTenantAssociation.deleted_at.is_(None),
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except ImportError:
            return False

    async def cleanup_expired(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> int:
        """
        Clean up expired invitations by marking them as expired status.

        Note: We don't delete expired invitations to maintain audit trail.
        The computed_status property handles expiration display.

        Args:
            tenant_id: Optional tenant to limit cleanup to

        Returns:
            Number of invitations marked as expired
        """
        # This is a no-op since we compute expiration status dynamically
        # But could be used for batch updates if needed
        logger.info("Expired invitation cleanup is handled via computed_status property")
        return 0
