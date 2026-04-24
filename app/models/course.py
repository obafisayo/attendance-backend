import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False)       # e.g. "CSC 401"
    name = Column(String, nullable=False)       # e.g. "Mobile Development"
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professor = relationship("User", back_populates="courses")
    sessions = relationship("Session", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"

    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), primary_key=True)

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
