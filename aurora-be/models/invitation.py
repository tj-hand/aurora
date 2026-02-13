"""Invitation model - Pre-registration and invitation management"""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# Use Matrix infrastructure (Layer 0)
from src.database import Base


class InvitationStatus(str, enum.Enum):
    """Invitation status states"""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class Invitation(Base):
    """Invitation model - manages user pre-registration invitations"""

    __tablename__ = "aurora_invitations"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Invitee info
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Invitee email address",
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Invitee display name (optional)",
    )

    # Context
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Tenant (account) the user is being invited to",
    )
    client_ids: Mapped[Optional[list[UUID]]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        nullable=True,
        comment="Clients to assign on acceptance",
    )

    # Pre-assigned permissions (optional)
    role_group_ids: Mapped[Optional[list[UUID]]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        nullable=True,
        comment="Role groups to assign on acceptance",
    )

    # Invitation metadata
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus),
        nullable=False,
        default=InvitationStatus.PENDING,
        index=True,
        comment="Current invitation status",
    )
    invited_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="User who created the invitation",
    )

    # Token for acceptance (hashed like Guardian tokens)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of acceptance token",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the invitation expires",
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the invitation was accepted",
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the invitation was revoked",
    )
    revoked_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User who revoked the invitation",
    )

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp",
    )

    # Message (optional custom message from inviter)
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Custom message from inviter",
    )

    # Table indexes and constraints
    __table_args__ = (
        # Unique pending invitation per email per tenant
        UniqueConstraint(
            "tenant_id",
            "email",
            name="uq_aurora_pending_invitation",
            postgresql_where="status = 'PENDING' AND deleted_at IS NULL",
        ),
        # Tenant status queries
        Index(
            "idx_aurora_tenant_status",
            "tenant_id",
            "status",
        ),
        # Tenant created queries
        Index(
            "idx_aurora_tenant_created",
            "tenant_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, email={self.email}, status={self.status})>"
