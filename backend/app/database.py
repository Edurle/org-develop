from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


mongo_client: Optional[object] = None
mongo_db: Optional[object] = None


async def init_mongo() -> None:
    global mongo_client, mongo_db
    if settings.MONGO_URL is None:
        return

    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    mongo_db = mongo_client[settings.MONGO_DB_NAME]


async def close_mongo() -> None:
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
