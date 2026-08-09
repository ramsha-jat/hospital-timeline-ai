# app/config.py — FULL FILE (replace everything)
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str = "mongodb+srv://ramshabscsf19:xNKxr8MjSeGEr87z@cluster0.8keb21y.mongodb.net/"
    MONGODB_DATABASE: str = "curelens_ai"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.0
    GEMINI_MAX_RETRIES: int = 3

    # Safety
    SQL_MAX_ROWS: int = 5000
    MONGO_QUERY_TIMEOUT_MS: int = 30000

    ALLOWED_COLLECTIONS: list[str] = [
        "patients", "admissions", "icustays", "transfers",
        "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
        "chartevents", "outputevents", "inputevents_mv",
        "d_labitems", "d_items", "d_icd_diagnoses", "d_icd_procedures",
    ]

    # Timeline
    HIGH_VOLUME_THRESHOLD: int = 50
    MAX_TIMELINE_EVENTS: int = 10000

    # .env file config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Print loaded values on console
    print("=" * 50)
    print("⚙️  Settings loaded from .env:")
    print(f"   MONGODB_DATABASE = {settings.MONGODB_DATABASE}")
    print(f"   GEMINI_MODEL     = {settings.GEMINI_MODEL}")
    print(f"   GEMINI_API_KEY   = {settings.GEMINI_API_KEY[:8]}..." if len(settings.GEMINI_API_KEY) > 8 else f"   GEMINI_API_KEY   = {settings.GEMINI_API_KEY}")
    print(f"   MONGODB_URI      = {settings.MONGODB_URI[:30]}...")
    print("=" * 50)
    return settings