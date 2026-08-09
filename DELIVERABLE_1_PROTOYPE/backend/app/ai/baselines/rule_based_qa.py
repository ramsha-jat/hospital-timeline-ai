# backend/app/ai/baselines/rule_based_qa.py
"""
Simple rule-based QA baseline for comparison with the LLM approach.

This is the baseline the evaluation protocol requires.
It uses keyword matching + direct SQL templates — no AI.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import Optional
from datetime import datetime

from app.db.models import (
    Admission, LabEvent, Prescription, DiagnosisICD, 
    ProcedureICD, ICUSTay, DLabItem, DICDDiagnosis
)
from app.timeline.schemas import SourceTrace


class RuleBasedQA:
    """
    Keyword-matching QA without any AI.
    Serves as the REQUIRED baseline for evaluation comparison.
    """
    
    # Pattern → query template mapping
    PATTERNS = {
        "abnormal_labs": {
            "keywords": ["abnormal", "lab", "labs", "flagged", "out of range"],
            "description": "Find lab results flagged as abnormal",
        },
        "medications": {
            "keywords": ["medication", "medications", "drug", "drugs", "prescribed", "rx"],
            "description": "List all medications prescribed",
        },
        "diagnoses": {
            "keywords": ["diagnosis", "diagnoses", "condition", "conditions", "icd"],
            "description": "List all ICD diagnoses",
        },
        "procedures": {
            "keywords": ["procedure", "procedures", "surgery", "operation"],
            "description": "List all ICD procedures",
        },
        "icu_stay": {
            "keywords": ["icu", "intensive care", "length of stay", "los"],
            "description": "ICU stay duration",
        },
        "potassium": {
            "keywords": ["potassium", "k+", "kal"],
            "description": "Potassium lab results",
        },
        "creatinine": {
            "keywords": ["creatinine", "cr", "renal", "kidney function"],
            "description": "Creatinine lab results",
        },
        "lactate": {
            "keywords": ["lactate", "lactic acid"],
            "description": "Lactate lab results",
        },
        "ventilator": {
            "keywords": ["ventilator", "vent", "mechanical ventilation", "intubat"],
            "description": "Ventilator-related observations",
        },
        "blood_pressure": {
            "keywords": ["blood pressure", "bp", "systolic", "diastolic", "map"],
            "description": "Blood pressure observations",
        },
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def match_query(self, question: str) -> Optional[str]:
        """Match a question to a query template via keywords."""
        question_lower = question.lower()
        best_match = None
        best_score = 0
        
        for query_id, pattern in self.PATTERNS.items():
            score = sum(
                1 for kw in pattern["keywords"] 
                if kw in question_lower
            )
            if score > best_score:
                best_score = score
                best_match = query_id
        
        return best_match if best_score > 0 else None
    
    async def answer(
        self, question: str, hadm_id: int
    ) -> dict:
        """Answer using rule-based matching (NO AI)."""
        
        query_id = self.match_query(question)
        
        if query_id is None:
            return {
                "answer": None,
                "method": "rule_based_baseline",
                "matched_template": None,
                "supporting_rows": 0,
                "evidence": [],
                "abstained": True,
                "reason": "no_keyword_match",
            }
        
        # Execute the matched template
        handler = getattr(self, f"_query_{query_id}", None)
        if handler is None:
            return {
                "answer": None,
                "method": "rule_based_baseline",
                "matched_template": query_id,
                "supporting_rows": 0,
                "evidence": [],
                "abstained": True,
                "reason": "no_handler",
            }
        
        result = await handler(hadm_id)
        result["method"] = "rule_based_baseline"
        result["matched_template"] = query_id
        
        return result
    
    async def _query_abnormal_labs(self, hadm_id: int) -> dict:
        result = await self.session.execute(
            select(LabEvent, DLabItem.label)
            .join(DLabItem, LabEvent.itemid == DLabItem.itemid, isouter=True)
            .where(and_(
                LabEvent.hadm_id == hadm_id,
                LabEvent.flag.isnot(None),
            ))
            .order_by(LabEvent.charttime)
        )
        
        rows = result.all()
        evidence = []
        for lab, label in rows:
            evidence.append({
                "data": {
                    "label": label,
                    "value": lab.valuenum,
                    "uom": lab.valueuom,
                    "flag": lab.flag,
                    "charttime": lab.charttime.isoformat() if lab.charttime else None,
                },
                "source_trace": SourceTrace(
                    table="labevents",
                    column="itemid,valuenum,flag,charttime",
                    row_id=lab.labevent_id,
                    charttime=lab.charttime,
                ).model_dump(mode="json"),
            })
        
        answer = f"Found {len(rows)} abnormal lab results." if rows else "No abnormal lab results found."
        
        return {
            "answer": answer,
            "supporting_rows": len(rows),
            "evidence": evidence,
            "abstained": len(rows) == 0,
        }
    
    async def _query_medications(self, hadm_id: int) -> dict:
        result = await self.session.execute(
            select(Prescription)
            .where(Prescription.hadm_id == hadm_id)
            .order_by(Prescription.starttime)
        )
        meds = result.scalars().all()
        
        evidence = []
        for med in meds:
            evidence.append({
                "data": {
                    "drug": med.drug,
                    "dose": f"{med.dose_val_rx or ''} {med.dose_unit_rx or ''}".strip(),
                    "route": med.route,
                    "starttime": med.starttime.isoformat() if med.starttime else None,
                },
                "source_trace": SourceTrace(
                    table="prescriptions",
                    column="drug,dose_val_rx,route,starttime",
                    row_id=med.prescription_id,
                    charttime=med.starttime,
                ).model_dump(mode="json"),
            })
        
        # Build answer text
        drug_names = [m.drug for m in meds if m.drug]
        unique_drugs = list(dict.fromkeys(drug_names))  # preserve order, dedupe
        
        if unique_drugs:
            answer = f"Patient was prescribed {len(unique_drugs)} distinct medications: {', '.join(unique_drugs[:20])}"
            if len(unique_drugs) > 20:
                answer += f" (and {len(unique_drugs) - 20} more)"
        else:
            answer = "No medication records found for this admission."
        
        return {
            "answer": answer,
            "supporting_rows": len(meds),
            "evidence": evidence,
            "abstained": len(meds) == 0,
        }
    
    async def _query_diagnoses(self, hadm_id: int) -> dict:
        result = await self.session.execute(
            select(DiagnosisICD, DICDDiagnosis.long_title)
            .join(DICDDiagnosis, 
                  and_(DiagnosisICD.icd_code == DICDDiagnosis.icd_code,
                       DiagnosisICD.icd_version == DICDDiagnosis.icd_version),
                  isouter=True)
            .where(DiagnosisICD.hadm_id == hadm_id)
            .order_by(DiagnosisICD.seq_num)
        )
        rows = result.all()
        
        evidence = []
        for dx, title in rows:
            evidence.append({
                "data": {
                    "icd_code": dx.icd_code,
                    "icd_version": dx.icd_version,
                    "long_title": title,
                    "seq_num": dx.seq_num,
                    "label_source": "d_icd_diagnoses_dictionary",
                },
                "source_trace": SourceTrace(
                    table="diagnoses_icd",
                    column="icd_code,icd_version,seq_num",
                    row_id=dx.row_id,
                    charttime=None,
                ).model_dump(mode="json"),
            })
        
        titles = [t for _, t in rows if t]
        answer = f"Found {len(rows)} diagnoses: {', '.join(titles[:10])}" if rows else "No diagnoses found."
        
        return {
            "answer": answer,
            "supporting_rows": len(rows),
            "evidence": evidence,
            "abstained": len(rows) == 0,
        }
    
    async def _query_icu_stay(self, hadm_id: int) -> dict:
        result = await self.session.execute(
            select(ICUSTay).where(ICUSTay.hadm_id == hadm_id)
        )
        stays = result.scalars().all()
        
        evidence = []
        for stay in stays:
            evidence.append({
                "data": {
                    "stay_id": stay.stay_id,
                    "first_careunit": stay.first_careunit,
                    "last_careunit": stay.last_careunit,
                    "intime": stay.intime.isoformat() if stay.intime else None,
                    "outtime": stay.outtime.isoformat() if stay.outtime else None,
                    "los_days": stay.los,
                },
                "source_trace": SourceTrace(
                    table="icustays",
                    column="first_careunit,last_careunit,intime,outtime,los",
                    row_id=stay.stay_id,
                    charttime=stay.intime,
                ).model_dump(mode="json"),
            })
        
        if stays:
            los_values = [s.los for s in stays if s.los is not None]
            total_los = sum(los_values) if los_values else 0
            answer = f"Patient had {len(stays)} ICU stay(s). Total ICU LOS: {total_los:.1f} days."
        else:
            answer = "No ICU stays recorded for this admission."
        
        return {
            "answer": answer,
            "supporting_rows": len(stays),
            "evidence": evidence,
            "abstained": len(stays) == 0,
        }
    
    # Additional handlers for potassium, creatinine, lactate, etc.
    # Follow the same pattern — keyword match → direct SQL → evidence
    
    async def _query_potassium(self, hadm_id: int) -> dict:
        # Itemid 50983 = Potassium (lab) in MIMIC-IV
        result = await self.session.execute(
            select(LabEvent)
            .where(and_(
                LabEvent.hadm_id == hadm_id,
                LabEvent.itemid == 50983,
            ))
            .order_by(LabEvent.charttime)
        )
        labs = result.scalars().all()
        
        evidence = []
        for lab in labs:
            evidence.append({
                "data": {
                    "value": lab.valuenum,
                    "uom": lab.valueuom,
                    "flag": lab.flag,
                    "charttime": lab.charttime.isoformat() if lab.charttime else None,
                },
                "source_trace": SourceTrace(
                    table="labevents",
                    column="itemid,valuenum,valueuom,flag,charttime",
                    row_id=lab.labevent_id,
                    charttime=lab.charttime,
                ).model_dump(mode="json"),
            })
        
        values = [l.valuenum for l in labs if l.valuenum is not None]
        if values:
            answer = (
                f"Potassium: {len(values)} measurements. "
                f"Range: [{min(values):.1f}, {max(values):.1f}] {labs[0].valueuom or ''}. "
                f"Mean: {sum(values)/len(values):.1f}."
            )
        else:
            answer = "No potassium measurements found."
        
        return {
            "answer": answer,
            "supporting_rows": len(labs),
            "evidence": evidence,
            "abstained": len(labs) == 0,
        }
    
    # _query_creatinine, _query_lactate, _query_ventilator, _query_blood_pressure
    # follow the same pattern with their respective itemids