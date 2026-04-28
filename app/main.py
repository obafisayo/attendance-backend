from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import delete

from app.config import settings
from app.routers import auth, sessions, attendance, courses, ml, users, dashboard

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Clean up expired blocklist entries on startup so the table doesn't grow forever
    from app.database import AsyncSessionLocal
    from app.models.blocklist import TokenBlocklist
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(TokenBlocklist).where(TokenBlocklist.expires_at < datetime.now(timezone.utc))
        )
        await db.commit()
    yield


app = FastAPI(
    title="Attendance API",
    version="1.0.0",
    description="BLE-based attendance system with facial recognition",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_PROD_ORIGINS = [
    # Add your production domain here, e.g. "https://attendance.youruniversity.edu"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else _PROD_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok"}
