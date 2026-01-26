"""Invitation schemas for Aurora API

Request and response models for invitation CRUD operations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InvitationStatus(str, Enum):
    """Invitation status values"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class UserLevel(str, Enum):
    """User hierarchy levels (mirrors Mentor's UserLevel)"""
    TENANT_ADMIN = "tenant_admin"
    SIMPLE_USER = "simple_user"


# Request schemas

class InvitationCreate(BaseModel):
    """Schema for creating a new invitation"""

    email: EmailStr = Field(..., description="Email address to invite")
    name: Optional[str] = Field(None, max_length=255, description="Name of the invitee")
    user_level: UserLevel = Field(
        default=UserLevel.SIMPLE_USER,
        description="User level to assign upon acceptance"
    )
    role_id: Optional[UUID] = Field(None, description="Optional role ID to assign")
    client_id: Optional[UUID] = Field(None, description="Optional client/scope context")
    message: Optional[str] = Field(None, description="Custom message for the invitation email")
    validity_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days the invitation is valid"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "name": "John Doe",
                "user_level": "simple_user",
                "message": "Welcome to our team!",
                "validity_days": 7
            }
        }


class InvitationResend(BaseModel):
    """Schema for resending an invitation"""

    custom_message: Optional[str] = Field(
        None,
        description="Override the original message for this resend"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "custom_message": "Reminder: Your invitation is still pending!"
            }
        }


class InvitationRevoke(BaseModel):
    """Schema for revoking an invitation"""

    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for revocation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Position no longer available"
            }
        }


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation (used with token)"""

    # The token is typically passed as a path/query parameter
    # This schema is for any additional data needed during acceptance
    pass


class InvitationBulkCreate(BaseModel):
    """Schema for bulk invitation creation"""

    invitations: List[InvitationCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of invitations to create"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "invitations": [
                    {"email": "user1@example.com", "user_level": "simple_user"},
                    {"email": "user2@example.com", "user_level": "tenant_admin"}
                ]
            }
        }


# Response schemas

class InvitationResponse(BaseModel):
    """Schema for invitation response"""

    id: UUID = Field(..., description="Invitation ID")
    email: str = Field(..., description="Invitee email address")
    name: Optional[str] = Field(None, description="Invitee name")
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_slug: Optional[str] = Field(None, description="Tenant slug")
    client_id: Optional[UUID] = Field(None, description="Client ID if scoped")
    client_slug: Optional[str] = Field(None, description="Client slug")
    user_level: str = Field(..., description="User level to assign on acceptance")
    role_id: Optional[UUID] = Field(None, description="Role ID to assign")
    status: InvitationStatus = Field(..., description="Current invitation status")
    message: Optional[str] = Field(None, description="Custom invitation message")
    invited_by: UUID = Field(..., description="ID of user who created the invitation")
    invited_by_email: Optional[str] = Field(None, description="Email of inviter")
    accepted_by: Optional[UUID] = Field(None, description="ID of user who accepted")
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    revoked_by: Optional[UUID] = Field(None, description="ID of user who revoked")
    revoked_at: Optional[datetime] = Field(None, description="Revocation timestamp")
    revocation_reason: Optional[str] = Field(None, description="Reason for revocation")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    email_sent_at: Optional[datetime] = Field(None, description="Last email sent timestamp")
    email_sent_count: int = Field(..., description="Number of emails sent")
    is_expired: bool = Field(..., description="Whether the invitation has expired")
    is_valid: bool = Field(..., description="Whether the invitation can still be accepted")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "newuser@example.com",
                "name": "John Doe",
                "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                "tenant_slug": "acme-corp",
                "user_level": "simple_user",
                "status": "pending",
                "invited_by": "770e8400-e29b-41d4-a716-446655440002",
                "invited_by_email": "admin@example.com",
                "created_at": "2026-01-25T10:30:00Z",
                "expires_at": "2026-02-01T10:30:00Z",
                "updated_at": "2026-01-25T10:30:00Z",
                "email_sent_count": 1,
                "is_expired": False,
                "is_valid": True
            }
        }


class InvitationListResponse(BaseModel):
    """Schema for paginated invitation list response"""

    invitations: List[InvitationResponse] = Field(..., description="List of invitations")
    total: int = Field(..., description="Total number of invitations")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=20, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")

    class Config:
        json_schema_extra = {
            "example": {
                "invitations": [],
                "total": 0,
                "page": 1,
                "per_page": 20,
                "has_more": False
            }
        }


class InvitationBulkResult(BaseModel):
    """Result of bulk invitation operation"""

    created: List[InvitationResponse] = Field(
        default_factory=list,
        description="Successfully created invitations"
    )
    failed: List[dict] = Field(
        default_factory=list,
        description="Failed invitations with error details"
    )
    total_created: int = Field(..., description="Number of successfully created invitations")
    total_failed: int = Field(..., description="Number of failed invitations")


class InvitationTokenInfo(BaseModel):
    """Public information about an invitation from its token"""

    email: str = Field(..., description="Invited email address")
    tenant_slug: Optional[str] = Field(None, description="Tenant name")
    invited_by_email: Optional[str] = Field(None, description="Inviter's email")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_valid: bool = Field(..., description="Whether the invitation is still valid")
    message: Optional[str] = Field(None, description="Custom invitation message")
