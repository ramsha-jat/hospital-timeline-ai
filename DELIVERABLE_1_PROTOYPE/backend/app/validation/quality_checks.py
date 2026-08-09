# backend/app/validation/quality_checks.py
"""
Data quality validation for research credibility.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import datetime

from app.db.models import (
    Admission, LabEvent, Prescription, 
    ChartEvent, ICUSTay
)


class DataQualityChecker:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_admission(self, hadm_id: int) -> dict:
        """Run quality checks on a single admission."""
        issues = []
        warnings = []
        
        # 1. Temporal consistency
        adm = await self.session.execute(
            select(Admission).where(Admission.hadm_id == hadm_id)
        )
        admission = adm.scalar_one_or_none()
        if not admission:
            return {"valid": False, "issues": ["Admission not found"]}
        
        if admission.dischtime and admission.dischtime < admission.admittime:
            issues.append("dischtime < admittime@me")
        
        if admission.deathtime and admission.dischtime and admission.deathtime > admission.dischtime:
            warnings.append("deathtime > dischtime (may be expected for outpatient death)")
        
        # 2. Missing critical timestamps
        lab_count = await self.session.execute(
            select(func.count(LabEvent.labevent_id))
            .where(and_(
                LabEvent.hadm_id == hadm_id,
                LabEvent.charttime.is_(None)
            ))
        )
        labs_without_time = lab_count.scalar()
        if labs_without_time > 0:
            issues.append(f"{labs_without_time} lab events missing charttime")
        
        # 3. ICU stay consistency
        icu_stays = await self.session.execute(
            select(ICUSTay).where(ICUSTay.hadm_id == hadm_id)
        )
        for stay in icu_stays.scalars().all():
            if stay.intime < admission.admittime:
                warnings.append(f"ICU stay {stay.stay_id} intime before admission")
            if admission.dischtime and stay.outtime and stay.outtime > admission.dischtime:
                warnings.append(f"ICU stay {stay.stay_id} outtime after discharge")
        
        # 4. Lab value ranges
        extreme_labs = await self.session.execute(
            select(func.count(LabEvent.labevent_id))
            .where(and_(
                LabEvent.hadm_id == hadm_id,
                LabEvent.valuenum < 0,
            ))
        )
        neg_labs = extreme_labs.scalar()
        if neg_labs > 0:
            warnings.append(f"{neg_labs} lab events with negative numeric values")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "hadm_id": hadm_id,
            "disclaimer": "Data quality checks are for research data validation, not clinical safety assessment",
        }
