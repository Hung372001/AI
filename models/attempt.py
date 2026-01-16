import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_answer = Column(Text, nullable=False)
    score = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    question = relationship("Question", back_populates="attempts")
    user = relationship("User", back_populates="attempts")
