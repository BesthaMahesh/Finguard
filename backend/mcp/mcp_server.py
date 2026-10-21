"""
FinGuard Model Context Protocol (MCP) Server.
Enforces defense-in-depth:
- Explicit Approved Tool Allowlist
- Read-Only vs. Side-Effect Separation
- Server-Side Role-Based Authorization & Permission Verification
- Human-in-the-Loop Approval Enforcement for Severe Actions
- Safe Failure Modes
"""

from typing import Dict, Any, List, Optional
from backend.mcp.mcp_tools import FinGuardMCPTools
from backend.security.rbac import verify_role_permission, normalize_role, UserRole

MCP_TOOL_DEFINITIONS = [
    {
        "name": "lookup_transaction",
        "description": "Retrieve comprehensive financial transaction record and current risk metrics by ID.",
        "category": "READ_ONLY",
        "required_permission": "view_transactions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "integer", "description": "Transaction integer ID", "minimum": 1}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "lookup_account",
        "description": "Retrieve synthetic behavioral profile and transaction history for an account.",
        "category": "READ_ONLY",
        "required_permission": "view_transactions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Synthetic account ID (C... or M...)", "minLength": 3, "maxLength": 50}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "calculate_risk",
        "description": "Calculate ML fraud probability, run deterministic rules, and get SHAP feature contributions.",
        "category": "READ_ONLY",
        "required_permission": "run_risk_analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "step": {"type": "integer", "minimum": 1},
                "type": {"type": "string", "enum": ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]},
                "amount": {"type": "number", "minimum": 0.0},
                "name_orig": {"type": "string", "minLength": 2, "maxLength": 50},
                "old_balance_org": {"type": "number", "minimum": 0.0},
                "new_balance_orig": {"type": "number", "minimum": 0.0},
                "name_dest": {"type": "string", "minLength": 2, "maxLength": 50},
                "old_balance_dest": {"type": "number", "minimum": 0.0},
                "new_balance_dest": {"type": "number", "minimum": 0.0}
            },
            "required": ["type", "amount", "name_orig", "old_balance_org", "new_balance_orig", "name_dest", "old_balance_dest", "new_balance_dest"]
        }
    },
    {
        "name": "search_policies",
        "description": "Search financial crime compliance manuals, AML regulations, and fraud typologies.",
        "category": "READ_ONLY",
        "required_permission": "search_policies",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Compliance or investigation query", "minLength": 3, "maxLength": 1000},
                "top_k": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
                "event_date": {"type": "string", "description": "Optional ISO event date (YYYY-MM-DD) for historical policy versioning"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_investigation_case",
        "description": "Create a case docket for a suspicious transaction requiring investigator review.",
        "category": "SIDE_EFFECT",
        "required_permission": "create_case",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "integer", "minimum": 1},
                "title": {"type": "string", "minLength": 5, "maxLength": 200},
                "summary": {"type": "string", "minLength": 10, "maxLength": 4000},
                "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
            },
            "required": ["transaction_id", "title", "summary"]
        }
    },
    {
        "name": "update_case_disposition",
        "description": "Update case disposition (ESCALATE_TO_SAR, FREEZE_ACCOUNT, REQUEST_ADDITIONAL_KYC, DISMISS_FALSE_POSITIVE).",
        "category": "SIDE_EFFECT",
        "required_permission": "update_disposition",
        "requires_human_approval": True,
        "inputSchema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "minLength": 5},
                "disposition": {"type": "string", "enum": ["ESCALATE_TO_SAR", "FREEZE_ACCOUNT", "REQUEST_ADDITIONAL_KYC", "DISMISS_FALSE_POSITIVE"]},
                "disposition_notes": {"type": "string", "minLength": 5, "maxLength": 4000},
                "approved_by_human": {"type": "boolean", "description": "Confirmation of human analyst authorization for high-severity actions"}
            },
            "required": ["case_id", "disposition", "disposition_notes"]
        }
    },
    {
        "name": "check_synthetic_watchlist",
        "description": "Screen an entity against synthetic internal mock watchlist.",
        "category": "READ_ONLY",
        "required_permission": "view_transactions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "minLength": 2, "maxLength": 100}
            },
            "required": ["entity_name"]
        }
    }
]

