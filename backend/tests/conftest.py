"""Test fixtures: fresh in-memory SQLite per test for full isolation."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base
from app.models import *  # noqa: F401, F403 — register all models
from app.services.user import create_user
from app.services.team import create_organization, create_team, add_team_member


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Per-test DB with fresh SQLite in-memory database for full isolation."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seed_data(db: AsyncSession):
    """Create org, team, project, iteration, and a test user."""
    import uuid

    unique = uuid.uuid4().hex[:8]
    org = await create_organization(db, f"Test Org {unique}", f"test-org-{unique}")
    team = await create_team(db, org.id, f"Test Team {unique}", f"test-team-{unique}")
    user = await create_user(
        db, f"testuser-{unique}", f"test-{unique}@example.com", "password123", "Test User"
    )
    await add_team_member(db, team.id, user.id, '["admin"]')

    from app.models.project import Project

    project = Project(
        team_id=team.id, name=f"Test Project {unique}", slug=f"test-project-{unique}"
    )
    db.add(project)
    await db.flush()

    from app.models.iteration import Iteration

    iteration = Iteration(project_id=project.id, name="Sprint 1", status="active")
    db.add(iteration)
    await db.flush()

    return {
        "org": org,
        "team": team,
        "user": user,
        "project": project,
        "iteration": iteration,
    }
