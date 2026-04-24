import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum("active", "ended", name="session_status"),
        default="active",
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    professor = relationship("User", back_populates="sessions")
    course = relationship("Course", back_populates="sessions")
    tokens = relationship("SessionToken", back_populates="session")
    attendance_records = relationship("Attendance", back_populates="session")


class SessionToken(Base):
    """One row per BLE token rotation (every ~20 seconds)."""

    __tablename__ = "session_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    token_id = Column(String, nullable=False)   # the "t" field from BLE payload
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # issued_at + ~25s
    used = Column(Boolean, default=False)

    session = relationship("Session", back_populates="tokens")
