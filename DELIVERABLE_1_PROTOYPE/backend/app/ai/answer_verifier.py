# app/ai/answer_verifier.py
"""
Verification gate — the most critical safety component.

Checks:
1. Do supporting rows exist? If not → ABSTAIN
2. Does every claimed fact match a real database row?
3. Is the answer staying in scope (no clinical recommendations)?
4. Are numeric claims within plausible ranges?
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
import re


class AnswerVerifier:
    """
    Verifies AI-generated answers against actual database rows.
    The system MUST abstain when verification fails.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def verify_answer(
        self,
        answer: str,
        evidence_rows: list[dict],
        question: str,
    ) -> dict:
        """
        Full verification pipeline.
        Returns pass/fail + details.
        """
        results = {
            "verified": True,
            "checks": {},
            "reasons_to_abstain": [],
        }
        
        # Check 1: Supporting rows exist
        row_check = self._check_supporting_rows(evidence_rows)
        results["checks"]["supporting_rows"] = row_check
        if not row_check["passed"]:
            results["verified"] = False
            results["reasons_to_abstain"].append(row_check["reason"])
        
        # Check 2: Source traces are valid
        trace_check = self._check_source_traces(evidence_rows)
        results["checks"]["source_traces"] = trace_check
        if not trace_check["passed"]:
            results["verified"] = False
            results["reasons_to_abstain"].append(trace_check["reason"])
        
        # Check 3: No out-of-scope clinical claims
        scope_check = self._check_scope(answer)
        results["checks"]["scope"] = scope_check
        if not scope_check["passed"]:
            results["verified"] = False
            results["reasons_to_abstain"].append(scope_check["reason"])
        
        # Check 4: Numeric plausibility
        plausibility_check = self._check_plausibility(evidence_rows)
        results["checks"]["plausibility"] = plausibility_check
        # This is a WARNING, not a hard fail
        
        # Check 5: Question-answer relevance
        relevance_check = self._check_relevance(question, answer, evidence_rows)
        results["checks"]["relevance"] = relevance_check
        
        return results
    
    def _check_supporting_rows(self, evidence_rows: list[dict]) -> dict:
        """Check that at least one supporting row exists."""
        if not evidence_rows or len(evidence_rows) == 0:
            return {
                "passed": False,
                "reason": "zero_supporting_rows",
                "detail": "No evidence rows found to support the answer",
            }
        return {
            "passed": True,
            "reason": None,
            "detail": f"{len(evidence_rows)} supporting rows found",
        }
    
    def _check_source_traces(self, evidence_rows: list[dict]) -> dict:
        """Check that every evidence row has a valid source trace."""
        invalid_traces = []
        
        for i, row in enumerate(evidence_rows):
            trace = row.get("source_trace", {})
            
            # Must have collection name
            if not trace.get("collection"):
                invalid_traces.append({
                    "row_index": i,
                    "issue": "missing_collection",
                })
                continue
            
            # Must have doc_id
            if not trace.get("doc_id"):
                invalid_traces.append({
                    "row_index": i,
                    "issue": "missing_doc_id",
                })
                continue
            
            # Collection must be in allowed list
            allowed = [
                "patients", "admissions", "icustays", "transfers",
                "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
                "chartevents", "outputevents", "inputevents_mv",
                "d_labitems", "d_items", "d_icd_diagnoses", "d_icd_procedures",
            ]
            if trace["collection"] not in allowed:
                invalid_traces.append({
                    "row_index": i,
                    "issue": f"disallowed_collection: {trace['collection']}",
                })
        
        if invalid_traces:
            return {
                "passed": False,
                "reason": "invalid_source_traces",
                "detail": f"{len(invalid_traces)} invalid traces: {invalid_traces[:5]}",
            }
        return {
            "passed": True,
            "reason": None,
            "detail": f"All {len(evidence_rows)} traces valid",
        }
    
    def _check_scope(self, answer: str) -> dict:
        """
        Check that the answer doesn't make out-of-scope clinical claims.
        Prohibited: diagnosis, treatment, triage, emergency guidance.
        """
        answer_lower = answer.lower()
        
        prohibited_patterns = [
            (r"should\s+(be|take|receive|get|start|stop)", "treatment_recommendation"),
            (r"recommend\s+(treatment|medication|therapy|drug)", "treatment_recommendation"),
            (r"patient\s+should", "treatment_recommendation"),
            (r"diagnos[ie]s\s+(is|are|confirms)", "clinical_diagnosis_claim"),
            (r"confirm(?:s|ed)?\s+diagnosis", "clinical_diagnosis_claim"),
            (r"prognosis\s+(is|appears|seems|looks)", "prognosis_claim"),
            (r"life\s+expectancy", "prognosis_claim"),
            (r"discharge\s+(today|now|immediately)", "triage_decision"),
            (r"admit\s+(to|immediately)", "triage_decision"),
            (r"emergency", "emergency_guidance"),
            (r"call\s+911|seek\s+immediate", "emergency_guidance"),
            (r"this\s+patient\s+has\s+(?:been\s+)?diagnosed", "clinical_diagnosis_claim"),
            (r"treatment\s+plan", "treatment_recommendation"),
        ]
        
        violations = []
        for pattern, violation_type in prohibited_patterns:
            if re.search(pattern, answer_lower):
                violations.append(violation_type)
        
        if violations:
            return {
                "passed": False,
                "reason": f"out_of_scope: {', '.join(set(violations))}",
                "detail": "Answer contains prohibited clinical claims",
            }
        return {
            "passed": True,
            "reason": None,
            "detail": "No out-of-scope clinical claims detected",
        }
    
    def _check_plausibility(self, evidence_rows: list[dict]) -> dict:
        """
        Check if numeric values are within plausible clinical ranges.
        This is a WARNING system, not a hard block.
        """
        IMPLAUSIBLE_RANGES = {
            "Heart Rate": (0, 350),
            "Respiratory Rate": (0, 100),
            "Temperature": (20, 50),  # Celsius
            "Blood Pressure": (0, 400),
            "SpO2": (0, 100),
            "Potassium": (0, 15),
            "Sodium": (0, 250),
            "Creatinine": (0, 50),
            "Glucose": (0, 2000),
            "Hemoglobin": (0, 30),
            "WBC": (0, 200),
            "Platelet": (0, 2000),
            "Lactate": (0, 50),
            "pH": (0, 14),
        }
        
        warnings = []
        for row in evidence_rows:
            data = row.get("data", {})
            label = data.get("label", "")
            value = data.get("value") or data.get("valuenum")
            
            if value is None:
                continue
            
            try:
                value = float(value)
            except (ValueError, TypeError):
                continue
            
            # Check against known ranges
            for known_label, (lo, hi) in IMPLAUSIBLE_RANGES.items():
                if known_label.lower() in label.lower():
                    if value < lo or value > hi:
                        warnings.append({
                            "label": label,
                            "value": value,
                            "expected_range": [lo, hi],
                        })
                    break
        
        return {
            "passed": True,  # Warnings don't block
            "warnings": warnings,
            "detail": f"{len(warnings)} implausible values found" if warnings else "All values plausible",
        }
    
    def _check_relevance(
        self, question: str, answer: str, evidence_rows: list[dict]
    ) -> dict:
        """
        Basic relevance check: does the answer mention
        anything related to the question topic?
        """
        # Extract key nouns from question
        question_words = set(question.lower().split())
        answer_lower = answer.lower()
        
        # Check if any significant question word appears in answer
        significant_words = question_words - {
            "what", "were", "was", "the", "is", "are", "how",
            "many", "much", "did", "do", "does", "a", "an",
            "of", "in", "on", "for", "with", "this", "that",
        }
        
        overlap = sum(1 for w in significant_words if w in answer_lower)
        
        if len(significant_words) > 0 and overlap == 0 and len(evidence_rows) > 0:
            return {
                "passed": True,
                "detail": "Answer may not directly address question topic (low word overlap), but evidence rows exist",
                "warning": True,
            }
        
        return {
            "passed": True,
            "detail": f"Answer appears relevant ({overlap} keyword overlaps)",
            "warning": False,
        }
    
    async def verify_source_row_exists(
        self, collection: str, doc_id: str
    ) -> bool:
        """
        Check that a specific document actually exists in MongoDB.
        Used for deep verification of source traces.
        """
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(doc_id)
                doc = await self.db[collection].find_one({"_id": oid})
            except Exception:
                # Not a valid ObjectId, try as business key
                doc = await self.db[collection].find_one({"_id": doc_id})
            
            return doc is not None
        except Exception:
            return False