# Explicit Tool Allowlist
ALLOWED_MCP_TOOLS = {defn["name"] for defn in MCP_TOOL_DEFINITIONS}

# Tool Permission Requirements
TOOL_PERMISSION_MAP = {
    defn["name"]: defn.get("required_permission", "view_transactions")
    for defn in MCP_TOOL_DEFINITIONS
}

# High-Severity Actions requiring human approval verification
HIGH_SEVERITY_DISPOSITIONS = {"FREEZE_ACCOUNT", "ESCALATE_TO_SAR"}


class MCPServer:
    """
    Model Context Protocol (MCP) server enforcing least privilege,
    tool allowlisting, and 4-Eyes human verification.
    """

    @staticmethod
    def list_tools() -> List[Dict[str, Any]]:
        return MCP_TOOL_DEFINITIONS

    @staticmethod
    def call_tool(
        name: str,
        arguments: Dict[str, Any],
        user_role: str = "analyst",
        username: str = "agent"
    ) -> Dict[str, Any]:
        # 1. Allowlist Enforcement
        if name not in ALLOWED_MCP_TOOLS:
            return {
                "error": f"Tool '{name}' is not in the approved FinGuard MCP tool allowlist.",
                "status": "FORBIDDEN_TOOL",
                "allowed_tools": list(ALLOWED_MCP_TOOLS)
            }

        # 2. Server-Side RBAC Enforcement
        required_perm = TOOL_PERMISSION_MAP.get(name)
        if required_perm and not verify_role_permission(user_role, required_perm):
            return {
                "error": f"Unauthorized: Role '{user_role}' lacks required permission '{required_perm}' for tool '{name}'.",
                "status": "PERMISSION_DENIED"
            }

        # 3. 4-Eyes Governance: Human Approval Check for High-Severity Side Effects
        if name == "update_case_disposition":
            target_disposition = str(arguments.get("disposition", "")).strip().upper()
            if target_disposition in HIGH_SEVERITY_DISPOSITIONS:
                # Must be verified by human reviewer or explicit human approval flag with notes
                normalized = normalize_role(user_role)
                if normalized not in (UserRole.INVESTIGATOR, UserRole.ADMIN, UserRole.ADMINISTRATOR):
                    return {
                        "error": (
                            f"4-Eyes Governance Violation: Severity action '{target_disposition}' "
                            f"cannot be executed by role '{user_role}'. Requires investigator or administrator role."
                        ),
                        "status": "HUMAN_APPROVAL_REQUIRED"
                    }
                notes = str(arguments.get("disposition_notes", "")).strip()
                if len(notes) < 15:
                    return {
                        "error": "Detailed review justification (minimum 15 characters) is required for severe disposition.",
                        "status": "INSUFFICIENT_JUSTIFICATION"
                    }

        # 4. Dispatch to verified tool implementation
        tools_map = {
            "lookup_transaction": FinGuardMCPTools.lookup_transaction,
            "lookup_account": FinGuardMCPTools.lookup_account,
            "calculate_risk": FinGuardMCPTools.calculate_risk,
            "search_policies": FinGuardMCPTools.search_policies,
            "create_investigation_case": FinGuardMCPTools.create_investigation_case,
            "update_case_disposition": FinGuardMCPTools.update_case_disposition,
            "check_synthetic_watchlist": FinGuardMCPTools.check_synthetic_watchlist,
        }

        func = tools_map.get(name)
        if not func:
            return {"error": f"Tool implementation '{name}' not found.", "status": "TOOL_NOT_FOUND"}

        try:
            return func(arguments, user_role=user_role, username=username)
        except Exception as e:
            FinGuardMCPTools.log_tool_audit(name, "EXEC_EXCEPTION", username, user_role, outcome="ERROR", details={"error": str(e)})
            return {"error": f"Internal error executing tool '{name}': {str(e)}", "status": "EXECUTION_ERROR"}


mcp_server = MCPServer()
