"""Aurora dependencies - FastAPI dependency injection"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .services.invitation_service import InvitationService, get_invitation_service


async def get_aurora(db: AsyncSession = Depends(get_db)) -> InvitationService:
    """Get InvitationService instance for dependency injection"""
    return get_invitation_service(db)


# Type alias for FastAPI dependencies
InvitationServiceDep = Annotated[InvitationService, Depends(get_aurora)]
