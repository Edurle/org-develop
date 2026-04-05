"""Service layer for user management."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.models.user import User
from app.services.audit import log_action


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    display_name: str | None = None,
) -> User:
    """Create a new user. Raises ValueError if username or email already exists."""
    existing = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if existing.scalar_one_or_none():
        raise ValueError("Username or email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
    )
    db.add(user)
    await db.flush()
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    user_id: str,
    display_name: str | None = None,
    email: str | None = None,
) -> User:
    """Update user profile fields."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise ValueError(f"User '{user_id}' not found")

    if email is not None:
        # Check uniqueness
        existing = await db.execute(
            select(User).where(User.email == email, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Email '{email}' already in use")
        user.email = email

    if display_name is not None:
        user.display_name = display_name
    await db.flush()
    await log_action(
        db, user_id=user_id, action="user.update",
        resource_type="user", resource_id=user_id,
        detail="Updated user profile",
    )
    return user
