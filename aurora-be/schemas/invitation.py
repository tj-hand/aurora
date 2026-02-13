"""Invitation schemas - Pydantic models for invitation API endpoints"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.invitation import InvitationStatus


class InvitationBase(BaseModel):
    """Base schema for invitations"""

    email: EmailStr = Field(..., description="Invitee email address")
    name: Optional[str] = Field(None, max_length=255, description="Invitee display name")
    client_ids: Optional[list[UUID]] = Field(None, description="Clients to assign on acceptance")
    role_group_ids: Optional[list[UUID]] = Field(None, description="Role groups to assign")
    message: Optional[str] = Field(None, max_length=1000, description="Custom invitation message")


class InvitationCreate(InvitationBase):
    """Schema for creating an invitation"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "name": "John Doe",
                "client_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "role_group_ids": ["123e4567-e89b-12d3-a456-426614174001"],
                "message": "Welcome to our team!",
            }
        }
    )


class InvitationRead(InvitationBase):
    """Schema for reading an invitation"""

    id: UUID
    tenant_id: UUID
    status: InvitationStatus
    invited_by: UUID
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoked_by: Optional[UUID]

    model_config = ConfigDict(from_attributes=True)


class InvitationList(BaseModel):
    """Paginated list of invitations"""

    items: list[InvitationRead]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 10,
                "page": 1,
                "page_size": 50,
                "pages": 1,
            }
        }
    )


class InvitationFilter(BaseModel):
    """Filter parameters for invitation queries"""

    # Status filter
    status: Optional[InvitationStatus] = None

    # Email search
    email: Optional[str] = Field(None, max_length=255)

    # Date range
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    # Inviter filter
    invited_by: Optional[UUID] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "PENDING",
                "email": "john",
            }
        }
    )


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation"""

    token: str = Field(..., min_length=32, max_length=64, description="Invitation token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "abc123def456...",
            }
        }
    )


class InvitationAcceptResponse(BaseModel):
    """Response for successful invitation acceptance"""

    success: bool = True
    message: str = "Invitation accepted successfully"
    tenant_id: UUID
    tenant_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Invitation accepted successfully",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_name": "Acme Corp",
            }
        }
    )


class InvitationResendResponse(BaseModel):
    """Response for resending an invitation"""

    success: bool
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Invitation email resent",
            }
        }
    )


class InvitationRevokeResponse(BaseModel):
    """Response for revoking an invitation"""

    success: bool
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Invitation revoked",
            }
        }
    )


class InvitationStats(BaseModel):
    """Invitation statistics for a tenant"""

    total: int
    pending: int
    accepted: int
    expired: int
    revoked: int
    sent_today: int
    sent_this_week: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 100,
                "pending": 10,
                "accepted": 75,
                "expired": 10,
                "revoked": 5,
                "sent_today": 3,
                "sent_this_week": 15,
            }
        }
    )
