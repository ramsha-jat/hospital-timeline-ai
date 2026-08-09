# app/evidence/attribution.py
"""
Attribution engine — resolves claims to their source data.
This is the core of "clear trail back to the source data".
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId
import json


class AttributionEngine:
    """
    Every claim must be traceable to its source document.
    This engine resolves source traces back to actual MongoDB documents.
    """
    
    # Mapping of event_id prefixes to collections and key fields
    EVENT_PREFIX_MAP = {
        "admission": ("admissions", "hadm_id"),
        "discharge": ("admissions", "hadm_id"),
        "transfer": ("transfers", "transfer_id"),
        "icu_in": ("icustays", "stay_id"),
        "icu_out": ("icustays", "stay_id"),
        "lab": ("labevents", "labevent_id"),
        "med": ("prescriptions", "prescription_id"),
        "dx": ("diagnoses_icd", "row_id"),
        "px": ("procedures_icd", "row_id"),
        "chart": ("chartevents", "chartevent_id"),
        "output": ("outputevents", "outputevent_id"),
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def fetch_source_document(
        self, collection: str, doc_id: str
    ) -> Optional[dict]:
        """
        Fetch a specific document from MongoDB by its ID.
        Tries ObjectId first, then falls back to string lookup.
        """
        try:
            # Try as ObjectId
            try:
                oid = ObjectId(doc_id)
                doc = await self.db[collection].find_one({"_id": oid})
                if doc:
                    return self._serialize(doc)
            except Exception:
                pass
            
            # Try as business key (hadm_id, stay_id, etc.)
            # Determine which field to search by
            key_field = self._get_key_field(collection)
            if key_field:
                try:
                    key_value = int(doc_id)
                    doc = await self.db[collection].find_one({key_field: key_value})
                    if doc:
                        return self._serialize(doc)
                except ValueError:
                    pass
            
            # Try as string match on _id
            doc = await self.db[collection].find_one({"_id": doc_id})
            if doc:
                return self._serialize(doc)
            
            return None
            
        except Exception as e:
            return {"error": str(e), "collection": collection, "doc_id": doc_id}
    
    async def resolve_event_to_source(
        self, event_id: str
    ) -> Optional[dict]:
        """
        Resolve a timeline event_id to its source MongoDB document.
        Event IDs follow pattern: {category_prefix}_{identifier}
        e.g., lab_6709a3f2e4b0, med_5f8d..., dx_4a2b...
        """
        # Parse event_id
        parts = event_id.split("_", 1)
        if len(parts) != 2:
            return {
                "event_id": event_id,
                "resolved": False,
                "error": "Invalid event_id format. Expected: prefix_identifier",
            }
        
        prefix, identifier = parts
        
        # Find matching collection
        if prefix not in self.EVENT_PREFIX_MAP:
            # Try partial matching
            matched_prefix = None
            for known_prefix in self.EVENT_PREFIX_MAP:
                if prefix.startswith(known_prefix) or known_prefix.startswith(prefix):
                    matched_prefix = known_prefix
                    break
            
            if not matched_prefix:
                return {
                    "event_id": event_id,
                    "resolved": False,
                    "error": f"Unknown event prefix: {prefix}",
                }
            prefix = matched_prefix
        
        collection, key_field = self.EVENT_PREFIX_MAP[prefix]
        
        # Try to fetch the document
        doc = await self.fetch_source_document(collection, identifier)
        
        if doc and "error" not in doc:
            return {
                "event_id": event_id,
                "resolved": True,
                "source_trace": {
                    "collection": collection,
                    "doc_id": identifier,
                    "key_field": key_field,
                },
                "document": doc,
                "disclaimer": self._get_disclaimer(collection),
            }
        
        return {
            "event_id": event_id,
            "resolved": False,
            "error": f"Source document not found: {collection}/{identifier}",
        }
    
    async def batch_verify(self, traces: list[dict]) -> dict:
        """
        Verify a batch of source traces.
        Each trace should have: collection, doc_id, fields.
        Returns which traces are valid/invalid.
        """
        results = {
            "total": len(traces),
            "valid": 0,
            "invalid": 0,
            "details": [],
        }
        
        for trace in traces:
            collection = trace.get("collection", "")
            doc_id = trace.get("doc_id", "")
            
            doc = await self.fetch_source_document(collection, doc_id)
            
            is_valid = doc is not None and "error" not in (doc or {})
            
            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
            
            # Verify that claimed fields exist in the document
            claimed_fields = trace.get("fields", "").split(",")
            missing_fields = []
            if is_valid and doc:
                for field in claimed_fields:
                    field = field.strip()
                    if field and field not in doc:
                        missing_fields.append(field)
            
            results["details"].append({
                "collection": collection,
                "doc_id": doc_id,
                "valid": is_valid,
                "missing_fields": missing_fields,
            })
        
        results["coverage"] = round(results["valid"] / results["total"], 4) if results["total"] > 0 else 0
        
        return results
    
    async def create_source_trace(
        self,
        collection: str,
        doc: dict,
        fields_used: list[str],
    ) -> dict:
        """
        Create a source trace from a MongoDB document.
        Called by the timeline builder for every event.
        """
        doc_id = str(doc.get("_id", ""))
        
        # Find the primary timestamp
        charttime = None
        for time_field in ["charttime", "admittime", "intime", "starttime", "storetime"]:
            if doc.get(time_field):
                val = doc[time_field]
                if isinstance(val, datetime):
                    charttime = val
                break
        
        return {
            "collection": collection,
            "fields": ",".join(fields_used),
            "doc_id": doc_id,
            "charttime": charttime.isoformat() if charttime else None,
        }
    
    def _get_key_field(self, collection: str) -> Optional[str]:
        """Map collection name to its business key field."""
        key_map = {
            "patients": "subject_id",
            "admissions": "hadm_id",
            "icustays": "stay_id",
            "transfers": "transfer_id",
            "labevents": "labevent_id",
            "prescriptions": "prescription_id",
            "diagnoses_icd": "row_id",
            "procedures_icd": "row_id",
            "chartevents": "chartevent_id",
            "outputevents": "outputevent_id",
            "d_labitems": "itemid",
            "d_items": "itemid",
            "d_icd_diagnoses": "icd_code",
            "d_icd_procedures": "icd_code",
        }
        return key_map.get(collection)
    
    def _get_disclaimer(self, collection: str) -> str:
        """Get appropriate disclaimer for a collection type."""
        if collection in ("diagnoses_icd", "d_icd_diagnoses"):
            return "ICD billing code from structured data, NOT a clinician-authored diagnosis note"
        elif collection in ("procedures_icd", "d_icd_procedures"):
            return "ICD procedure code from structured data, NOT a clinician-authored procedure note"
        elif collection in ("d_labitems", "d_items"):
            return "Label from dictionary table, NOT a clinician-authored note"
        elif collection in ("prescriptions",):
            return "Drug name from pharmacy system, NOT a clinical order note"
        else:
            return "Structured clinical data, NOT a clinician-authored note"
    
    def _serialize(self, doc: dict) -> dict:
        """Serialize MongoDB document for JSON response."""
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