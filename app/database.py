from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# --- URL NORMALIZATION ---
# This fixes the "Could not parse SQLAlchemy URL" error by ensuring 
# the async driver (+aiomysql) is present.
db_url = settings.DATABASE_URL

# Remove accidental double-naming if "DATABASE_URL=" was pasted into the value
if db_url.startswith("DATABASE_URL="):
    db_url = db_url.replace("DATABASE_URL=", "", 1)

if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+aiomysql://", 1)

# --- ENGINE CREATION ---
engine = create_async_engine(
    db_url, 
    echo=True,
    pool_pre_ping=True,  # Prevents "Link Failure" errors on Railway
    pool_recycle=3600    # Closes connections before MySQL timeouts
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # For async, the 'async with' block handles closing, 
            # but explicit close is safe.
            await session.close()
