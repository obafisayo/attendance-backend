import uuid
from sqlalchemy import Column, String, Enum, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    matric_no = Column(String, unique=True, nullable=True)  # students only
    password_hash = Column(String, nullable=False)
    role = Column(Enum("student", "professor", name="user_role"), nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    failed_login_attempts = Column(Integer, nullable=False, server_default="0", default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # TODO: add face_embedding column (LargeBinary or Vector) when ML is ready
    # face_embedding = Column(LargeBinary, nullable=True)

    courses = relationship("Course", back_populates="professor")
    sessions = relationship("Session", back_populates="professor")
    enrollments = relationship("Enrollment", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")
