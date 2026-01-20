"""
Aurora Router - Main API Router

Aggregates all Aurora routers and exposes them to Matrix.
"""

from fastapi import APIRouter

# Import sub-routers
from .routers import users

router = APIRouter(prefix="/aurora", tags=["aurora"])

# Include sub-routers
router.include_router(users.router)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "module": "aurora"}
