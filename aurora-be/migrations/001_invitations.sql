-- Aurora Invitations Migration
-- Creates the invitations table for user invitation management
-- Version: 001
-- Date: 2026-01-25

-- Create invitation status enum type
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invitation_status') THEN
        CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'revoked');
    END IF;
END$$;

-- Create invitations table
CREATE TABLE IF NOT EXISTS invitations (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Secure token for invitation link
    token VARCHAR(64) NOT NULL UNIQUE,

    -- Invitee information
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),

    -- Tenant context
    tenant_id UUID NOT NULL,
    tenant_slug VARCHAR(100),

    -- Optional client/scope context
    client_id UUID,
    client_slug VARCHAR(100),

    -- Role/level assignment on acceptance
    user_level VARCHAR(50) NOT NULL DEFAULT 'simple_user',
    role_id UUID,

    -- Invitation status
    status invitation_status NOT NULL DEFAULT 'pending',

    -- Custom message for invitation email
    message TEXT,

    -- Tracking
    invited_by UUID NOT NULL,
    invited_by_email VARCHAR(255),

    -- Result tracking
    accepted_by UUID,
    accepted_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Email tracking
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_sent_count INTEGER NOT NULL DEFAULT 0,
    last_email_error TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_tenant_id ON invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invitations_client_id ON invitations(client_id);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON invitations(status);
CREATE INDEX IF NOT EXISTS idx_invitations_tenant_status ON invitations(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_invitations_email_tenant ON invitations(email, tenant_id);
CREATE INDEX IF NOT EXISTS idx_invitations_created ON invitations(created_at);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_invitations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_invitations_updated_at ON invitations;
CREATE TRIGGER trigger_invitations_updated_at
    BEFORE UPDATE ON invitations
    FOR EACH ROW
    EXECUTE FUNCTION update_invitations_updated_at();

-- Add comments
COMMENT ON TABLE invitations IS 'User invitations for tenant onboarding';
COMMENT ON COLUMN invitations.token IS 'Secure token for invitation link verification';
COMMENT ON COLUMN invitations.email IS 'Email address of the invitee';
COMMENT ON COLUMN invitations.tenant_id IS 'Tenant the user is being invited to';
COMMENT ON COLUMN invitations.user_level IS 'User level to assign upon acceptance';
COMMENT ON COLUMN invitations.status IS 'Current invitation status (pending, accepted, revoked)';
COMMENT ON COLUMN invitations.expires_at IS 'Expiration timestamp for the invitation';
