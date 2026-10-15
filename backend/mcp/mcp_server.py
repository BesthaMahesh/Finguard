from typing import Dict, Any, List
from backend.mcp.mcp_tools import FinGuardMCPTools

MCP_TOOL_DEFINITIONS = [
    {
        "name": "lookup_transaction",
        "description": "Retrieve comprehensive financial transaction record and current risk metrics by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "integer", "description": "Transaction integer ID"}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "lookup_account",
        "description": "Retrieve synthetic behavioral profile and transaction history for an account.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Synthetic account ID (C... or M...)"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "calculate_risk",
        "description": "Calculate ML fraud probability, run deterministic rules, and get SHAP feature contributions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "step": {"type": "integer"},
                "type": {"type": "string", "enum": ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]},
                "amount": {"type": "number"},
                "name_orig": {"type": "string"},
                "old_balance_org": {"type": "number"},
                "new_balance_orig": {"type": "number"},
                "name_dest": {"type": "string"},
                "old_balance_dest": {"type": "number"},
                "new_balance_dest": {"type": "number"}
            },
            "required": ["type", "amount", "name_orig", "old_balance_org", "new_balance_orig", "name_dest", "old_balance_dest", "new_balance_dest"]
        }
    },
    {
        "name": "search_policies",
        "description": "Search financial crime compliance manuals, AML regulations, and fraud typologies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Compliance or investigation query"},
                "top_k": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_investigation_case",
        "description": "Create a case docket for a suspicious transaction requiring investigator review.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "integer"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
            },
            "required": ["transaction_id", "title", "summary"]
        }
    },
    {
        "name": "update_case_disposition",
        "description": "Update case disposition (ESCALATE_TO_SAR, FREEZE_ACCOUNT, REQUEST_ADDITIONAL_KYC, DISMISS_FALSE_POSITIVE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "disposition": {"type": "string"},
                "disposition_notes": {"type": "string"}
            },
            "required": ["case_id", "disposition", "disposition_notes"]
        }
    },
    {
        "name": "check_synthetic_watchlist",
        "description": "Screen an entity against synthetic internal mock watchlist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string"}
            },
            "required": ["entity_name"]
        }
    }
]

class MCPServer:
    """
    Model Context Protocol (MCP) compatible server interface.
    """
    @staticmethod
    def list_tools() -> List[Dict[str, Any]]:
        return MCP_TOOL_DEFINITIONS

    @staticmethod
    def call_tool(name: str, arguments: Dict[str, Any], user_role: str = "analyst", username: str = "agent") -> Dict[str, Any]:
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
            return {"error": f"Unknown tool: {name}", "status": "TOOL_NOT_FOUND"}

        return func(arguments, user_role=user_role, username=username)

mcp_server = MCPServer()
