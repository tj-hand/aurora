"""
Aurora Users Router

Handles user CRUD operations, orchestrating Guardian and Mentor.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/users", tags=["aurora-users"])


# TODO: Implement endpoints
# - POST /users - Create user (Guardian + Mentor orchestration)
# - GET /users - List users for tenant
# - GET /users/{id} - Get user details
# - PUT /users/{id} - Update user
# - DELETE /users/{id} - Deactivate user


@router.get("/")
async def list_users():
    """List users for current tenant."""
    # TODO: Implement
    return {"users": [], "message": "Not implemented yet"}


@router.post("/")
async def create_user():
    """Create a new user (orchestrates Guardian + Mentor)."""
    # TODO: Implement
    # 1. Create guardian_users record in Guardian
    # 2. Create UserTenantAssociation in Mentor
    # 3. Store Aurora metadata (optional)
    return {"message": "Not implemented yet"}
