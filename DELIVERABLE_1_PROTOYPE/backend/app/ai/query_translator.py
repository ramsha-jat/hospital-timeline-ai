# app/ai/query_translator.py — FULL FILE (API-MINIMIZED)
"""
API-MINIMIZED Query Translator.

Default: Rule-based (ZERO API calls)
Optional: Gemini only if GEMINI_API_KEY is set AND rule fails
Answer generation: Always from code (never from API)
"""
import json
from typing import Optional
from datetime import datetime
from collections import Counter

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.timeline.schemas import SourceTrace

settings = get_settings()


# ═══════════════════════════════════════════════════════
# RULE ENGINE — Handles 95% of questions, ZERO API
# ═══════════════════════════════════════════════════════

RULES = [
    {
        "id": "abnormal_labs",
        "keywords": ["abnormal", "flagged", "out of range", "abnorm"],
        "collection": "labevents",
        "base_filter": {"flag": {"$ne": None}},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "all_labs",
        "keywords": ["lab", "laboratory", "test", "tests", "result", "results", "blood work", "bloodwork"],
        "collection": "labevents",
        "base_filter": {},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "lab_labels",
    },
    {
        "id": "medications",
        "keywords": ["medication", "medications", "drug", "drugs", "prescribed", "medicine", "rx", "pharmacy"],
        "collection": "prescriptions",
        "base_filter": {},
        "sort": [("starttime", 1)],
        "limit": 200,
        "enrich": None,
    },
    {
        "id": "diagnoses",
        "keywords": ["diagnosis", "diagnoses", "condition", "conditions", "icd", "disease"],
        "collection": "diagnoses_icd",
        "base_filter": {},
        "sort": [("seq_num", 1)],
        "limit": 100,
        "enrich": "icd_diagnosis_labels",
    },
    {
        "id": "procedures",
        "keywords": ["procedure", "procedures", "surgery", "operation", "surgical"],
        "collection": "procedures_icd",
        "base_filter": {},
        "sort": [("seq_num", 1)],
        "limit": 50,
        "enrich": "icd_procedure_labels",
    },
    {
        "id": "icu_stay",
        "keywords": ["icu", "intensive", "length of stay", "los", "icu stay", "critical care"],
        "collection": "icustays",
        "base_filter": {},
        "sort": [("intime", 1)],
        "limit": 10,
        "enrich": None,
    },
    {
        "id": "transfers",
        "keywords": ["transfer", "transfers", "ward", "unit", "moved", "bed"],
        "collection": "transfers",
        "base_filter": {},
        "sort": [("intime", 1)],
        "limit": 50,
        "enrich": None,
    },
    {
        "id": "admissions_info",
        "keywords": ["admission", "admit", "admitted", "discharge", "discharged", "encounter", "hospital stay"],
        "collection": "admissions",
        "base_filter": {},
        "sort": [],
        "limit": 5,
        "enrich": None,
    },
    {
        "id": "potassium",
        "keywords": ["potassium", "k+", "kal"],
        "collection": "labevents",
        "base_filter": {"itemid": 50983},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "creatinine",
        "keywords": ["creatinine", "cr ", "renal function", "kidney function"],
        "collection": "labevents",
        "base_filter": {"itemid": 50912},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "sodium",
        "keywords": ["sodium", "na+"],
        "collection": "labevents",
        "base_filter": {"itemid": 50983},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "glucose",
        "keywords": ["glucose", "blood sugar", "bg", "blood glucose"],
        "collection": "labevents",
        "base_filter": {"itemid": 50909},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "hemoglobin",
        "keywords": ["hemoglobin", "hb", "hgb"],
        "collection": "labevents",
        "base_filter": {"itemid": 51221},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "wbc",
        "keywords": ["wbc", "white blood", "white cell", "leukocyte"],
        "collection": "labevents",
        "base_filter": {"itemid": 51301},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "lactate",
        "keywords": ["lactate", "lactic acid"],
        "collection": "labevents",
        "base_filter": {"itemid": 50813},
        "sort": [("charttime", 1)],
        "limit": 100,
        "enrich": "lab_labels",
    },
    {
        "id": "bp_chart",
        "keywords": ["blood pressure", "bp", "systolic", "diastolic", "map", "mean arterial"],
        "collection": "chartevents",
        "base_filter": {"itemid": {"$in": [220050, 220051, 220052, 220179]}},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "chart_labels",
    },
    {
        "id": "heart_rate",
        "keywords": ["heart rate", "hr", "pulse", "heartbeat"],
        "collection": "chartevents",
        "base_filter": {"itemid": 220045},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "chart_labels",
    },
    {
        "id": "spo2",
        "keywords": ["spo2", "oxygen", "saturation", "pulse ox"],
        "collection": "chartevents",
        "base_filter": {"itemid": 220277},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "chart_labels",
    },
    {
        "id": "ventilator",
        "keywords": ["ventilator", "vent", "mechanical ventilation", "intubat", "resp rate"],
        "collection": "chartevents",
        "base_filter": {"itemid": {"$in": [220210, 224700, 223849]}},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "chart_labels",
    },
    {
        "id": "outputs",
        "keywords": ["output", "outputs", "urine", "urine output", "fluid output", "foley"],
        "collection": "outputevents",
        "base_filter": {},
        "sort": [("charttime", 1)],
        "limit": 200,
        "enrich": "chart_labels",
    },
]


