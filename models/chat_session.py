import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )
