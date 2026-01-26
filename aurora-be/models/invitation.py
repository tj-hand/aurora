"""Invitation model - User invitation management"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# Use Matrix infrastructure (Layer 0)
from src.database import Base


class InvitationStatus(str, Enum):
    """Invitation status values"""
    PENDING = "pending"      # Invitation sent, awaiting acceptance
    ACCEPTED = "accepted"    # User accepted the invitation
    REVOKED = "revoked"      # Admin revoked the invitation
    EXPIRED = "expired"      # Invitation expired (not used in DB, computed)


# Default invitation validity period (7 days)
DEFAULT_INVITATION_VALIDITY_DAYS = 7


class Invitation(Base):
    """
    Invitation model - represents an invitation for a user to join a tenant.

    Invitation Flow:
    1. Admin creates invitation with email and optional role/permissions
    2. System sends email with secure token
    3. User clicks link, verifies identity (via Guardian)
    4. On success, user is associated with tenant (via Mentor)
    5. Invitation marked as accepted

    Status Transitions:
    - pending -> accepted (user accepts)
    - pending -> revoked (admin revokes)
    - pending -> expired (computed based on expires_at)
    """

    __tablename__ = "invitations"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Secure token for invitation link
    token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )

    # Invitee information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Tenant context
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    tenant_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Optional client/scope context
    client_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    client_slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Role/level assignment on acceptance
    user_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="simple_user"
    )

    # Optional role ID to assign
    role_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Invitation status
    status: Mapped[InvitationStatus] = mapped_column(
        SAEnum(InvitationStatus, name="invitation_status", create_type=True),
        default=InvitationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Custom message for invitation email
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tracking
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    invited_by_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Result tracking
    accepted_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Email tracking
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    email_sent_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_email_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Table constraints and indexes
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("idx_invitations_tenant_status", "tenant_id", "status"),
        Index("idx_invitations_email_tenant", "email", "tenant_id"),
        Index("idx_invitations_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Invitation(id={self.id}, email={self.email}, "
            f"tenant_id={self.tenant_id}, status={self.status.value})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        if self.status != InvitationStatus.PENDING:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None) if self.expires_at else False

    @property
    def is_valid(self) -> bool:
        """Check if invitation can still be accepted"""
        return self.status == InvitationStatus.PENDING and not self.is_expired

    @property
    def computed_status(self) -> InvitationStatus:
        """Get status considering expiration"""
        if self.status == InvitationStatus.PENDING and self.is_expired:
            return InvitationStatus.EXPIRED
        return self.status

    def to_dict(self) -> dict:
        """Convert invitation to dictionary for API responses"""
        return {
            "id": str(self.id),
            "token": self.token,
            "email": self.email,
            "name": self.name,
            "tenant_id": str(self.tenant_id),
            "tenant_slug": self.tenant_slug,
            "client_id": str(self.client_id) if self.client_id else None,
            "client_slug": self.client_slug,
            "user_level": self.user_level,
            "role_id": str(self.role_id) if self.role_id else None,
            "status": self.computed_status.value,
            "message": self.message,
            "invited_by": str(self.invited_by),
            "invited_by_email": self.invited_by_email,
            "accepted_by": str(self.accepted_by) if self.accepted_by else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "revoked_by": str(self.revoked_by) if self.revoked_by else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "email_sent_count": self.email_sent_count,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
        }
