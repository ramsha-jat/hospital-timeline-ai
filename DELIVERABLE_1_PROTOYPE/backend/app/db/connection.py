# app/db/connection.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings
from functools import lru_cache

@lru_cache()
def get_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    return AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

def get_database() -> AsyncIOMotorDatabase:
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.MONGODB_DATABASE]

# FastAPI dependency
async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency — gives you the MongoDB database."""
    db = get_database()
    try:
        yield db
    finally:
        pass  # Motor handles connection pooling

# Startup check
async def check_connection() -> bool:
    try:
        client = get_mongo_client()
        await client.admin.command("ping")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False