def match_rule(question: str) -> Optional[dict]:
    """Match question to best rule. ZERO API call."""
    q = question.lower().strip()
    best_rule = None
    best_score = 0

    for rule in RULES:
        score = sum(2 if kw in q else 0 for kw in rule["keywords"])
        # Bonus for exact match
        for kw in rule["keywords"]:
            if q == kw:
                score += 5
        if score > best_score:
            best_score = score
            best_rule = rule

    return best_rule if best_score > 0 else None


# ═══════════════════════════════════════════════════════
# ANSWER BUILDERS — Code-generated, ZERO API
# ═══════════════════════════════════════════════════════
def build_answer(question: str, rule_id: str, rows: list[dict]) -> str:
    """
    Smart answer builder — writes human-readable answers from code.
    NO LLM needed. NO API needed. NO extra space.
    """
    n = len(rows)
    if n == 0:
        return f"No {rule_id.replace('_', ' ')} data found for this admission."

    builder = AnswerBuilder(question, rule_id, rows)
    return builder.build()


class AnswerBuilder:
    """Builds beautiful, human-readable answers from structured data."""
    
    def __init__(self, question: str, rule_id: str, rows: list[dict]):
        self.question = question
        self.rule_id = rule_id
        self.rows = rows
        self.n = len(rows)
        self.lines: list[str] = []
    
    def build(self) -> str:
        dispatch = {
            "abnormal_labs": self._abnormal_labs,
            "all_labs": self._all_labs,
            "medications": self._medications,
            "diagnoses": self._diagnoses,
            "procedures": self._procedures,
            "icu_stay": self._icu_stay,
            "transfers": self._transfers,
            "admissions_info": self._admissions,
            "potassium": self._specific_lab,
            "creatinine": self._specific_lab,
            "sodium": self._specific_lab,
            "glucose": self._specific_lab,
            "hemoglobin": self._specific_lab,
            "wbc": self._specific_lab,
            "lactate": self._specific_lab,
            "bp_chart": self._vitals,
            "heart_rate": self._vitals,
            "spo2": self._vitals,
            "ventilator": self._vitals,
            "outputs": self._outputs,
        }
        
        handler = dispatch.get(self.rule_id, self._generic)
        handler()
        
        # Always add footer
        self.lines.append("")
        self.lines.append("━" * 40)
        self.lines.append("📎 Source: MIMIC-IV structured data | Research use only")
        
        return "\n".join(self.lines)
    
    def _header(self, icon: str, text: str):
        self.lines.append(f"{icon}  {text}")
        self.lines.append("")
    
    def _stat_box(self, label: str, value: str, unit: str = "", flag: str = ""):
        flag_str = f"  [{flag}]" if flag else ""
        self.lines.append(f"  ├─ {label}: {value} {unit}{flag_str}")
    
    def _abnormal_labs(self):
        self._header("🔬", f"Abnormal Lab Results ({self.n} found)")
        
        # Group by lab name
        by_name: dict[str, list] = {}
        for r in self.rows:
            name = r.get("label", f"Item {r.get('itemid', '?')}")
            by_name.setdefault(name, []).append(r)
        
        for name, items in sorted(by_name.items(), key=lambda x: -len(x[1])):
            values = [r.get("valuenum") for r in items if r.get("valuenum") is not None]
            uom = items[0].get("valueuom", "")
            
            self.lines.append(f"  ⚠️  {name}")
            if values:
                self.lines.append(f"      Values: {min(values):.1f} – {max(values):.1f} {uom}")
                self.lines.append(f"      Occurrences: {len(values)} abnormal reading(s)")
            # Show first 3 timestamps
            for r in items[:3]:
                t = str(r.get("charttime", ""))[:16]
                v = r.get("valuenum", "?")
                f = r.get("flag", "")
                self.lines.append(f"      • {t}  →  {v} {uom}  ({f})")
            if len(items) > 3:
                self.lines.append(f"      ... +{len(items)-3} more")
            self.lines.append("")
    
    def _all_labs(self):
        self._header("🔬", f"Laboratory Results ({self.n} tests)")
        
        # Group by lab name
        by_name: dict[str, list] = {}
        for r in self.rows:
            name = r.get("label", f"Item {r.get('itemid', '?')}")
            by_name.setdefault(name, []).append(r)
        
        for name, items in sorted(by_name.items(), key=lambda x: -len(x[1])):
            values = [r.get("valuenum") for r in items if r.get("valuenum") is not None]
            uom = items[0].get("valueuom", "")
            abnormal = [r for r in items if r.get("flag")]
            
            self.lines.append(f"  📊  {name}")
            if values:
                avg = sum(values) / len(values)
                self.lines.append(f"      Range: {min(values):.1f} – {max(values):.1f} {uom}")
                self.lines.append(f"      Mean:  {avg:.1f} {uom}")
                self.lines.append(f"      Count: {len(values)} measurement(s)")
                if abnormal:
                    self.lines.append(f"      ⚠️  {len(abnormal)} abnormal")
            self.lines.append("")
            
            if len(by_name) > 10:
                self.lines.append(f"  ... and {len(by_name) - 10} more lab types")
                break
    
    def _specific_lab(self):
        lab_name = self.rule_id.replace("_", " ").title()
        self._header("🔬", f"{lab_name} Trend ({self.n} measurements)")
        
        values = [r.get("valuenum") for r in self.rows if r.get("valuenum") is not None]
        uom = self.rows[0].get("valueuom", "") if self.rows else ""
        abnormal = [r for r in self.rows if r.get("flag")]
        
        if values:
            avg = sum(values) / len(values)
            lo, hi = min(values), max(values)
            
            # Stats summary
            self.lines.append("  ┌─────────────────────────────────┐")
            self.lines.append(f"  │  Low:    {lo:>8.1f} {uom:<8}      │")
            self.lines.append(f"  │  Mean:   {avg:>8.1f} {uom:<8}      │")
            self.lines.append(f"  │  High:   {hi:>8.1f} {uom:<8}      │")
            self.lines.append(f"  │  Count:  {len(values):>8} reading(s)   │")
            if abnormal:
                self.lines.append(f"  │  ⚠️ Abnormal: {len(abnormal):>4}            │")
            self.lines.append("  └─────────────────────────────────┘")
            self.lines.append("")
            
            # Trend (first 8 + last 3)
            self.lines.append("  Timeline:")
            shown = list(range(min(8, len(self.rows)))) + list(range(max(8, len(self.rows)-3), len(self.rows)))
            shown = sorted(set(shown))
            for i in shown:
                r = self.rows[i]
                v = r.get("valuenum", "?")
                t = str(r.get("charttime", ""))[:16]
                flag = " ⚠️" if r.get("flag") else ""
                bar = self._sparkline(v, lo, hi) if isinstance(v, (int, float)) else ""
                self.lines.append(f"    {t}  {v:>6} {uom}{flag}  {bar}")
            if len(self.rows) > 11:
                self.lines.append(f"    ... ({len(self.rows) - 11} readings omitted)")
    
    def _vitals(self):
        vital_name = self.rule_id.replace("_", " ").title()
        self._header("💓", f"{vital_name} Observations ({self.n} readings)")
        
        values = [r.get("valuenum") for r in self.rows if r.get("valuenum") is not None]
        uom = self.rows[0].get("valueuom", "") if self.rows else ""
        
        if values:
            avg = sum(values) / len(values)
            lo, hi = min(values), max(values)
            
            self.lines.append("  ┌─────────────────────────────────┐")
            self.lines.append(f"  │  Low:    {lo:>8.0f} {uom:<8}      │")
            self.lines.append(f"  │  Mean:   {avg:>8.1f} {uom:<8}      │")
            self.lines.append(f"  │  High:   {hi:>8.0f} {uom:<8}      │")
            self.lines.append("  └─────────────────────────────────┘")
            self.lines.append("")
            
            # Most recent 5
            self.lines.append("  Most recent:")
            for r in self.rows[-5:]:
                v = r.get("valuenum", "?")
                t = str(r.get("charttime", ""))[:16]
                w = " ⚠️" if r.get("warning") else ""
                self.lines.append(f"    {t}  →  {v} {uom}{w}")
    
    def _medications(self):
        self._header("💊", f"Medications ({self.n} prescriptions)")
        
        # Group by drug name
        by_drug: dict[str, list] = {}
        for r in self.rows:
            drug = r.get("drug", "Unknown")
            by_drug.setdefault(drug, []).append(r)
        
        unique_count = len(by_drug)
        self.lines.append(f"  {unique_count} distinct medication(s) prescribed:")
        self.lines.append("")
        
        # Sort by frequency
        sorted_drugs = sorted(by_drug.items(), key=lambda x: -len(x[1]))
        
        for drug, items in sorted_drugs:
            count = len(items)
            route = items[0].get("route", "")
            dose = items[0].get("dose_val_rx", "")
            
            # Compact format
            parts = [f"  •  {drug}"]
            if dose:
                parts.append(f" {dose}")
            if route:
                parts.append(f" ({route})")
            if count > 1:
                parts.append(f"  ×{count}")
            
            self.lines.append("".join(parts))
        
        if unique_count > 25:
            self.lines.append(f"  ... +{unique_count - 25} more")
    
    def _diagnoses(self):
        self._header("📋", f"Diagnoses ({self.n} ICD codes)")
        self.lines.append("  Ranked by clinical priority (seq_num):")
        self.lines.append("")
        
        for r in self.rows[:25]:
            seq = r.get("seq_num", "?")
            code = r.get("icd_code", "")
            version = r.get("icd_version", "")
            title = r.get("long_title", f"ICD-{version} {code}")
            
            # Primary vs secondary
            marker = "🔴" if seq == 1 else "🟡" if seq and seq <= 3 else "⚪"
            self.lines.append(f"  {marker}  #{seq}  {title}")
            self.lines.append(f"        ICD-{version}: {code}")
        
        if self.n > 25:
            self.lines.append(f"  ... +{self.n - 25} more codes")
        
        self.lines.append("")
        self.lines.append("  ⚠️  These are ICD billing codes, not clinician-authored diagnoses.")
    
    def _procedures(self):
        self._header("🔧", f"Procedures ({self.n} ICD codes)")
        self.lines.append("")
        
        for r in self.rows[:15]:
            code = r.get("icd_code", "")
            version = r.get("icd_version", "")
            title = r.get("long_title", f"ICD-{version} {code}")
            self.lines.append(f"  •  {title}")
            self.lines.append(f"     ICD-{version}: {code}")
        
        if self.n > 15:
            self.lines.append(f"  ... +{self.n - 15} more")
    
    def _icu_stay(self):
        self._header("🚑", f"ICU Stay(s) — {self.n} stay(s)")
        self.lines.append("")
        
        for r in self.rows:
            unit_in = r.get("first_careunit", "?")
            unit_out = r.get("last_careunit", "?")
            los = r.get("los", 0)
            t_in = str(r.get("intime", "?"))[:16]
            t_out = str(r.get("outtime", "?"))[:16]
            stay_id = r.get("stay_id", "?")
            
            self.lines.append(f"  Stay #{stay_id}")
            self.lines.append(f"  ┌────────────────────────────────────┐")
            self.lines.append(f"  │  Unit:      {unit_in} → {unit_out}")
            self.lines.append(f"  │  Admitted:  {t_in}")
            self.lines.append(f"  │  Discharged:{t_out}")
            self.lines.append(f"  │  Duration:  {los:.1f} days ({los*24:.0f} hours)")
            self.lines.append(f"  └────────────────────────────────────┘")
            self.lines.append("")
    
    def _transfers(self):
        self._header("↔️", f"Ward Transfers ({self.n})")
        self.lines.append("")
        
        for r in self.rows[:20]:
            event = r.get("eventtype", "?")
            unit = r.get("careunit", "?")
            t = str(r.get("intime", "?"))[:16]
            self.lines.append(f"  •  {t}  {event} → {unit}")
        
        if self.n > 20:
            self.lines.append(f"  ... +{self.n - 20} more")
    
    def _admissions(self):
        self._header("🏥", f"Admission Details")
        self.lines.append("")
        
        for r in self.rows:
            self.lines.append(f"  Type:       {r.get('admission_type', '?')}")
            self.lines.append(f"  From:       {r.get('admission_location', '?')}")
            self.lines.append(f"  Discharge:  {r.get('discharge_location', '?')}")
            self.lines.append(f"  Admitted:   {str(r.get('admittime', '?'))[:16]}")
            self.lines.append(f"  Discharged: {str(r.get('dischtime', '?'))[:16]}")
            
            # Calculate LOS
            try:
                t_in = datetime.fromisoformat(str(r.get('admittime', '')))
                t_out = datetime.fromisoformat(str(r.get('dischtime', '')))
                los = (t_out - t_in).total_seconds() / 86400
                self.lines.append(f"  Duration:   {los:.1f} days")
            except:
                pass
            
            self.lines.append(f"  Insurance:  {r.get('insurance', '?')}")
            self.lines.append(f"  Race:       {r.get('race', '?')}")
            if r.get('hospital_expire_flag'):
                self.lines.append(f"  ⚠️  Expired during hospitalization")
    
    def _outputs(self):
        self._header("📉", f"Output Events ({self.n})")
        self.lines.append("")
        
        values = [r.get("value") for r in self.rows if r.get("value") is not None]
        if values:
            total = sum(values)
            self.lines.append(f"  Total output: {total:.0f} mL")
            self.lines.append(f"  Readings: {len(values)}")
            self.lines.append(f"  Average per reading: {total/len(values):.1f} mL")
        self.lines.append("")
        
        for r in self.rows[-10:]:
            v = r.get("value", "?")
            uom = r.get("valueuom", "")
            t = str(r.get("charttime", ""))[:16]
            self.lines.append(f"  •  {t}  →  {v} {uom}")
    
    def _generic(self):
        self._header("📊", f"Results ({self.n} records)")
        for r in self.rows[:10]:
            self.lines.append(f"  •  {r}")
    
    def _sparkline(self, value: float, lo: float, hi: float, width: int = 10) -> str:
        """Mini bar chart for trends."""
        if hi == lo:
            return "█" * width
        ratio = (value - lo) / (hi - lo)
        filled = int(ratio * width)
        return "█" * filled + "░" * (width - filled)
