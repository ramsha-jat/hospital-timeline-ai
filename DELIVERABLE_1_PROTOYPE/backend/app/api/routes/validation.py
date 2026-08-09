# app/api/routes/validation.py
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.connection import get_db

router = APIRouter()

@router.get("/quality/{hadm_id}")
async def check_quality(
    hadm_id: int,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    admission = await db.admissions.find_one({"hadm_id": hadm_id})
    if not admission:
        return {"valid": False, "issues": ["Admission not found"]}
    
    issues = []
    warnings = []
    
    # Check temporal consistency
    if admission.get("dischtime") and admission["dischtime"] < admission["admittime"]:
        issues.append("dischtime < admittime")
    
    # Check missing timestamps
    labs_no_time = await db.labevents.count_documents({
        "hadm_id": hadm_id, "charttime": None
    })
    if labs_no_time > 0:
        issues.append(f"{labs_no_time} lab events missing charttime")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "hadm_id": hadm_id,
        "disclaimer": "Data quality checks for research validation, not clinical safety",
    }

@router.get("/census")
async def dataset_census(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Dataset census — sample counts and missingness."""
    census = {}
    
    for coll_name in ["patients", "admissions", "icustays", "labevents", "prescriptions", "diagnoses_icd", "chartevents"]:
        census[coll_name] = await db[coll_name].count_documents({})
    
    # Gender distribution
    pipeline = [{"$group": {"_id": "$gender", "count": {"$sum": 1}}}]
    gender_dist = {}
    async for doc in db.patients.aggregate(pipeline):
        gender_dist[doc["_id"]] = doc["count"]
    
    return {
        "table_counts": census,
        "gender_distribution": gender_dist,
        "total_patients": census.get("patients", 0),
        "total_admissions": census.get("admissions", 0),
    }