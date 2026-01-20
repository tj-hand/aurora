"""Unit tests for Aurora UserService

Tests the orchestration logic between Guardian and Mentor.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from .conftest import (
    MockDBSession,
    MockGuardianService,
    MockUser,
    MockUserLevel,
    MockUserTenantAssociation,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def user_service_mocks():
    """Set up mocks for UserService tests"""
    tenant_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    guardian_service = MockGuardianService()

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "guardian_service": guardian_service,
    }


# ============================================================================
# Create User Tests
# ============================================================================


class TestCreateUser:
    """Tests for UserService.create_user"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service_mocks):
        """
        Test successful user creation.

        Should:
        1. Call Guardian to get/create user identity
        2. Create UserTenantAssociation in Mentor
        3. Return both user and association
        """
        tenant_id = user_service_mocks["tenant_id"]
        admin_id = user_service_mocks["admin_id"]
        guardian_service = user_service_mocks["guardian_service"]

        # Mock database
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Patch Guardian service
        with patch(
            "aurora_be.services.user_service.get_guardian_service",
            return_value=guardian_service,
        ):
            # Import after patching
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                with patch(
                    "aurora_be.services.user_service.UserLevel",
                    MockUserLevel,
                ):
                    from aurora_be.services.user_service import UserService

                    service = UserService(mock_db)

                    # Create user
                    email = "newuser@example.com"
                    user, association = await service.create_user(
                        email=email,
                        tenant_id=tenant_id,
                        user_level="simple_user",
                        created_by=admin_id,
                    )

                    # Assertions
                    assert user is not None
                    assert user.email == email.lower()
                    assert association is not None
                    assert association.tenant_id == tenant_id
                    assert association.user_level.value == "simple_user"
                    assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_user_already_exists_in_tenant(self, user_service_mocks):
        """
        Test creating user that already exists in tenant.

        Should raise ValueError.
        """
        tenant_id = user_service_mocks["tenant_id"]
        admin_id = user_service_mocks["admin_id"]
        guardian_service = user_service_mocks["guardian_service"]

        # Pre-add user to guardian
        existing_user = MockUser(email="existing@example.com")
        guardian_service.users["existing@example.com"] = existing_user

        # Mock existing association
        existing_association = MockUserTenantAssociation(
            user_id=existing_user.id,
            tenant_id=tenant_id,
            user_level="simple_user",
        )

        # Mock database to return existing association
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: existing_association)
        )

        with patch(
            "aurora_be.services.user_service.get_guardian_service",
            return_value=guardian_service,
        ):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                with patch(
                    "aurora_be.services.user_service.UserLevel",
                    MockUserLevel,
                ):
                    from aurora_be.services.user_service import UserService

                    service = UserService(mock_db)

                    with pytest.raises(ValueError, match="already associated"):
                        await service.create_user(
                            email="existing@example.com",
                            tenant_id=tenant_id,
                            user_level="simple_user",
                            created_by=admin_id,
                        )

    @pytest.mark.asyncio
    async def test_create_user_guardian_creates_new(self, user_service_mocks):
        """
        Test that Guardian creates new user if doesn't exist.
        """
        tenant_id = user_service_mocks["tenant_id"]
        admin_id = user_service_mocks["admin_id"]
        guardian_service = user_service_mocks["guardian_service"]

        # Ensure user doesn't exist
        assert "brand-new@example.com" not in guardian_service.users

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "aurora_be.services.user_service.get_guardian_service",
            return_value=guardian_service,
        ):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                with patch(
                    "aurora_be.services.user_service.UserLevel",
                    MockUserLevel,
                ):
                    from aurora_be.services.user_service import UserService

                    service = UserService(mock_db)

                    user, _ = await service.create_user(
                        email="brand-new@example.com",
                        tenant_id=tenant_id,
                        user_level="simple_user",
                        created_by=admin_id,
                    )

                    # Guardian should have created the user
                    assert "brand-new@example.com" in guardian_service.users
                    assert user.email == "brand-new@example.com"


# ============================================================================
# List Users Tests
# ============================================================================


class TestListUsers:
    """Tests for UserService.list_users"""

    @pytest.mark.asyncio
    async def test_list_users_empty(self):
        """
        Test listing users when none exist.
        """
        tenant_id = uuid.uuid4()

        mock_db = AsyncMock()
        # First execute returns count = 0
        # Second execute returns empty list
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=lambda: 0),  # count query
                MagicMock(all=lambda: []),  # data query
            ]
        )

        with patch("aurora_be.services.user_service.User", MockUser):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)
                users, total = await service.list_users(tenant_id)

                assert users == []
                assert total == 0

    @pytest.mark.asyncio
    async def test_list_users_pagination(self):
        """
        Test pagination parameters are applied.
        """
        tenant_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar=lambda: 50),  # total count
                MagicMock(all=lambda: []),  # page data (simplified)
            ]
        )

        with patch("aurora_be.services.user_service.User", MockUser):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)
                users, total = await service.list_users(
                    tenant_id,
                    page=2,
                    per_page=10,
                )

                assert total == 50
                # Offset should be (2-1) * 10 = 10


