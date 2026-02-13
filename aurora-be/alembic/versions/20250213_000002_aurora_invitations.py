"""Create aurora invitations table

Revision ID: 20250213_000002
Revises: 20250213_000001
Create Date: 2025-02-13

Creates the aurora_invitations table for user pre-registration and invitations.

Dependencies: Reel migration (20250213_000001) which depends on Mentor core
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250213_000002'
down_revision: Union[str, None] = '20250213_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # INVITATION STATUS ENUM
    # ============================================================================
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE invitation_status_enum AS ENUM ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    # ============================================================================
    # AURORA INVITATIONS: User pre-registration and invitation management
    # ============================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS aurora_invitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Invitee info
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255),

            -- Context
            tenant_id UUID NOT NULL,
            client_ids UUID[],
            role_group_ids UUID[],

            -- Invitation metadata
            status invitation_status_enum NOT NULL DEFAULT 'PENDING',
            invited_by UUID NOT NULL,

            -- Token for acceptance (SHA-256 hash)
            token_hash VARCHAR(64) NOT NULL UNIQUE,

            -- Timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            accepted_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            revoked_by UUID,

            -- Soft delete
            deleted_at TIMESTAMPTZ,

            -- Custom message
            message TEXT
        )
    """)

    # ============================================================================
    # INDEXES: Optimized for common query patterns
    # ============================================================================

    # Email lookup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_email
        ON aurora_invitations(email)
    """)

    # Tenant queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_tenant_id
        ON aurora_invitations(tenant_id)
    """)

    # Token lookup (unique already creates index, but explicit for clarity)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_token_hash
        ON aurora_invitations(token_hash)
    """)

    # Status queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_status
        ON aurora_invitations(status)
    """)

    # Tenant + status queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_tenant_status
        ON aurora_invitations(tenant_id, status)
    """)

    # Tenant + created_at (for listing)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_tenant_created
        ON aurora_invitations(tenant_id, created_at DESC)
    """)

    # Unique pending invitation per email per tenant
    # This is a partial unique index
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_aurora_unique_pending
        ON aurora_invitations(tenant_id, email)
        WHERE status = 'PENDING' AND deleted_at IS NULL
    """)

    # Expiry cleanup queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_aurora_expires_at
        ON aurora_invitations(expires_at)
        WHERE status = 'PENDING'
    """)

    # ============================================================================
    # COMMENTS: Documentation
    # ============================================================================
    op.execute("COMMENT ON TABLE aurora_invitations IS 'User pre-registration and invitation management'")
    op.execute("COMMENT ON COLUMN aurora_invitations.email IS 'Invitee email address'")
    op.execute("COMMENT ON COLUMN aurora_invitations.name IS 'Invitee display name (optional)'")
    op.execute("COMMENT ON COLUMN aurora_invitations.tenant_id IS 'Tenant the user is being invited to'")
    op.execute("COMMENT ON COLUMN aurora_invitations.client_ids IS 'Clients to assign on acceptance'")
    op.execute("COMMENT ON COLUMN aurora_invitations.role_group_ids IS 'Role groups to assign on acceptance'")
    op.execute("COMMENT ON COLUMN aurora_invitations.status IS 'Current invitation status'")
    op.execute("COMMENT ON COLUMN aurora_invitations.invited_by IS 'User who created the invitation'")
    op.execute("COMMENT ON COLUMN aurora_invitations.token_hash IS 'SHA-256 hash of acceptance token'")
    op.execute("COMMENT ON COLUMN aurora_invitations.expires_at IS 'When the invitation expires'")
    op.execute("COMMENT ON COLUMN aurora_invitations.accepted_at IS 'When the invitation was accepted'")
    op.execute("COMMENT ON COLUMN aurora_invitations.revoked_at IS 'When the invitation was revoked'")
    op.execute("COMMENT ON COLUMN aurora_invitations.revoked_by IS 'User who revoked the invitation'")
    op.execute("COMMENT ON COLUMN aurora_invitations.message IS 'Custom message from inviter'")


def downgrade() -> None:
    # Drop table
    op.execute("DROP TABLE IF EXISTS aurora_invitations CASCADE")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS invitation_status_enum")
