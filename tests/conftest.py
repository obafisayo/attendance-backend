"""
Test DB setup. Requires a 'attendance_test' database:
  docker compose exec db psql -U attendance -d attendance_db -c "CREATE DATABASE attendance_test;"
"""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models.attendance  # noqa — register with Base
import app.models.blocklist   # noqa
import app.models.course      # noqa
import app.models.session     # noqa
import app.models.user        # noqa
from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DB_URL = settings.DATABASE_URL.replace("/attendance_db", "/attendance_test")

# NullPool: each fixture gets a fresh connection — prevents asyncpg "operation in progress" errors
engine_test = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
TestSession = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.execute(text(
            "DROP TABLE IF EXISTS attendance, session_tokens, sessions, enrollments, "
            "courses, token_blocklist, users CASCADE"
        ))
        await conn.execute(text(
            "DROP TYPE IF EXISTS user_role, session_status CASCADE"
        ))

    async with engine_test.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=False))

    yield

    async with engine_test.begin() as conn:
        await conn.execute(text(
            "DROP TABLE IF EXISTS attendance, session_tokens, sessions, enrollments, "
            "courses, token_blocklist, users CASCADE"
        ))
        await conn.execute(text(
            "DROP TYPE IF EXISTS user_role, session_status CASCADE"
        ))


@pytest_asyncio.fixture
async def db(setup_db):
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