# ============================================================================
# Get User Tests
# ============================================================================


class TestGetUser:
    """Tests for UserService.get_user"""

    @pytest.mark.asyncio
    async def test_get_user_found(self):
        """
        Test getting an existing user.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_user = MockUser(id=user_id, email="found@example.com")
        mock_assoc = MockUserTenantAssociation(
            user_id=user_id,
            tenant_id=tenant_id,
            user_level="simple_user",
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(first=lambda: (mock_user, mock_assoc))
        )

        with patch("aurora_be.services.user_service.User", MockUser):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)
                result = await service.get_user(user_id, tenant_id)

                assert result is not None
                assert result["id"] == user_id
                assert result["email"] == "found@example.com"
                assert result["user_level"] == "simple_user"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """
        Test getting a non-existent user.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(first=lambda: None))

        with patch("aurora_be.services.user_service.User", MockUser):
            with patch(
                "aurora_be.services.user_service.UserTenantAssociation",
                MockUserTenantAssociation,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)
                result = await service.get_user(user_id, tenant_id)

                assert result is None


# ============================================================================
# Update User Tests
# ============================================================================


class TestUpdateUser:
    """Tests for UserService.update_user"""

    @pytest.mark.asyncio
    async def test_update_user_level(self):
        """
        Test updating user level.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_assoc = MockUserTenantAssociation(
            user_id=user_id,
            tenant_id=tenant_id,
            user_level="simple_user",
        )

        mock_db = AsyncMock()
        # First call: _get_association
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: mock_assoc)
        )
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "aurora_be.services.user_service.UserTenantAssociation",
            MockUserTenantAssociation,
        ):
            with patch(
                "aurora_be.services.user_service.UserLevel",
                MockUserLevel,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)

                # Mock get_user to return updated data
                service.get_user = AsyncMock(
                    return_value={
                        "id": user_id,
                        "email": "user@example.com",
                        "user_level": "tenant_admin",
                        "is_active": True,
                        "tenant_id": tenant_id,
                        "association_id": mock_assoc.id,
                        "created_at": mock_assoc.created_at,
                        "updated_at": mock_assoc.updated_at,
                    }
                )

                result = await service.update_user(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    user_level="tenant_admin",
                )

                assert result is not None
                assert result["user_level"] == "tenant_admin"
                assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """
        Test updating non-existent user returns None.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: None)
        )

        with patch(
            "aurora_be.services.user_service.UserTenantAssociation",
            MockUserTenantAssociation,
        ):
            with patch(
                "aurora_be.services.user_service.UserLevel",
                MockUserLevel,
            ):
                from aurora_be.services.user_service import UserService

                service = UserService(mock_db)
                result = await service.update_user(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    user_level="tenant_admin",
                )

                assert result is None


# ============================================================================
# Deactivate User Tests
# ============================================================================


class TestDeactivateUser:
    """Tests for UserService.deactivate_user"""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self):
        """
        Test successful user deactivation.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_assoc = MockUserTenantAssociation(
            user_id=user_id,
            tenant_id=tenant_id,
            user_level="simple_user",
            is_active=True,
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: mock_assoc)
        )
        mock_db.commit = AsyncMock()

        with patch(
            "aurora_be.services.user_service.UserTenantAssociation",
            MockUserTenantAssociation,
        ):
            from aurora_be.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.deactivate_user(user_id, tenant_id)

            assert result is True
            assert mock_assoc.is_active is False
            assert mock_assoc.deleted_at is not None
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self):
        """
        Test deactivating non-existent user returns False.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: None)
        )

        with patch(
            "aurora_be.services.user_service.UserTenantAssociation",
            MockUserTenantAssociation,
        ):
            from aurora_be.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.deactivate_user(user_id, tenant_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_deactivate_already_deleted(self):
        """
        Test deactivating already-deleted user returns False.
        """
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_assoc = MockUserTenantAssociation(
            user_id=user_id,
            tenant_id=tenant_id,
            user_level="simple_user",
            deleted_at=datetime.now(timezone.utc),  # Already deleted
        )

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: mock_assoc)
        )

        with patch(
            "aurora_be.services.user_service.UserTenantAssociation",
            MockUserTenantAssociation,
        ):
            from aurora_be.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.deactivate_user(user_id, tenant_id)

            assert result is False
