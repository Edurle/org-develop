"""Unit tests for user service layer.

Tests create, read, and update operations on users,
including uniqueness constraints for username and email.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import create_user, get_user_by_username, get_user, update_user, list_users


# ────────────────────────────────────────────────────────────
# Create User
# ────────────────────────────────────────────────────────────

class TestCreateUser:
    async def test_create_user(self, db: AsyncSession):
        user = await create_user(
            db, "testuser1", "test1@example.com", "password123"
        )
        assert user.username == "testuser1"
        assert user.email == "test1@example.com"
        assert user.display_name is None
        assert user.is_active is True

    async def test_create_user_with_display_name(self, db: AsyncSession):
        user = await create_user(
            db, "testuser2", "test2@example.com", "password123",
            display_name="Test User 2",
        )
        assert user.display_name == "Test User 2"

    async def test_duplicate_username_raises_value_error(self, db: AsyncSession):
        await create_user(db, "testuser3", "test3@example.com", "password123")
        with pytest.raises(ValueError, match="already exists"):
            await create_user(db, "testuser3", "other@example.com", "password456")

    async def test_duplicate_email_raises_value_error(self, db: AsyncSession):
        await create_user(db, "testuser4", "test4@example.com", "password123")
        with pytest.raises(ValueError, match="already exists"):
            await create_user(db, "different", "test4@example.com", "password456")

    async def test_duplicate_username_and_email_raises_value_error(self, db: AsyncSession):
        await create_user(db, "testuser5", "test5@example.com", "password123")
        with pytest.raises(ValueError, match="already exists"):
            await create_user(db, "testuser5", "test5@example.com", "password123")


# ────────────────────────────────────────────────────────────
# Get User
# ────────────────────────────────────────────────────────────

class TestGetUser:
    async def test_get_by_username(self, db: AsyncSession):
        user = await create_user(
            db, "finduser1", "find1@example.com", "password123"
        )
        result = await get_user_by_username(db, "finduser1")
        assert result is not None
        assert result.id == user.id
        assert result.username == "finduser1"

    async def test_get_by_username_nonexistent(self, db: AsyncSession):
        result = await get_user_by_username(db, "nonexistent")
        assert result is None

    async def test_get_by_id(self, db: AsyncSession):
        user = await create_user(
            db, "finduser2", "find2@example.com", "password123"
        )
        result = await get_user(db, user.id)
        assert result is not None
        assert result.id == user.id
        assert result.username == "finduser2"

    async def test_get_by_id_nonexistent(self, db: AsyncSession):
        result = await get_user(db, "nonexistent-id")
        assert result is None


# ────────────────────────────────────────────────────────────
# Update User
# ────────────────────────────────────────────────────────────

class TestUpdateUser:
    async def test_update_display_name(self, db: AsyncSession):
        user = await create_user(
            db, "upuser1", "up1@example.com", "password123"
        )
        updated = await update_user(db, user.id, display_name="Updated Name")
        assert updated.display_name == "Updated Name"
        assert updated.email == "up1@example.com"

    async def test_update_email(self, db: AsyncSession):
        user = await create_user(
            db, "upuser2", "up2@example.com", "password123"
        )
        updated = await update_user(db, user.id, email="new@example.com")
        assert updated.email == "new@example.com"

    async def test_update_both_display_name_and_email(self, db: AsyncSession):
        user = await create_user(
            db, "upuser3", "up3@example.com", "password123"
        )
        updated = await update_user(
            db, user.id, display_name="New Name", email="both@example.com"
        )
        assert updated.display_name == "New Name"
        assert updated.email == "both@example.com"

    async def test_update_duplicate_email_raises_value_error(self, db: AsyncSession):
        await create_user(db, "upuser4a", "up4a@example.com", "password123")
        user = await create_user(db, "upuser4b", "up4b@example.com", "password123")
        with pytest.raises(ValueError, match="already in use"):
            await update_user(db, user.id, email="up4a@example.com")

    async def test_update_nonexistent_user_raises_value_error(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not found"):
            await update_user(db, "nonexistent-id", display_name="Ghost")

    async def test_update_no_fields_leaves_user_unchanged(self, db: AsyncSession):
        user = await create_user(
            db, "upuser5", "up5@example.com", "password123",
            display_name="Original",
        )
        updated = await update_user(db, user.id)
        assert updated.username == "upuser5"
        assert updated.display_name == "Original"
        assert updated.email == "up5@example.com"


# ────────────────────────────────────────────────────────────
# List Users
# ────────────────────────────────────────────────────────────

class TestListUsers:
    async def test_list_all_users(self, db: AsyncSession):
        await create_user(db, "listuser1", "list1@example.com", "password123")
        await create_user(db, "listuser2", "list2@example.com", "password123")
        users = await list_users(db)
        assert len(users) >= 2
        usernames = [u.username for u in users]
        assert "listuser1" in usernames
        assert "listuser2" in usernames

    async def test_list_users_with_search(self, db: AsyncSession):
        await create_user(db, "searchalice", "alice@example.com", "password123", display_name="Alice Wonderland")
        await create_user(db, "searchbob", "bob@example.com", "password123", display_name="Bob Builder")
        users = await list_users(db, search="alice")
        assert len(users) == 1
        assert users[0].username == "searchalice"

    async def test_list_users_search_by_display_name(self, db: AsyncSession):
        await create_user(db, "dispuser1", "disp1@example.com", "password123", display_name="Charlie Chief")
        await create_user(db, "dispuser2", "disp2@example.com", "password123", display_name="David Developer")
        users = await list_users(db, search="Charlie")
        assert len(users) == 1
        assert users[0].display_name == "Charlie Chief"

    async def test_list_users_search_no_results(self, db: AsyncSession):
        users = await list_users(db, search="nonexistent_user_xyz")
        assert len(users) == 0

    async def test_list_users_empty_db(self, db: AsyncSession):
        users = await list_users(db)
        assert isinstance(users, list)
