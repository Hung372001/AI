from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# IMPORT MODEL SAU KHI CÓ BASE
from .documents import Documents
from .document_chunk import DocumentChunk
from .lesson import Lesson