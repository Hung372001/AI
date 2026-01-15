from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from . import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
