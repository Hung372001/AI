import asyncio
from typing import List, Optional, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from core.database import get_db
from models.chat_message import ChatMessage
from models.chat_session import ChatSession
from models.user import User
from services.chroma_service import collection, get_current_user_id
from services.llm_service import generate_reply
from services.mastery_service import upsert_mastery

router = APIRouter(prefix="/api/tutor", tags=["Tutor"])


class TutorChatRequest(BaseModel):

    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None



class ContextChunk(BaseModel):
    chunk_id: str
    content: str
    score: float


class DiagramShape(BaseModel):
    type: str
    x: Optional[float] = None
    y: Optional[float] = None
    label: Optional[str] = None
    from_point: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    radius: Optional[float] = None

    class Config:
        allow_population_by_field_name = True


class Diagram(BaseModel):
    width: int
    height: int
    shapes: List[DiagramShape]


class TutorChatResponse(BaseModel):
    reply: str
    session_id: str
    context: List[ContextChunk]
    diagram: Optional[Diagram] = None

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: Optional[str] = None


class ChatMessagesResponse(BaseModel):
    messages: List[ChatMessageResponse]

class SessionSummary(BaseModel):
    id: str
    topic: Optional[str] = None
    created_at: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]

@router.post("/chat", response_model=TutorChatResponse)
async def tutor_chat(payload: TutorChatRequest, db: AsyncSession = Depends(get_db),user_id: str = Depends( get_current_user_id)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = None
    if payload.session_id:
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == payload.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session and str(session.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to user")

    if not session:
        session = ChatSession(user_id = user_id)
        db.add(session)
        await db.flush()

    query_kwargs = {
        "query_texts": [payload.message],
        "n_results": 3,
        "include": ["documents", "distances"],
    }
    # if payload.grade is not None:
    #     query_kwargs["where"] = {"grade": payload.grade}

    query_result = collection.query(**query_kwargs)
    documents = query_result.get("documents", [[]])[0]
    # if payload.grade is not None and not documents:
    #     query_kwargs.pop("where", None)
    #     query_result = collection.query(**query_kwargs)
    #     documents = query_result.get("documents", [[]])[0]

    contexts: List[ContextChunk] = []
    ids = query_result.get("ids", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    for chunk_id, content, distance in zip(ids, documents, distances):
        score = 1.0 - float(distance) if distance is not None else 0.0
        contexts.append(
            ContextChunk(chunk_id=str(chunk_id), content=content, score=round(score, 4))
        )

    context_texts = [item.content for item in contexts]

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
    )
    history_items = list(reversed(history_result.scalars().all()))
    history_lines = [
        f"{item.role}: {item.content}" for item in history_items
    ]

    try:
        response_payload = await generate_reply(
            payload.message,
            context_texts,
            history_lines,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if isinstance(response_payload, dict):
        reply = str(response_payload.get("reply", "")).strip()
        diagram = response_payload.get("diagram")
    else:
        reply = str(response_payload).strip()
        diagram = None

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
    # if payload.topic:
    #     await upsert_mastery(db, payload.user_id, payload.topic, delta=0.01)
    await db.commit()

    return TutorChatResponse(
        reply=reply,
        session_id=str(session.id),
        context=contexts,
        diagram=diagram,
    )
@router.post("/chat/stream")
async def tutor_chat_stream(payload: TutorChatRequest, db: AsyncSession = Depends(get_db),user_id: str = Depends( get_current_user_id)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = None
    if payload.session_id:
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == payload.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session and str(session.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to user")

    if not session:
        session = ChatSession(user_id=user_id)
        db.add(session)
        await db.flush()

    query_kwargs = {
        "query_texts": [payload.message],
        "n_results": 3,
        "include": ["documents", "distances"],
    }
    # if payload.grade is not None:
    #     query_kwargs["where"] = {"grade": payload.grade}

    query_result = collection.query(**query_kwargs)
    documents = query_result.get("documents", [[]])[0]
    # if payload.grade is not None and not documents:
    #     query_kwargs.pop("where", None)
    #     query_result = collection.query(**query_kwargs)
    #     documents = query_result.get("documents", [[]])[0]

    contexts: List[ContextChunk] = []
    ids = query_result.get("ids", [[]])[0]
    distances = query_result.get("distances", [[]])[0]
    for chunk_id, content, distance in zip(ids, documents, distances):
        score = 1.0 - float(distance) if distance is not None else 0.0
        contexts.append(
            ContextChunk(chunk_id=str(chunk_id), content=content, score=round(score, 4))
        )

    context_texts = [item.content for item in contexts]

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
    )
    history_items = list(reversed(history_result.scalars().all()))
    history_lines = [f"{item.role}: {item.content}" for item in history_items]

    try:
        response_payload = await generate_reply(
            payload.message,
            context_texts,
            history_lines,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if isinstance(response_payload, dict):
        reply = str(response_payload.get("reply", "")).strip()
    else:
        reply = str(response_payload).strip()

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
    # if payload.topic:
    #     await upsert_mastery(db, payload.user_id, payload.topic, delta=0.01)
    await db.commit()

    async def _stream() -> AsyncIterator[bytes]:
        for chunk in reply.split():
            yield f"{chunk} ".encode("utf-8")
            await asyncio.sleep(0)

    return StreamingResponse(_stream(), media_type="text/plain",    headers={"X-Session-Id": str(session.id)}
)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: str = Depends( get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = [
        SessionSummary(
            id=str(item.id),
            topic=item.topic,
            created_at=item.created_at.isoformat() if item.created_at else None,
        )
        for item in result.scalars().all()
    ]
    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    session_result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = [
        ChatMessageResponse(
            id=str(item.id),
            role=item.role,
            content=item.content,
            created_at=item.created_at.isoformat() if item.created_at else None,
        )
        for item in messages_result.scalars().all()
    ]
    return ChatMessagesResponse(messages=messages)