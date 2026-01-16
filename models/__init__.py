from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# IMPORT MODEL SAU KHI CÓ BASE
from .documents import Documents
from .document_chunk import DocumentChunk
from .lesson import Lesson
from .user import User
from .user_profile import UserProfile
from .learning_mastery import LearningMastery
from .chat_session import ChatSession
from .chat_message import ChatMessage
from .assignment import Assignment
from .question import Question
from .attempt import Attempt
from .chunk_embedding import ChunkEmbedding
