import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base


class LearningMastery(Base):
    __tablename__ = "learning_mastery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic = Column(String, nullable=False)
    mastery_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="mastery")
