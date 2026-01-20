"""Test configuration and fixtures for Aurora tests

Provides:
- Mock database session
- Mock Guardian service
- Mock Mentor dependencies
- Test client with dependency overrides
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel


# ============================================================================
# Mock Models
# ============================================================================


class MockUser:
    """Mock Guardian User model"""

    def __init__(
        self,
        id: UUID = None,
        email: str = "test@example.com",
        is_active: bool = True,
    ):
        self.id = id or uuid.uuid4()
        self.email = email
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockUserLevel:
    """Mock Mentor UserLevel enum"""

    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    SIMPLE_USER = "simple_user"

    def __init__(self, value: str):
        self.value = value


class MockUserTenantAssociation:
    """Mock Mentor UserTenantAssociation model"""

    def __init__(
        self,
        id: UUID = None,
        user_id: UUID = None,
        tenant_id: UUID = None,
        user_level: str = "simple_user",
        is_active: bool = True,
        created_by: UUID = None,
        deleted_at: datetime = None,
    ):
        self.id = id or uuid.uuid4()
        self.user_id = user_id or uuid.uuid4()
        self.tenant_id = tenant_id or uuid.uuid4()
        self.user_level = MockUserLevel(user_level)
        self.is_active = is_active
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.deleted_at = deleted_at


# ============================================================================
# Mock Services
# ============================================================================


class MockGuardianService:
    """Mock Guardian authentication service"""

    def __init__(self):
        self.users = {}  # email -> MockUser

    async def get_or_create_user(self, db, email: str) -> MockUser:
        """Get or create a user by email"""
        email = email.lower()
        if email not in self.users:
            self.users[email] = MockUser(email=email)
        return self.users[email]

    def verify_jwt(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        if token == "valid_token":
            return {
                "sub": str(uuid.uuid4()),
                "email": "admin@example.com",
            }
        if token.startswith("user_"):
            return {
                "sub": token.replace("user_", ""),
                "email": "user@example.com",
            }
        return None


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_guardian_service():
    """Provide mock Guardian service"""
    return MockGuardianService()


@pytest.fixture
def tenant_id():
    """Provide a consistent tenant ID for tests"""
    return uuid.uuid4()


@pytest.fixture
def admin_user_id():
    """Provide a consistent admin user ID for tests"""
    return uuid.uuid4()


@pytest.fixture
def simple_user_id():
    """Provide a consistent simple user ID for tests"""
    return uuid.uuid4()


class MockDBSession:
    """Mock async database session"""

    def __init__(self):
        self.associations = []  # List of MockUserTenantAssociation
        self.committed = False
        self.added = []

    def add(self, obj):
        self.added.append(obj)
        if hasattr(obj, "id") and obj.id is None:
            obj.id = uuid.uuid4()

    async def commit(self):
        self.committed = True
        # Move added items to associations if they're associations
        for obj in self.added:
            if isinstance(obj, MockUserTenantAssociation):
                self.associations.append(obj)
        self.added = []

    async def refresh(self, obj):
        pass

    async def execute(self, query):
        """Mock execute - returns mock result"""
        return MockResult(self.associations)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockResult:
    """Mock SQLAlchemy result"""

    def __init__(self, data):
        self.data = data

    def scalar_one_or_none(self):
        return self.data[0] if self.data else None

    def scalar(self):
        return len(self.data)

    def all(self):
        return self.data

    def first(self):
        return self.data[0] if self.data else None


@pytest.fixture
def mock_db():
    """Provide mock database session"""
    return MockDBSession()


# ============================================================================
# Test App and Client
# ============================================================================


@pytest.fixture
def mock_current_user(admin_user_id):
    """Mock current user (admin)"""

    class UserInfo(BaseModel):
        id: UUID
        email: str
        is_verified: bool = True
        metadata: dict = {}

    return UserInfo(
        id=admin_user_id,
        email="admin@example.com",
    )


@pytest.fixture
def mock_tenant_context(tenant_id, admin_user_id):
    """Mock tenant context (admin)"""

    class TenantContextInfo(BaseModel):
        tenant_id: UUID
        tenant_slug: str
        tenant_name: str
        user_is_admin: bool = True
        user_is_superadmin: bool = False

    return TenantContextInfo(
        tenant_id=tenant_id,
        tenant_slug="test-tenant",
        tenant_name="Test Tenant",
        user_is_admin=True,
        user_is_superadmin=False,
    )


@pytest.fixture
def mock_tenant_context_non_admin(tenant_id):
    """Mock tenant context (non-admin)"""

    class TenantContextInfo(BaseModel):
        tenant_id: UUID
        tenant_slug: str
        tenant_name: str
        user_is_admin: bool = False
        user_is_superadmin: bool = False

    return TenantContextInfo(
        tenant_id=tenant_id,
        tenant_slug="test-tenant",
        tenant_name="Test Tenant",
        user_is_admin=False,
        user_is_superadmin=False,
    )


def create_test_app(
    mock_current_user,
    mock_tenant_context,
    mock_db,
):
    """Create FastAPI test app with dependency overrides"""
    from fastapi import FastAPI

    app = FastAPI()

    # Import router
    from aurora_be.routers.users import router

    app.include_router(router, prefix="/api/v1/aurora")

    # Override dependencies
    async def override_get_db():
        return mock_db

    async def override_get_current_user():
        return mock_current_user

    async def override_get_tenant_context():
        return mock_tenant_context

    # Note: In real tests, you'd override:
    # app.dependency_overrides[get_db] = override_get_db
    # app.dependency_overrides[get_current_user] = override_get_current_user
    # etc.

    return app


@pytest_asyncio.fixture
async def async_client(
    mock_current_user,
    mock_tenant_context,
    mock_db,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client.

    Note: This is a simplified fixture. In a real Matrix deployment,
    you would set up the full app with proper dependency injection.
    """
    app = create_test_app(mock_current_user, mock_tenant_context, mock_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
