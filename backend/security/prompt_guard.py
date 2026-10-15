import re

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
