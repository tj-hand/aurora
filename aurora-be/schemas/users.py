"""User schemas for Aurora API

Request and response models for user CRUD operations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserLevel(str, Enum):
    """User hierarchy levels (mirrors Mentor's UserLevel)"""

    TENANT_ADMIN = "tenant_admin"
    SIMPLE_USER = "simple_user"


# Request schemas

class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr = Field(..., description="User email address")
    user_level: UserLevel = Field(
        default=UserLevel.SIMPLE_USER,
        description="User level within the tenant",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "user_level": "simple_user",
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating an existing user"""

    user_level: Optional[UserLevel] = Field(
        default=None,
        description="New user level within the tenant",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="User active status",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_level": "tenant_admin",
                "is_active": True,
            }
        }


# Response schemas

class UserResponse(BaseModel):
    """Schema for user response"""

    id: UUID = Field(..., description="User ID (from Guardian)")
    email: str = Field(..., description="User email address")
    user_level: str = Field(..., description="User level within the tenant")
    is_active: bool = Field(..., description="User active status")
    tenant_id: UUID = Field(..., description="Tenant ID")
    association_id: UUID = Field(..., description="UserTenantAssociation ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "user_level": "simple_user",
                "is_active": True,
                "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                "association_id": "770e8400-e29b-41d4-a716-446655440002",
                "created_at": "2024-01-20T10:30:00Z",
                "updated_at": "2024-01-20T10:30:00Z",
            }
        }


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""

    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=20, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")

    class Config:
        json_schema_extra = {
            "example": {
                "users": [],
                "total": 0,
                "page": 1,
                "per_page": 20,
                "has_more": False,
            }
        }
