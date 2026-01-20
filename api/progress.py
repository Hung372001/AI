from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.learning_mastery import LearningMastery
from models.user import User

router = APIRouter(prefix="/api/progress", tags=["Progress"])


class TopicMastery(BaseModel):
    topic: str
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime | None = None


class ProgressResponse(BaseModel):
    user_id: str
    topics: List[TopicMastery]


class UpdateMasteryRequest(BaseModel):
    user_id: str
    topic: str
    mastery_score: float = Field(..., ge=0.0, le=1.0)


@router.get("", response_model=ProgressResponse)
async def get_progress(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    mastery_result = await db.execute(
        select(LearningMastery).where(LearningMastery.user_id == user_id)
    )
    topics = [
        TopicMastery(
            topic=item.topic,
            mastery_score=item.mastery_score,
            last_updated=item.last_updated,
        )
        for item in mastery_result.scalars().all()
    ]

    return ProgressResponse(user_id=str(user.id), topics=topics)


@router.post("/update", response_model=TopicMastery)
async def update_mastery(payload: UpdateMasteryRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    mastery_result = await db.execute(
        select(LearningMastery).where(
            LearningMastery.user_id == payload.user_id,
            LearningMastery.topic == payload.topic,
        )
    )
    mastery = mastery_result.scalar_one_or_none()

    if not mastery:
        mastery = LearningMastery(
            user_id=payload.user_id,
            topic=payload.topic,
            mastery_score=payload.mastery_score,
        )
        db.add(mastery)
    else:
        mastery.mastery_score = payload.mastery_score

    await db.commit()
    await db.refresh(mastery)

    return TopicMastery(
        topic=mastery.topic,
        mastery_score=mastery.mastery_score,
        last_updated=mastery.last_updated,
    )