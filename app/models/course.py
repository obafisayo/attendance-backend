import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    professor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professor = relationship("User", back_populates="courses")
    sessions = relationship("Session", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"

    student_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    course_id = Column(Uuid(as_uuid=True), ForeignKey("courses.id"), primary_key=True)

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
