from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.assignment import Assignment
from models.attempt import Attempt
from models.question import Question
from models.user import User
from services.chroma_service import collection
from services.llm_service import generate_questions
from services.mastery_service import upsert_mastery

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


class CreateAssignmentRequest(BaseModel):
    user_id: str
    topic: str
    difficulty: int | None = None


class AssignmentResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    difficulty: int | None = None


class AttemptPayload(BaseModel):
    question_id: str
    student_answer: str
    score: float = Field(..., ge=0.0, le=1.0)


class SubmitAssignmentRequest(BaseModel):
    user_id: str
    topic: str
    attempts: List[AttemptPayload]


class SubmitAssignmentResponse(BaseModel):
    assignment_id: str
    mastery_score: float
    results: List[AttemptPayload]


class GenerateQuestionsRequest(BaseModel):
    topic: str | None = None
    count: int = Field(3, ge=1, le=10)


class QuestionResponse(BaseModel):
    id: str
    question_text: str
    hint: str | None = None


class GenerateQuestionsResponse(BaseModel):
    assignment_id: str
    questions: List[QuestionResponse]


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    payload: CreateAssignmentRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == payload.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    assignment = Assignment(
        user_id=payload.user_id,
        topic=payload.topic,
        difficulty=payload.difficulty,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return AssignmentResponse(
        id=str(assignment.id),
        user_id=str(assignment.user_id),
        topic=assignment.topic,
        difficulty=assignment.difficulty,
    )


@router.post("/{assignment_id}/submit", response_model=SubmitAssignmentResponse)
async def submit_assignment(
    assignment_id: str,
    payload: SubmitAssignmentRequest,
    db: AsyncSession = Depends(get_db),
):
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if str(assignment.user_id) != payload.user_id:
        raise HTTPException(status_code=403, detail="Assignment does not belong to user")

    if not payload.attempts:
        raise HTTPException(status_code=400, detail="Attempts required")

    total_score = 0.0
    results: List[AttemptPayload] = []
    for attempt in payload.attempts:
        total_score += attempt.score
        db.add(
            Attempt(
                question_id=attempt.question_id,
                user_id=payload.user_id,
                student_answer=attempt.student_answer,
                score=attempt.score,
            )
        )
        results.append(attempt)

    mastery_score = total_score / len(payload.attempts)
    mastery = await upsert_mastery(
        db,
        payload.user_id,
        payload.topic,
        new_score=mastery_score,
    )

    await db.commit()
    await db.refresh(mastery)

    return SubmitAssignmentResponse(
        assignment_id=str(assignment.id),
        mastery_score=mastery.mastery_score,
        results=results,
    )


@router.post("/{assignment_id}/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_assignment_questions(
    assignment_id: str,
    payload: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    topic = payload.topic or assignment.topic
    query_result = collection.query(
        query_texts=[topic],
        n_results=5,
        include=["documents"],
    )
    documents = query_result.get("documents", [[]])[0]

    try:
        generated = await generate_questions(topic, documents, payload.count)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    questions: List[QuestionResponse] = []
    for item in generated[: payload.count]:
        question_text = str(item.get("question_text", "")).strip()
        if not question_text:
            continue
        question = Question(
            assignment_id=assignment.id,
            question_text=question_text,
            hint=item.get("hint"),
        )
        db.add(question)
        await db.flush()
        questions.append(
            QuestionResponse(
                id=str(question.id),
                question_text=question.question_text,
                hint=question.hint,
            )
        )

    await db.commit()

    return GenerateQuestionsResponse(
        assignment_id=str(assignment.id),
        questions=questions,
    )
