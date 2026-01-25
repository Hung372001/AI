from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.learning_mastery import LearningMastery
from models.lesson import Lesson
from models.user import User
from models.user_profile import UserProfile

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])


class RecommendLessonRequest(BaseModel):
    user_id: str
    topic: Optional[str] = None


class RecommendLessonResponse(BaseModel):
    lesson_id: str
    grade: int
    topic: str
    difficulty: int | None = None
    mastery_score: float | None = None
    reason: str


def _target_difficulty(mastery_score: Optional[float]) -> int | None:
    if mastery_score is None:
        return None
    if mastery_score < 0.4:
        return 1
    if mastery_score < 0.7:
        return 2
    return 3


@router.post("/recommend", response_model=RecommendLessonResponse)
async def recommend_lesson(
    payload: RecommendLessonRequest,
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == payload.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile or profile.grade_level is None:
        raise HTTPException(status_code=400, detail="User grade level is required")

    topic = payload.topic
    mastery_score: float | None = None
    if not topic:
        mastery_result = await db.execute(
            select(LearningMastery)
            .where(LearningMastery.user_id == payload.user_id)
            .order_by(LearningMastery.mastery_score.asc())
        )
        mastery = mastery_result.scalars().first()
        if mastery:
            topic = mastery.topic
            mastery_score = mastery.mastery_score

    if not topic:
        lesson_result = await db.execute(
            select(Lesson)
            .where(Lesson.grade == profile.grade_level)
            .order_by(Lesson.created_at.desc())
        )
        lesson = lesson_result.scalars().first()
        if not lesson:
            raise HTTPException(status_code=404, detail="No lessons available")
        return RecommendLessonResponse(
            lesson_id=str(lesson.id),
            grade=lesson.grade,
            topic=lesson.topic,
            difficulty=lesson.difficulty,
            mastery_score=None,
            reason="No mastery data available; selected latest lesson for grade.",
        )

    if mastery_score is None:
        mastery_result = await db.execute(
            select(LearningMastery)
            .where(
                LearningMastery.user_id == payload.user_id,
                LearningMastery.topic == topic,
            )
            .limit(1)
        )
        mastery = mastery_result.scalar_one_or_none()
        mastery_score = mastery.mastery_score if mastery else None

    lesson_result = await db.execute(
        select(Lesson).where(
            Lesson.grade == profile.grade_level,
            Lesson.topic == topic,
        )
    )
    lessons = lesson_result.scalars().all()
    if not lessons:
        lesson_result = await db.execute(
            select(Lesson)
            .where(Lesson.grade == profile.grade_level)
            .order_by(Lesson.created_at.desc())
        )
        lesson = lesson_result.scalars().first()
        if not lesson:
            raise HTTPException(status_code=404, detail="No lessons available")
        return RecommendLessonResponse(
            lesson_id=str(lesson.id),
            grade=lesson.grade,
            topic=lesson.topic,
            difficulty=lesson.difficulty,
            mastery_score=mastery_score,
            reason="No lesson matched topic; selected latest lesson for grade.",
        )

    target = _target_difficulty(mastery_score)
    if target is None:
        lesson = lessons[0]
        reason = "Selected lesson for topic without mastery-based difficulty tuning."
    else:
        lesson = min(
            lessons,
            key=lambda item: abs((item.difficulty or target) - target),
        )
        reason = "Selected lesson matching weakest mastery topic and difficulty band."

    return RecommendLessonResponse(
        lesson_id=str(lesson.id),
        grade=lesson.grade,
        topic=lesson.topic,
        difficulty=lesson.difficulty,
        mastery_score=mastery_score,
        reason=reason,
    )