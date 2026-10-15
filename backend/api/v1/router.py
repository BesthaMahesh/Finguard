from fastapi import APIRouter
from backend.api.v1.endpoints import (
    auth,
    transactions,
    risk,
    investigations,
    models,
    knowledge,
    audit,
    observability,
    dashboard,
    assistant,
    mcp_routes
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(transactions.router)
api_router.include_router(risk.router)
api_router.include_router(investigations.router)
api_router.include_router(models.router)
api_router.include_router(knowledge.router)
api_router.include_router(audit.router)
api_router.include_router(observability.router)
api_router.include_router(assistant.router)
api_router.include_router(mcp_routes.router)
