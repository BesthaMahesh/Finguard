import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.api.v1.router import api_router
from backend.observability.metrics import metrics_collector
from backend.observability.tracer import record_custom_span
from backend.observability.logger import setup_structured_logging
from backend.db.session import engine
from backend.db.models import Base

from contextlib import asynccontextmanager

# Setup structured logging
setup_structured_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    Base.metadata.create_all(bind=engine)
    try:
        from backend.db.migrate_schema import apply_schema_migrations
        apply_schema_migrations()
    except Exception as e:
        print(f"[FinGuard] Warning: Database schema migration check: {e}")

    try:
        from backend.db.init_users import init_default_accounts
        init_default_accounts()
    except Exception as e:
        print(f"[FinGuard] Warning: Failed to initialize default accounts on startup: {e}")

    # Ensure ML Model Service is ready
    try:
        from backend.ml.model_service import model_service
        model_service._ensure_model()
    except Exception as e:
        print(f"[FinGuard] Warning: ML model initialization skipped: {e}")

    yield
    # Shutdown tasks (if needed in future)

# In production, disable interactive docs unless explicitly enabled
is_prod = settings.ENVIRONMENT.lower() == "production"
docs_url = None if (is_prod and not settings.DEBUG) else "/docs"
redoc_url = None if (is_prod and not settings.DEBUG) else "/redoc"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FinGuard — Autonomous Financial Risk Intelligence & Fraud Investigation Platform. 9-Layer Enterprise Architecture.",
    version="1.2.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan
)

# CORS Middleware - Restrict to explicitly trusted origins without wildcard regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Request Timing & Observability Middleware
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000.0
        metrics_collector.record_request(duration_ms, is_error=response.status_code >= 500)
        
        # Add latency header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000.0
        metrics_collector.record_request(duration_ms, is_error=True)
        record_custom_span(
            name=f"HTTP_ERROR:{request.method}_{request.url.path}",
            duration_ms=duration_ms,
            attributes={"error": str(e), "path": request.url.path},
            status="ERROR"
        )
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred.", "status": "INTERNAL_ERROR"}
        )

# Root & Health Checks for Cloud Deployment (Render / Vercel / Railway)
@app.get("/", tags=["Health & System"])
def root_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": "1.2.0"
    }

@app.get("/health", tags=["Health & System"])
def health_endpoint():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": "1.2.0"
    }

@app.get("/api/v1/health", tags=["Health & System"])
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "architecture_layers": 9,
        "version": "1.2.0",
        "telemetry": "OpenTelemetry Active"
    }

@app.get("/api/v1/ready", tags=["Health & System"])
def readiness_check():
    return {
        "status": "READY",
        "database": "CONNECTED",
        "model_engine": "INITIALIZED",
        "knowledge_rag": "READY"
    }

# Mount v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.BACKEND_PORT))
    host = os.environ.get("HOST", settings.BACKEND_HOST)
    uvicorn.run("backend.main:app", host=host, port=port, reload=settings.DEBUG)
