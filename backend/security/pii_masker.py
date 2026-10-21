"""
Backward compatibility module for PIIMasker and PromptGuard.
Binds to enhanced FinancialPIIProtector and PromptGuard.
"""

from typing import Dict, Any
from backend.security.pii_protection import pii_protector
from backend.security.prompt_guard import PromptGuard

class PIIMasker:
    """
    Masks confidential customer account identifiers and sensitive tokens in logs and reports.
    Delegates to Presidio-backed FinancialPIIProtector with zero-overhead fallback.
    """
    @staticmethod
    def mask_account_id(account_id: str) -> str:
        return pii_protector.mask_financial_account(account_id)

    @classmethod
    def sanitize_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        return pii_protector.sanitize_dictionary(record)

__all__ = ["PIIMasker", "PromptGuard", "pii_protector"]
