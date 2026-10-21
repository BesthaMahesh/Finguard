from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinGuard - Autonomous Financial Risk Intelligence"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    API_V1_STR: str = "/api/v1"
    BACKEND_HOST: str = os.environ.get("HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.environ.get("PORT", 8000))
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

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self):
        env = (self.ENVIRONMENT or "").strip().lower()
        if env == "production":
            insecure_defaults = [
                "finguard-enterprise-autonomous-risk-intelligence-secure-jwt-key",
                "finguard-secret-key-for-development-change-in-production",
                "secret",
                "changeme",
                "password"
            ]
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_defaults or len(self.SECRET_KEY) < 32:
                # If running on cloud platforms (Render, Heroku, Docker) where secret was omitted
                if os.environ.get("RENDER") or os.environ.get("AUTO_GENERATE_SECRET", "true").lower() == "true":
                    import secrets
                    import logging
                    auto_key = secrets.token_urlsafe(48)
                    self.SECRET_KEY = auto_key
                    logging.getLogger("finguard.security").warning(
                        "[SECURITY NOTICE] No strong SECRET_KEY was provided in production environment. "
                        "Generated ephemeral 48-byte cryptographic key for this runtime. "
                        "To persist user login sessions across restarts, set SECRET_KEY in your cloud environment dashboard."
                    )
                else:
                    raise ValueError(
                        "SECURITY FATAL: In production ENVIRONMENT, SECRET_KEY must be a cryptographically strong "
                        "string provided via environment variables (at least 32 characters) and cannot use default/development values."
                    )
            if self.DEBUG is True:
                raise ValueError("SECURITY FATAL: DEBUG mode must be disabled (DEBUG=False) in production.")
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError("SECURITY FATAL: Wildcard CORS origin ('*') is prohibited in production when credentials are enabled.")
        return self

settings = Settings()
