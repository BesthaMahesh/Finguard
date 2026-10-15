from enum import Enum
from typing import Set
from fastapi import HTTPException, status

class UserRole(str, Enum):
    # Primary Enterprise Roles
    USER = "USER"
    ADMIN = "ADMIN"

    # Legacy Compatibility Roles
    ANALYST = "analyst"
    INVESTIGATOR = "investigator"
    AUDITOR = "auditor"
    ADMINISTRATOR = "administrator"

# Permissions matrix
ROLE_PERMISSIONS = {
    # Primary Enterprise Roles
    UserRole.USER: {
        "view_health",
        "view_transactions",
        "run_risk_analysis",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "create_case",
        "view_cases",
        "submit_review_notes",
        "update_disposition",
        "review_case",
        "view_model_performance",
        "view_model_governance",
    },
    UserRole.ADMIN: {
        "view_health",
        "view_transactions",
        "run_risk_analysis",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "create_case",
        "view_cases",
        "submit_review_notes",
        "update_disposition",
        "review_case",
        "export_cases",
        "view_model_performance",
        "view_model_governance",
        "view_audit_trail",
        "view_observability",
        "view_detailed_telemetry",
        "manage_users",
        "retrain_model",
        "ingest_data",
        "manage_knowledge",
        "reindex_documents",
        "system_config",
        "model_deployment_config",
    },
    # Legacy Compatibility Roles for Existing Tests
    UserRole.ANALYST: {
        "view_health",
        "view_transactions",
        "run_risk_analysis",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "create_case",
        "view_observability",
    },
    UserRole.INVESTIGATOR: {
        "view_health",
        "view_transactions",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "create_case",
        "update_disposition",
        "review_case",
        "view_observability",
    },
    UserRole.AUDITOR: {
        "view_health",
        "view_transactions",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "view_audit_trail",
        "view_model_governance",
        "view_observability",
    },
    UserRole.ADMINISTRATOR: {
        "view_health",
        "view_transactions",
        "run_risk_analysis",
        "view_dashboard",
        "search_policies",
        "ask_ai_assistant",
        "create_case",
        "update_disposition",
        "review_case",
        "export_cases",
        "view_audit_trail",
        "view_model_governance",
        "view_observability",
        "view_detailed_telemetry",
        "manage_users",
        "retrain_model",
        "ingest_data",
        "system_config",
    },
}

LEGACY_ROLE_MAP = {
    "analyst": UserRole.ANALYST,
    "investigator": UserRole.INVESTIGATOR,
    "auditor": UserRole.AUDITOR,
    "administrator": UserRole.ADMINISTRATOR,
    "admin": UserRole.ADMIN,
    "user": UserRole.USER,
}

def normalize_role(role_str: str) -> UserRole:
    if isinstance(role_str, UserRole):
        return role_str
    clean = str(role_str).strip()
    if clean.upper() == "ADMIN":
        return UserRole.ADMIN
    if clean.upper() == "USER":
        return UserRole.USER
    mapped = LEGACY_ROLE_MAP.get(clean.lower())
    if mapped:
        return mapped
    return UserRole.USER

def verify_role_permission(user_role: str, permission: str) -> bool:
    role_enum = normalize_role(user_role)
    perms = ROLE_PERMISSIONS.get(role_enum, set())
    return permission in perms

def check_permission(user_role: str, permission: str):
    if not verify_role_permission(user_role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: Role '{user_role}' lacks permission '{permission}'."
        )
