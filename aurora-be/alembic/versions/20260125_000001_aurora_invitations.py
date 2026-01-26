"""Aurora invitations table

Revision ID: aurora_invitations_001
Revises:
Create Date: 2026-01-25 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aurora_invitations_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create invitation_status enum type
    invitation_status = postgresql.ENUM(
        'pending', 'accepted', 'revoked',
        name='invitation_status',
        create_type=False
    )
    invitation_status.create(op.get_bind(), checkfirst=True)

    # Create invitations table
    op.create_table(
        'invitations',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Secure token for invitation link
        sa.Column('token', sa.String(64), nullable=False, unique=True, index=True),

        # Invitee information
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),

        # Tenant context
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('tenant_slug', sa.String(100), nullable=True),

        # Optional client/scope context
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('client_slug', sa.String(100), nullable=True),

        # Role/level assignment on acceptance
        sa.Column('user_level', sa.String(50), nullable=False, server_default='simple_user'),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Invitation status
        sa.Column('status', sa.Enum('pending', 'accepted', 'revoked',
                                     name='invitation_status', create_type=False),
                  nullable=False, server_default='pending', index=True),

        # Custom message for invitation email
        sa.Column('message', sa.Text, nullable=True),

        # Tracking
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_by_email', sa.String(255), nullable=True),

        # Result tracking
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(500), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),

        # Email tracking
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_sent_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_email_error', sa.Text, nullable=True),
    )

    # Create composite indexes
    op.create_index('idx_invitations_tenant_status', 'invitations',
                    ['tenant_id', 'status'])
    op.create_index('idx_invitations_email_tenant', 'invitations',
                    ['email', 'tenant_id'])
    op.create_index('idx_invitations_created', 'invitations',
                    ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_invitations_created', table_name='invitations')
    op.drop_index('idx_invitations_email_tenant', table_name='invitations')
    op.drop_index('idx_invitations_tenant_status', table_name='invitations')

    # Drop table
    op.drop_table('invitations')

    # Drop enum type
    invitation_status = postgresql.ENUM(
        'pending', 'accepted', 'revoked',
        name='invitation_status'
    )
    invitation_status.drop(op.get_bind(), checkfirst=True)
