import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_id = Column(String(10), nullable=False)
    marked_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO: store face verification result when ML is integrated
    # face_verified = Column(Boolean, nullable=True)
    # face_confidence = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student"),
    )

    session = relationship("Session", back_populates="attendance_records")
    student = relationship("User", back_populates="attendance_records")
