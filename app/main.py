from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import auth, sessions, attendance, courses, ml, users, enrollments, dashboard

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Attendance API",
    version="1.0.0",
    description="BLE-based attendance system with facial recognition",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_PROD_ORIGINS: list[str] = [
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


@app.get("/health")
async def health():
    return {"status": "ok"}
