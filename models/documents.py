from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from . import Base

class Documents(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String,nullable=False)
    doc_type = Column(String)
    source = Column(String)
    file_path  = Column(String, nullable=False)
    grade  = Column(Integer)
    topic =Column(String)
    uploaded_at   = Column(DateTime, server_default=func.now())

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )