import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic = Column(String, nullable=False)
    difficulty = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="assignments")
    questions = relationship(
        "Question",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )
