# app/api/routes/evidence.py
"""
Evidence routes — navigate from any claim back to its source data.
Core requirement: "clear trail back to the source data"
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from app.db.connection import get_db
from app.timeline.schemas import SourceTrace
from app.evidence.attribution import AttributionEngine
from app.evidence.formatter import EvidenceFormatter

router = APIRouter()


@router.get("/trace/{collection}/{doc_id}")
async def get_source_document(
    collection: str,
    doc_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Navigate from a source trace back to the exact source document.
    This is the audit trail endpoint.
    """
    allowed_collections = [
        "patients", "admissions", "icustays", "transfers",
        "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
        "chartevents", "outputevents", "inputevents_mv",
        "d_labitems", "d_items", "d_icd_diagnoses", "d_icd_procedures",
    ]
    
    if collection not in allowed_collections:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{collection}' not allowed. Allowed: {allowed_collections}"
        )
    
    engine = AttributionEngine(db)
    doc = await engine.fetch_source_document(collection, doc_id)
    
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document {doc_id} not found in {collection}"
        )
    
    formatter = EvidenceFormatter()
    return {
        "collection": collection,
        "doc_id": doc_id,
        "document": doc,
        "formatted": formatter.format_source_document(collection, doc),
        "disclaimer": "This is raw structured data from the source collection, not a clinical note",
    }


@router.get("/trace/{collection}/{doc_id}/raw")
async def get_raw_source_document(
    collection: str,
    doc_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get the raw MongoDB document with no formatting."""
    allowed_collections = [
        "patients", "admissions", "icustays", "transfers",
        "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
        "chartevents", "outputevents", "inputevents_mv",
        "d_labitems", "d_items", "d_icd_diagnoses", "d_icd_procedures",
    ]
    
    if collection not in allowed_collections:
        raise HTTPException(status_code=400, detail=f"Collection not allowed")
    
    engine = AttributionEngine(db)
    doc = await engine.fetch_source_document(collection, doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.get("/link/{event_id}")
async def get_event_source_link(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Given a timeline event_id, find and return its source document.
    Event IDs follow the pattern: {category}_{row_id}
    e.g., lab_6709a3f2..., med_5f8d..., dx_4a2b...
    """
    engine = AttributionEngine(db)
    result = await engine.resolve_event_to_source(event_id)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not resolve event_id '{event_id}' to a source document"
        )
    
    return result


@router.post("/batch-verify")
async def batch_verify_traces(
    traces: list[dict],
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Verify a batch of source traces — check that each
    document actually exists in the database.
    Used for evaluation and quality assurance.
    """
    engine = AttributionEngine(db)
    results = await engine.batch_verify(traces)
    return results


@router.get("/collection-stats")
async def collection_stats(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get statistics about each collection for provenance reporting."""
    stats = {}
    
    collections = [
        "patients", "admissions", "icustays", "transfers",
        "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
        "chartevents", "outputevents",
        "d_labitems", "d_items", "d_icd_diagnoses", "d_icd_procedures",
    ]
    
    for coll_name in collections:
        try:
            count = await db[coll_name].count_documents({})
            stats[coll_name] = {
                "document_count": count,
                "available": True,
            }
        except Exception as e:
            stats[coll_name] = {
                "document_count": 0,
                "available": False,
                "error": str(e),
            }
    
    return {
        "collections": stats,
        "total_documents": sum(s["document_count"] for s in stats.values()),
    }