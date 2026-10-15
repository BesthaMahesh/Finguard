from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinGuard - Autonomous Financial Risk Intelligence"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    API_V1_STR: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    DATABASE_URL: str = "sqlite:///./finguard.db"
    
    # LLM Settings
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    
    # Security Settings
    SECRET_KEY: str = "finguard-enterprise-autonomous-risk-intelligence-secure-jwt-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    RATE_LIMIT_PER_MINUTE: int = 120
    
    # OpenTelemetry Settings
    OTEL_SERVICE_NAME: str = "finguard-risk-intelligence"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    ENABLE_TRACING: bool = True
    
    # Data & ML
    DATASET_RAW_PATH: str = "PS_20174392719_1491204439457_log.csv"
    MODEL_ARTIFACTS_DIR: str = "./models"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    RANDOM_SEED: int = 42
    FRAUD_THRESHOLD: float = 0.65

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
