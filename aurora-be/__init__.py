"""Aurora module - User pre-registration and invitation management

Provides invitation creation, email sending, token-based acceptance,
and user onboarding workflows.

Exports:
    - router: FastAPI router for /api/v1/aurora/*
    - InvitationService: Core invitation service
    - get_invitation_service: FastAPI dependency
    - Invitation: SQLAlchemy model
    - InvitationStatus: Invitation status enum
"""

from .router import router
from .models.invitation import Invitation, InvitationStatus
from .services.invitation_service import InvitationService, get_invitation_service

__all__ = [
    "router",
    "Invitation",
    "InvitationStatus",
    "InvitationService",
    "get_invitation_service",
]
