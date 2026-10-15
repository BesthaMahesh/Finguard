import re
from typing import Dict, Any

class PIIMasker:
    """
    Masks confidential customer account identifiers and sensitive tokens in logs and reports.
    """
    @staticmethod
    def mask_account_id(account_id: str) -> str:
        if not account_id or len(account_id) < 5:
            return account_id
        # Example C123456789 -> C123***789
        prefix = account_id[:4]
        suffix = account_id[-3:]
        return f"{prefix}***{suffix}"

    @classmethod
    def sanitize_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = record.copy()
        if "name_orig" in sanitized:
            sanitized["name_orig_masked"] = cls.mask_account_id(str(sanitized["name_orig"]))
        if "name_dest" in sanitized:
            sanitized["name_dest_masked"] = cls.mask_account_id(str(sanitized["name_dest"]))
        return sanitized

class PromptGuard:
    """
    Defense-in-depth sanitization for user queries sent to AI Assistant and Agent orchestrator.
    Detects prompt injection vectors, jailbreak keywords, and unauthorized SQL injection attempts.
    """
    SUSPICIOUS_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+instructions",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"system\s*override",
        r"drop\s+table",
        r"delete\s+from",
        r"bypass\s+(security|authorization|rules)",
        r"reveal\s+(api\s*key|secret|password)"
    ]

    @classmethod
    def check_prompt(cls, prompt_text: str) -> tuple[bool, str]:
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, prompt_text, re.IGNORECASE):
                return False, f"Potential prompt manipulation / policy violation detected: '{pattern}'"
        return True, "PROMPT_SAFE"
