from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, sessions, attendance, courses, ml

app = FastAPI(
    title="Attendance API",
    version="1.0.0",
    description="BLE-based attendance system with facial recognition",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock this down to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])


@app.get("/health")
async def health():
    return {"status": "ok"}