# ═══════════════════════════════════════════════════════
# MAIN CLASS
# ═══════════════════════════════════════════════════════

class QueryTranslator:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def ask(
        self,
        question: str,
        hadm_id: Optional[int] = None,
        subject_id: Optional[int] = None,
    ) -> dict:
        """
        Main entry point.
        1. Try rule-based (ZERO API)
        2. Only try Gemini if rule fails AND key is set
        """

        # TRY 1: Rule-based (always, no API)
        rule = match_rule(question)
        if rule:
            print(f"  ✓ Rule matched: {rule['id']} (no API call)")
            result = await self._execute_rule(rule, hadm_id, question)
            if result:
                return result

        # TRY 2: Gemini (only if API key exists)
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 10:
            print(f"  → No rule match. Trying Gemini...")
            result = await self._try_gemini(question, hadm_id)
            if result:
                return result

        # Both failed / no match
        return {
            "answer": f"I couldn't find a matching query for \"{question}\". Try asking about: labs, medications, diagnoses, ICU stay, procedures, transfers, vitals (heart rate, blood pressure, SpO2), or specific lab tests (potassium, creatinine, glucose, etc.).",
            "query": {"method": "no_match", "available_rules": [r["id"] for r in RULES]},
            "supporting_rows": 0,
            "evidence": [],
            "refused": True,
            "error": None,
        }

    async def _execute_rule(
        self, rule: dict, hadm_id: Optional[int], question: str
    ) -> Optional[dict]:
        """Execute a matched rule. ZERO API call."""
        try:
            collection_name = rule["collection"]
            filter_doc = dict(rule["base_filter"])
            if hadm_id:
                filter_doc["hadm_id"] = hadm_id

            collection = self.db[collection_name]
            cursor = collection.find(filter_doc)

            # Sort
            for sort_field, sort_dir in rule.get("sort", []):
                cursor = cursor.sort(sort_field, sort_dir)

            cursor = cursor.limit(rule.get("limit", 100))

            rows = []
            async for doc in cursor:
                serialized = self._serialize(doc)
                rows.append(serialized)

            # Enrich with dictionary labels
            enrich_type = rule.get("enrich")
            if enrich_type and rows:
                rows = await self._enrich(rows, enrich_type)

            # Build answer from CODE (not API)
            answer = build_answer(question, rule["id"], rows)

            # Attach evidence
            evidence = self._attach_evidence(rows, collection_name)

            return {
                "answer": answer,
                "query": {
                    "method": "rule_based",
                    "rule_id": rule["id"],
                    "collection": collection_name,
                    "filter": {k: str(v) for k, v in filter_doc.items()},
                },
                "supporting_rows": len(rows),
                "evidence": evidence[:100],
                "refused": False,
                "error": None,
            }

        except Exception as e:
            print(f"  ✗ Rule execution error: {e}")
            return None

    async def _enrich(self, rows: list[dict], enrich_type: str) -> list[dict]:
        """Add human-readable labels from dictionary tables."""
        if enrich_type == "lab_labels":
            itemids = set(r.get("itemid") for r in rows if r.get("itemid"))
            label_map = {}
            async for doc in self.db.d_labitems.find({"itemid": {"$in": list(itemids)}}):
                label_map[doc["itemid"]] = doc.get("label", "")
            for r in rows:
                r["label"] = label_map.get(r.get("itemid"), f"Lab {r.get('itemid')}")

        elif enrich_type == "chart_labels":
            itemids = set(r.get("itemid") for r in rows if r.get("itemid"))
            label_map = {}
            async for doc in self.db.d_items.find({"itemid": {"$in": list(itemids)}}):
                label_map[doc["itemid"]] = doc.get("label", "")
            for r in rows:
                r["label"] = label_map.get(r.get("itemid"), f"Item {r.get('itemid')}")

        elif enrich_type == "icd_diagnosis_labels":
            for r in rows:
                icd_code = r.get("icd_code")
                icd_version = r.get("icd_version")
                if icd_code and icd_version:
                    lookup = await self.db.d_icd_diagnoses.find_one({
                        "icd_code": icd_code,
                        "icd_version": icd_version,
                    })
                    r["long_title"] = lookup.get("long_title", "") if lookup else ""

        elif enrich_type == "icd_procedure_labels":
            for r in rows:
                icd_code = r.get("icd_code")
                icd_version = r.get("icd_version")
                if icd_code and icd_version:
                    lookup = await self.db.d_icd_procedures.find_one({
                        "icd_code": icd_code,
                        "icd_version": icd_version,
                    })
                    r["long_title"] = lookup.get("long_title", "") if lookup else ""

        return rows

    async def _try_gemini(
        self, question: str, hadm_id: Optional[int]
    ) -> Optional[dict]:
        """Try Gemini ONLY when no rule matches. 1 API call only."""
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            schema = """Generate a MongoDB query as JSON for MIMIC-IV data.
Collections: patients, admissions, icustays, transfers, labevents, prescriptions, diagnoses_icd, procedures_icd, chartevents, outputevents, d_labitems, d_items.
Return: {"collection":"...", "filter":{...}, "sort":[[field,1]], "limit":50}
Always filter by hadm_id. JSON only, no markdown."""

            prompt = f"{schema}\n\nQuestion: {question}\nhadm_id = {hadm_id}"

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=0.0),
            )

            raw = response.text.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].strip() == "```": lines = lines[:-1]
                raw = "\n".join(lines).strip()
            if raw.startswith("json"): raw = raw[4:].strip()

            query = json.loads(raw)

            # Inject hadm_id
            if hadm_id and "filter" in query and "hadm_id" not in query.get("filter", {}):
                query["filter"]["hadm_id"] = hadm_id

            # Validate
            collection = query.get("collection", "")
            if collection not in settings.ALLOWED_COLLECTIONS:
                return None

            # Execute
            filter_doc = query.get("filter", {})
            sort_spec = query.get("sort", [])
            limit = min(query.get("limit", 100), 100)

            cursor = self.db[collection].find(filter_doc)
            for s in sort_spec:
                if isinstance(s, list) and len(s) == 2:
                    cursor = cursor.sort(s[0], s[1])
            cursor = cursor.limit(limit)

            rows = []
            async for doc in cursor:
                rows.append(self._serialize(doc))

            if not rows:
                return {
                    "answer": "No data found for this query.",
                    "query": {"method": "gemini", **query},
                    "supporting_rows": 0,
                    "evidence": [],
                    "refused": True,
                    "error": None,
                }

            # Build answer from CODE (not another API call!)
            answer = f"Found {len(rows)} records. "
            if rows:
                answer += f"Fields: {', '.join(list(rows[0].keys())[:8])}. "
            answer += "Research use only."

            evidence = self._attach_evidence(rows, collection)

            return {
                "answer": answer,
                "query": {"method": "gemini", **query},
                "supporting_rows": len(rows),
                "evidence": evidence[:100],
                "refused": False,
                "error": None,
            }

        except Exception as e:
            print(f"  ✗ Gemini error: {str(e)[:80]}")
            return None

    # ─── HELPERS ───────────────────────────────

    def _serialize(self, doc: dict) -> dict:
        from bson import ObjectId
        result = {}
        for k, v in doc.items():
            if k == "_id":
                result[k] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            else:
                result[k] = v
        return result

    def _attach_evidence(self, rows: list[dict], collection: str) -> list[dict]:
        evidenced = []
        for row in rows:
            doc_id = row.get("_id", "?")
            ct = row.get("charttime") or row.get("admittime") or row.get("intime")
            charttime = None
            if isinstance(ct, str):
                try: charttime = datetime.fromisoformat(ct)
                except: pass
            elif isinstance(ct, datetime):
                charttime = ct

            evidenced.append({
                "data": {k: v for k, v in row.items() if k != "_id"},
                "source_trace": SourceTrace(
                    collection=collection,
                    fields=",".join(k for k in row.keys() if k != "_id")[:100],
                    doc_id=doc_id,
                    charttime=charttime,
                ).to_dict(),
            })
        return evidenced