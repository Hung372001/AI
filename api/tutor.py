from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.chat_message import ChatMessage
from models.chat_session import ChatSession
from models.user import User
from services.chroma_service import collection
from services.llm_service import generate_reply

router = APIRouter(prefix="/api/tutor", tags=["Tutor"])


class TutorChatRequest(BaseModel):
    user_id: str = Field(..., description="UUID của người học")
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    topic: Optional[str] = None
    grade: Optional[int] = None


class ContextChunk(BaseModel):
    chunk_id: str
    content: str
    score: float


class TutorChatResponse(BaseModel):
    reply: str
    session_id: str
    context: List[ContextChunk]


@router.post("/chat", response_model=TutorChatResponse)
async def tutor_chat(payload: TutorChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = None
    if payload.session_id:
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == payload.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session and str(session.user_id) != payload.user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to user")

    if not session:
        session = ChatSession(user_id=payload.user_id, topic=payload.topic)
        db.add(session)
        await db.flush()

    query_result = collection.query(
        query_texts=[payload.message],
        n_results=3,
        include=["documents", "distances"],
    )

    contexts: List[ContextChunk] = []
    documents = query_result.get("documents", [[]])[0]
    ids = query_result.get("ids", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    for chunk_id, content, distance in zip(ids, documents, distances):
        score = 1.0 - float(distance) if distance is not None else 0.0
        contexts.append(
            ContextChunk(chunk_id=str(chunk_id), content=content, score=round(score, 4))
        )

    context_texts = [item.content for item in contexts]

    try:
        reply = await generate_reply(payload.message, context_texts)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.message,
    )
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply,
    )
    db.add_all([user_message, assistant_message])
    await db.commit()

    return TutorChatResponse(
        reply=reply,
        session_id=str(session.id),
        context=contexts,
    )