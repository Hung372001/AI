import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from . import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    role = Column(String, default="student")
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)
    password = Column(String, nullable=False)
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    mastery = relationship(
        "LearningMastery",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    assignments = relationship(
        "Assignment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    attempts = relationship(
        "Attempt",
        back_populates="user",
        cascade="all, delete-orphan",
    )