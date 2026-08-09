# app/main.py — FULL FILE (copy-paste karo)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.connection import get_mongo_client, check_connection, get_database
from app.api.routes import timeline, query, validation, evidence

@asynccontextmanager
async def lifespan(app: FastAPI):
    connected = await check_connection()
    if not connected:
        print("⚠️  MongoDB connection failed")
    else:
        print("✅ Connected to MongoDB")
        db = get_database()
        patient_count = await db.patients.count_documents({})
        print(f"   {patient_count} patients in database")
    yield
    client = get_mongo_client()
    client.close()

app = FastAPI(
    title="Hospital Timeline AI",
    description="Structured Patient Timeline & Evidence Retrieval — Track 1",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])

@app.get("/health")
async def health():
    connected = await check_connection()
    return {
        "status": "ok" if connected else "degraded",
        "database": "connected" if connected else "disconnected",
    }

@app.get("/")
async def root():
    return {
        "app": "Hospital Timeline AI",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "timeline": "/api/timeline/{hadm_id}",
            "query": "/api/query/ask",
            "validation": "/api/validation/quality/{hadm_id}",
            "census": "/api/validation/census",
            "evidence": "/api/evidence/trace/{collection}/{doc_id}",
        }
    }