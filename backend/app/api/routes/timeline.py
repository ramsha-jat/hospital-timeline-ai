# app/api/routes/timeline.py

from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.connection import get_db
from app.timeline.builder import TimelineBuilder
from app.timeline.schemas import EventCategory, PatientTimeline


router = APIRouter()


@router.get("/{hadm_id}", response_model=PatientTimeline)
async def get_timeline(
    hadm_id: int,
    categories: Optional[str] = Query(None),
    group_high_volume: bool = Query(True),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    include_categories = None

    if categories:
        include_categories = [
            EventCategory(c.strip())
            for c in categories.split(",")
        ]

    builder = TimelineBuilder(db)

    timeline = await builder.build_timeline(
        hadm_id=hadm_id,
        include_categories=include_categories,
        group_high_volume=group_high_volume,
    )

    return timeline