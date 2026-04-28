"""
Test DB setup. Requires a 'attendance_test' MySQL database accessible to the 'attendance' user:
  sudo mysql -e "CREATE DATABASE IF NOT EXISTS attendance_test; GRANT ALL PRIVILEGES ON attendance_test.* TO 'attendance'@'localhost'; FLUSH PRIVILEGES;"
"""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models.attendance  # noqa — register with Base
import app.models.blocklist  # noqa
import app.models.course  # noqa
import app.models.session  # noqa
import app.models.user  # noqa
from app.config import settings
from app.database import Base, get_db
from app.main import app

TEST_DB_URL = settings.DATABASE_URL.replace("/attendance_db", "/attendance_test")

# NullPool: each fixture gets a fresh connection — prevents "operation in progress" errors
engine_test = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
TestSession = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        # Disable FK checks so tables can be dropped in any order (MySQL)
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DROP TABLE IF EXISTS `{table.name}`"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    async with engine_test.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=False))

    yield

    async with engine_test.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DROP TABLE IF EXISTS `{table.name}`"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


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
