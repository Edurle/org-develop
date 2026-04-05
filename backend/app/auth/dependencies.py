import json
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token, pwd_context
from app.database import get_db
from app.models.auth import ApiKey
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current user from JWT token."""
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_current_user_from_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, list[str]]:
    """Get user and scopes from API key."""
    token = credentials.credentials
    prefix = token[:8]

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Verify full key hash
    if not pwd_context.verify(token, api_key.key_hash):
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API key expired")

    user_result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    scopes = json.loads(api_key.scopes)
    return user, scopes


def require_scope(required_scope: str):
    """Dependency factory to require a specific API key scope."""

    async def check_scope(
        auth: tuple = Depends(get_current_user_from_api_key),
    ) -> tuple[User, list[str]]:
        user, scopes = auth
        # Admin scope grants all
        if "*" in scopes or required_scope in scopes:
            return user, scopes
        # Check wildcard patterns like "requirements:*"
        resource, action = required_scope.split(":")
        if f"{resource}:*" in scopes:
            return user, scopes
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required scope: {required_scope}",
        )

    return check_scope


def generate_api_key() -> tuple[str, str, str]:
    """Generate an API key. Returns (raw_key, prefix, hash)."""
    raw_key = f"odk_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:8]
    hashed = pwd_context.hash(raw_key)
    return raw_key, prefix, hashed
