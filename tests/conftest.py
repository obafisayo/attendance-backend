"""
Test DB setup. Requires a 'attendance_test' database:
  docker exec <db-container> psql -U attendance -c "CREATE DATABASE attendance_test;"
"""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models.attendance  # noqa — register with Base
import app.models.course  # noqa
import app.models.session  # noqa
import app.models.user  # noqa
from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DB_URL = settings.DATABASE_URL.replace("/attendance_db", "/attendance_test")

engine_test = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(create_tables):
    async with engine_test.begin() as conn:
        await conn.execute(text("DELETE FROM attendance"))
        await conn.execute(text("DELETE FROM session_tokens"))
        await conn.execute(text("DELETE FROM sessions"))
        await conn.execute(text("DELETE FROM enrollments"))
        await conn.execute(text("DELETE FROM courses"))
        await conn.execute(text("DELETE FROM users"))
    yield


@pytest_asyncio.fixture
async def db(clean_tables):
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
