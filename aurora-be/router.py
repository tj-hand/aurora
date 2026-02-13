"""Aurora module main router

Aggregates all sub-routers under /v1/aurora prefix.
"""

from fastapi import APIRouter

from .routers.invitations import router as invitations_router

router = APIRouter(prefix="/v1/aurora", tags=["aurora"])

# Mount sub-routers
router.include_router(invitations_router, prefix="/invitations", tags=["invitations"])
