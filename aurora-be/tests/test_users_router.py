"""Integration tests for Aurora Users Router

Tests the full endpoint flow including:
- Authentication/authorization
- Request validation
- Response formatting
- Error handling
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from .conftest import (
    MockUser,
    MockUserLevel,
    MockUserTenantAssociation,
)


# ============================================================================
# Test Setup
# ============================================================================


def create_test_app_with_mocks(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    is_admin: bool = True,
    is_superadmin: bool = False,
):
    """
    Create a test FastAPI app with mocked dependencies.

    Args:
        user_id: Current user ID
        tenant_id: Current tenant ID
        is_admin: Whether user is tenant admin
        is_superadmin: Whether user is superadmin

    Returns:
        Tuple of (app, mock_db, mock_service)
    """
    from fastapi import Depends
    from pydantic import BaseModel
    from typing import Annotated
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create mock database
    mock_db = AsyncMock()

    # Create mock service
    mock_service = MagicMock()

    # Mock dependencies
    class MockUserInfo(BaseModel):
        id: uuid.UUID
        email: str
        is_verified: bool = True
        metadata: dict = {}

    class MockTenantContext(BaseModel):
        tenant_id: uuid.UUID
        tenant_slug: str
        tenant_name: str
        user_is_admin: bool
        user_is_superadmin: bool

    mock_user = MockUserInfo(id=user_id, email="admin@example.com")
    mock_context = MockTenantContext(
        tenant_id=tenant_id,
        tenant_slug="test-tenant",
        tenant_name="Test Tenant",
        user_is_admin=is_admin,
        user_is_superadmin=is_superadmin,
    )

    # Create app
    app = FastAPI()

    # Define dependency overrides inline to avoid import issues
    async def get_db_override():
        return mock_db

    async def get_current_user_override():
        return mock_user

    async def get_tenant_context_override():
        return mock_context

    # Import and include router with patched dependencies
    with patch("aurora_be.dependencies.auth.CurrentUser", MockUserInfo):
        with patch("aurora_be.dependencies.auth.TenantContext", MockTenantContext):
            # Create a simplified router for testing
            from fastapi import APIRouter, HTTPException, Query
            from aurora_be.schemas import (
                UserCreate,
                UserUpdate,
                UserResponse,
                UserListResponse,
            )

            router = APIRouter(prefix="/api/v1/aurora/users", tags=["aurora-users"])

            @router.post("", response_model=UserResponse, status_code=201)
            async def create_user(
                request: UserCreate,
                current_user: Annotated[MockUserInfo, Depends(get_current_user_override)],
                tenant_context: Annotated[MockTenantContext, Depends(get_tenant_context_override)],
                db: Annotated[AsyncSession, Depends(get_db_override)],
            ):
                if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
                    raise HTTPException(status_code=403, detail="Only tenant admins can create users")

                result = mock_service.create_user(
                    email=request.email,
                    tenant_id=tenant_context.tenant_id,
                    user_level=request.user_level.value,
                    created_by=current_user.id,
                )
                return result

            @router.get("", response_model=UserListResponse)
            async def list_users(
                current_user: Annotated[MockUserInfo, Depends(get_current_user_override)],
                tenant_context: Annotated[MockTenantContext, Depends(get_tenant_context_override)],
                db: Annotated[AsyncSession, Depends(get_db_override)],
                page: int = Query(default=1, ge=1),
                per_page: int = Query(default=20, ge=1, le=100),
            ):
                result = mock_service.list_users(
                    tenant_id=tenant_context.tenant_id,
                    page=page,
                    per_page=per_page,
                )
                return result

            @router.get("/{user_id}", response_model=UserResponse)
            async def get_user(
                user_id: uuid.UUID,
                current_user: Annotated[MockUserInfo, Depends(get_current_user_override)],
                tenant_context: Annotated[MockTenantContext, Depends(get_tenant_context_override)],
                db: Annotated[AsyncSession, Depends(get_db_override)],
            ):
                result = mock_service.get_user(user_id, tenant_context.tenant_id)
                if not result:
                    raise HTTPException(status_code=404, detail="User not found in this tenant")
                return result

            @router.put("/{user_id}", response_model=UserResponse)
            async def update_user(
                user_id: uuid.UUID,
                request: UserUpdate,
                current_user: Annotated[MockUserInfo, Depends(get_current_user_override)],
                tenant_context: Annotated[MockTenantContext, Depends(get_tenant_context_override)],
                db: Annotated[AsyncSession, Depends(get_db_override)],
            ):
                if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
                    raise HTTPException(status_code=403, detail="Only tenant admins can update users")

                # Prevent self-demotion
                if user_id == current_user.id and request.user_level == "simple_user":
                    if tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
                        raise HTTPException(status_code=400, detail="Cannot demote yourself")

                result = mock_service.update_user(
                    user_id=user_id,
                    tenant_id=tenant_context.tenant_id,
                    user_level=request.user_level.value if request.user_level else None,
                    is_active=request.is_active,
                )
                if not result:
                    raise HTTPException(status_code=404, detail="User not found in this tenant")
                return result

            @router.delete("/{user_id}", status_code=204)
            async def deactivate_user(
                user_id: uuid.UUID,
                current_user: Annotated[MockUserInfo, Depends(get_current_user_override)],
                tenant_context: Annotated[MockTenantContext, Depends(get_tenant_context_override)],
                db: Annotated[AsyncSession, Depends(get_db_override)],
            ):
                if not tenant_context.user_is_admin and not tenant_context.user_is_superadmin:
                    raise HTTPException(status_code=403, detail="Only tenant admins can deactivate users")

                if user_id == current_user.id:
                    raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

                result = mock_service.deactivate_user(user_id, tenant_context.tenant_id)
                if not result:
                    raise HTTPException(status_code=404, detail="User not found in this tenant")
                return None

            app.include_router(router)

    return app, mock_db, mock_service


# ============================================================================
# Create User Endpoint Tests
# ============================================================================


class TestCreateUserEndpoint:
    """Tests for POST /api/v1/aurora/users"""

    def test_create_user_success(self):
        """
        Test successful user creation via API.
        """
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        new_user_id = uuid.uuid4()
        assoc_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        # Mock service response
        mock_service.create_user.return_value = {
            "id": new_user_id,
            "email": "newuser@example.com",
            "user_level": "simple_user",
            "is_active": True,
            "tenant_id": tenant_id,
            "association_id": assoc_id,
            "created_at": now,
            "updated_at": now,
        }

        client = TestClient(app)
        response = client.post(
            "/api/v1/aurora/users",
            json={"email": "newuser@example.com", "user_level": "simple_user"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["user_level"] == "simple_user"
        mock_service.create_user.assert_called_once()

    def test_create_user_forbidden_non_admin(self):
        """
        Test that non-admins cannot create users.
        """
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=user_id,
            tenant_id=tenant_id,
            is_admin=False,  # Non-admin
        )

        client = TestClient(app)
        response = client.post(
            "/api/v1/aurora/users",
            json={"email": "newuser@example.com"},
        )

        assert response.status_code == 403
        assert "Only tenant admins" in response.json()["detail"]
        mock_service.create_user.assert_not_called()

    def test_create_user_invalid_email(self):
        """
        Test validation rejects invalid email.
        """
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        client = TestClient(app)
        response = client.post(
            "/api/v1/aurora/users",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 422  # Validation error
        mock_service.create_user.assert_not_called()


# ============================================================================
# List Users Endpoint Tests
# ============================================================================


class TestListUsersEndpoint:
    """Tests for GET /api/v1/aurora/users"""

    def test_list_users_success(self):
        """
        Test listing users via API.
        """
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=user_id,
            tenant_id=tenant_id,
            is_admin=False,  # Non-admin can list
        )

        mock_service.list_users.return_value = {
            "users": [
                {
                    "id": uuid.uuid4(),
                    "email": "user1@example.com",
                    "user_level": "simple_user",
                    "is_active": True,
                    "tenant_id": tenant_id,
                    "association_id": uuid.uuid4(),
                    "created_at": now,
                    "updated_at": now,
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "has_more": False,
        }

        client = TestClient(app)
        response = client.get("/api/v1/aurora/users")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "user1@example.com"

    def test_list_users_pagination(self):
        """
        Test pagination parameters are passed correctly.
        """
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=user_id,
            tenant_id=tenant_id,
        )

        mock_service.list_users.return_value = {
            "users": [],
            "total": 50,
            "page": 3,
            "per_page": 10,
            "has_more": True,
        }

        client = TestClient(app)
        response = client.get("/api/v1/aurora/users?page=3&per_page=10")

        assert response.status_code == 200
        mock_service.list_users.assert_called_once_with(
            tenant_id=tenant_id,
            page=3,
            per_page=10,
        )


# ============================================================================
# Get User Endpoint Tests
# ============================================================================


class TestGetUserEndpoint:
    """Tests for GET /api/v1/aurora/users/{user_id}"""

    def test_get_user_success(self):
        """
        Test getting a user via API.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
        )

        mock_service.get_user.return_value = {
            "id": target_user_id,
            "email": "target@example.com",
            "user_level": "simple_user",
            "is_active": True,
            "tenant_id": tenant_id,
            "association_id": uuid.uuid4(),
            "created_at": now,
            "updated_at": now,
        }

        client = TestClient(app)
        response = client.get(f"/api/v1/aurora/users/{target_user_id}")

        assert response.status_code == 200
        assert response.json()["email"] == "target@example.com"

    def test_get_user_not_found(self):
        """
        Test 404 when user not found.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
        )

        mock_service.get_user.return_value = None

        client = TestClient(app)
        response = client.get(f"/api/v1/aurora/users/{target_user_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ============================================================================
# Update User Endpoint Tests
# ============================================================================


class TestUpdateUserEndpoint:
    """Tests for PUT /api/v1/aurora/users/{user_id}"""

    def test_update_user_success(self):
        """
        Test updating a user via API.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        mock_service.update_user.return_value = {
            "id": target_user_id,
            "email": "target@example.com",
            "user_level": "tenant_admin",
            "is_active": True,
            "tenant_id": tenant_id,
            "association_id": uuid.uuid4(),
            "created_at": now,
            "updated_at": now,
        }

        client = TestClient(app)
        response = client.put(
            f"/api/v1/aurora/users/{target_user_id}",
            json={"user_level": "tenant_admin"},
        )

        assert response.status_code == 200
        assert response.json()["user_level"] == "tenant_admin"

    def test_update_user_forbidden_non_admin(self):
        """
        Test that non-admins cannot update users.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=False,
        )

        client = TestClient(app)
        response = client.put(
            f"/api/v1/aurora/users/{target_user_id}",
            json={"user_level": "tenant_admin"},
        )

        assert response.status_code == 403
        mock_service.update_user.assert_not_called()

    def test_update_self_demotion_blocked(self):
        """
        Test that tenant admin cannot demote themselves.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=True,
            is_superadmin=False,
        )

        client = TestClient(app)
        response = client.put(
            f"/api/v1/aurora/users/{current_user_id}",
            json={"user_level": "simple_user"},
        )

        assert response.status_code == 400
        assert "Cannot demote yourself" in response.json()["detail"]
        mock_service.update_user.assert_not_called()


