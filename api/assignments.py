from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.assignment import Assignment
from models.attempt import Attempt
from models.user import User
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
