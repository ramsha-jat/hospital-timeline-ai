"""
Prevent data leakage between train/test splits.
Critical for credible research.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.db.models import Patient, Admission


class LeakageDetector:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_patient_overlap(
        self, 
        train_hadm_ids: list[int], 
        test_hadm_ids: list[int]
    ) -> dict:
        """Check if any patient appears in both train and test sets."""
        
        # Get subject_ids for both sets
        train_subjects = await self.session.execute(
            select(Admission.subject_id)
            .where(Admission.hadm_id.in_(train_hadm_ids))
            .distinct()
        )
        test_subjects = await self.session.execute(
            select(Admission.subject_id)
            .where(Admission.hadm_id.in_(test_hadm_ids))
            .distinct()
        )
        
        train_set = set(train_subjects.scalars().all())
        test_set = set(test_subjects.scalars().all())
        overlap = train_set & test_set
        
        return {
            "leakage_detected": len(overlap) > 0,
            "overlapping_subject_ids": list(overlap),
            "train_unique_subjects": len(train_set),
            "test_unique_subjects": len(test_set),
            "recommendation": (
                "Split by subject_id, not hadm_id, to prevent patient-level leakage"
                if overlap else "No leakage detected"
            ),
        }
    
    async def check_temporal_leakage(
        self,
        train_hadm_ids: list[int],
        test_hadm_ids: list[int]
    ) -> dict:
        """Check if test admissions occur before train admissions (temporal leakage)."""
        
        train_times = await self.session.execute(
            select(Admission.admittime)
            .where(Admission.hadm_id.in_(train_hadm_ids))
        )
        test_times = await self.session.execute(
            select(Admission.admittime)
            .where(Admission.hadm_id.in_(test_hadm_ids))
        )
        
        train_admit_times = [t for t in train_times.scalars().all()]
        test_admit_times = [t for t in test_times.scalars().all()]
        
        if not train_admit_times or not test_admit_times:
            return {"leakage_detected": False, "reason": "insufficient_data"}
        
        min_test = min(test_admit_times)
        max_train = max(train_admit_times)
        
        temporal_leak = min_test < max_train
        
        return {
            "leakage_detected": temporal_leak,
            "min_test_admittime": min_test.isoformat(),
            "max_train_admittime": max_train.isoformat(),
            "recommendation": (
                "Use a temporal cutoff to ensure all test admissions occur after all train admissions"
                if temporal_leak else "No temporal leakage detected"
            ),
        }