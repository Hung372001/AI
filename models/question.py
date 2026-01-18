import uuid
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from . import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text = Column(Text, nullable=False)
    answer_key = Column(Text)
    hint = Column(Text)

    assignment = relationship("Assignment", back_populates="questions")
    attempts = relationship(
        "Attempt",
        back_populates="question",
        cascade="all, delete-orphan",
    )