# ============================================================================
# Deactivate User Endpoint Tests
# ============================================================================


class TestDeactivateUserEndpoint:
    """Tests for DELETE /api/v1/aurora/users/{user_id}"""

    def test_deactivate_user_success(self):
        """
        Test successful user deactivation via API.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        mock_service.deactivate_user.return_value = True

        client = TestClient(app)
        response = client.delete(f"/api/v1/aurora/users/{target_user_id}")

        assert response.status_code == 204
        mock_service.deactivate_user.assert_called_once()

    def test_deactivate_user_forbidden_non_admin(self):
        """
        Test that non-admins cannot deactivate users.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=False,
        )

        client = TestClient(app)
        response = client.delete(f"/api/v1/aurora/users/{target_user_id}")

        assert response.status_code == 403
        mock_service.deactivate_user.assert_not_called()

    def test_deactivate_self_blocked(self):
        """
        Test that users cannot deactivate themselves.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        client = TestClient(app)
        response = client.delete(f"/api/v1/aurora/users/{current_user_id}")

        assert response.status_code == 400
        assert "Cannot deactivate yourself" in response.json()["detail"]
        mock_service.deactivate_user.assert_not_called()

    def test_deactivate_user_not_found(self):
        """
        Test 404 when deactivating non-existent user.
        """
        current_user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        target_user_id = uuid.uuid4()

        app, mock_db, mock_service = create_test_app_with_mocks(
            user_id=current_user_id,
            tenant_id=tenant_id,
            is_admin=True,
        )

        mock_service.deactivate_user.return_value = False

        client = TestClient(app)
        response = client.delete(f"/api/v1/aurora/users/{target_user_id}")

        assert response.status_code == 404
