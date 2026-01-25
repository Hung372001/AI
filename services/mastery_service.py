from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.learning_mastery import LearningMastery


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


async def upsert_mastery(
    db: AsyncSession,
    user_id: str,
    topic: str,
    *,
    new_score: float | None = None,
    delta: float | None = None,
) -> LearningMastery:
    result = await db.execute(
        select(LearningMastery).where(
            LearningMastery.user_id == user_id,
            LearningMastery.topic == topic,
        )
    )
    mastery = result.scalar_one_or_none()

    if mastery is None:
        score = new_score if new_score is not None else (delta or 0.0)
        mastery = LearningMastery(
            user_id=user_id,
            topic=topic,
            mastery_score=_clamp(score),
        )
        db.add(mastery)
        return mastery

    if new_score is not None:
        mastery.mastery_score = _clamp(new_score)
    elif delta is not None:
        mastery.mastery_score = _clamp(mastery.mastery_score + delta)

    return mastery