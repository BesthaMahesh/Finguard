"""
FinGuard Enterprise PII Protection & Data Anonymization Engine
Powered by Microsoft Presidio (AnalyzerEngine & AnonymizerEngine)
With Custom Financial Recognizers, Tokenization Vault, and Fail-Safe Masking.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try loading Presidio Analyzer and Anonymizer
_PRESIDIO_AVAILABLE = False
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    _PRESIDIO_AVAILABLE = True
except ImportError:
    _PRESIDIO_AVAILABLE = False
    logger.warning("Microsoft Presidio not available; fallback regex masking will be active.")


class FinancialPIIProtector:
    """
    Enterprise PII Detection & Anonymization Engine.
    Protects user inputs, RAG retrieved context, telemetry logs, and LLM payloads.
    """

    def __init__(self):
        self.presidio_available = _PRESIDIO_AVAILABLE
        self.analyzer: Optional[Any] = None
        self.anonymizer: Optional[Any] = None
        self._vault: Dict[str, str] = {}  # Access-controlled token vault for reversible lookup

        if self.presidio_available:
            try:
                # Safely probe for locally installed spaCy models without remote download attempts
                chosen_model = None
                try:
                    import spacy
                    installed = spacy.util.get_installed_models()
                    for m in ["en_core_web_sm", "en_core_web_lg", "en_core_web_md"]:
                        if m in installed:
                            chosen_model = m
                            break
                except Exception:
                    chosen_model = None

                if chosen_model:
                    from presidio_analyzer.nlp_engine import NlpEngineProvider
                    nlp_conf = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": chosen_model}]}
                    provider = NlpEngineProvider(nlp_configuration=nlp_conf)
                    self.analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
                else:
                    try:
                        self.analyzer = AnalyzerEngine()
                    except Exception as err:
                        logger.warning(f"Presidio AnalyzerEngine skipped ({err}). Fast regex masking active.")
                        self.analyzer = None

                self.anonymizer = AnonymizerEngine()
                if self.analyzer:
                    self._register_custom_financial_recognizers()
            except Exception as e:
                logger.warning(f"Presidio model setup skipped: {e}. Active with regex pattern protection.")
                self.analyzer = None

    def _register_custom_financial_recognizers(self):
        """Register custom recognizers for banking & financial crime domain."""
        if not self.analyzer:
            return

        # 1. PaySim & Core Banking Account IDs (e.g. C1234567890, M9876543210)
        account_pattern = Pattern(
            name="paysim_account_pattern",
            regex=r"\b[CM]\d{7,12}\b",
            score=0.95
        )
        account_recognizer = PatternRecognizer(
            supported_entity="FINANCIAL_ACCOUNT",
            patterns=[account_pattern]
        )
        self.analyzer.registry.add_recognizer(account_recognizer)

        # 2. International Bank Account Number (IBAN)
        iban_pattern = Pattern(
            name="iban_pattern",
            regex=r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
            score=0.90
        )
        iban_recognizer = PatternRecognizer(
            supported_entity="IBAN_CODE",
            patterns=[iban_pattern]
        )
        self.analyzer.registry.add_recognizer(iban_recognizer)

        # 3. SWIFT / BIC Code (ISO 9362 8 or 11 characters with banking context)
        swift_pattern = Pattern(
            name="swift_bic_pattern",
            regex=r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b",
            score=0.70
        )
        swift_recognizer = PatternRecognizer(
            supported_entity="SWIFT_BIC",
            patterns=[swift_pattern],
            context=["swift", "bic", "bank", "wire", "transfer", "clearing"]
        )
        self.analyzer.registry.add_recognizer(swift_recognizer)

        # 4. Cryptocurrency Wallet Address (BTC, ETH)
        crypto_pattern = Pattern(
            name="crypto_wallet_pattern",
            regex=r"\b(0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
            score=0.90
        )
        crypto_recognizer = PatternRecognizer(
            supported_entity="CRYPTO_WALLET",
            patterns=[crypto_pattern]
        )
        self.analyzer.registry.add_recognizer(crypto_recognizer)

        # 5. Resilient International and US Phone Recognizer
        phone_pattern = Pattern(
            name="resilient_phone_pattern",
            regex=r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            score=0.95
        )
        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[phone_pattern]
        )
        self.analyzer.registry.add_recognizer(phone_recognizer)

    def analyze_pii(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Analyze text for sensitive PII entities including Person, Email, Phone,
        Financial Accounts, IBAN, SWIFT, and Crypto wallets.
        """
        if not text or not isinstance(text, str):
            return []

        results = []
        if self.presidio_available and self.analyzer:
            try:
                analyzer_results = self.analyzer.analyze(
                    text=text,
                    language=language,
                    entities=[
                        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS",
                        "CREDIT_CARD", "US_SSN", "FINANCIAL_ACCOUNT", "IBAN_CODE",
                        "SWIFT_BIC", "CRYPTO_WALLET"
                    ]
                )
                for res in analyzer_results:
                    results.append({
                        "entity_type": res.entity_type,
                        "start": res.start,
                        "end": res.end,
                        "score": round(res.score, 3),
                        "text": text[res.start:res.end]
                    })
                return results
            except Exception as e:
                logger.error(f"Presidio analyze error: {e}. Executing fallback analyzer.")

        # Fallback Regex Analyzer
        return self._fallback_regex_analyze(text)

    def redact_pii(
        self,
        text: str,
        language: str = "en",
        mask_accounts: bool = True,
        preserve_in_vault: bool = False
    ) -> str:
        """
        Redacts all identified PII entities.
        If preserve_in_vault is True, sensitive values can be restored by authorized investigators.
        """
        if not text or not isinstance(text, str):
            return text or ""

        if self.presidio_available and self.analyzer and self.anonymizer:
            try:
                analyzer_results = self.analyzer.analyze(
                    text=text,
                    language=language,
                    entities=[
                        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS",
                        "CREDIT_CARD", "US_SSN", "FINANCIAL_ACCOUNT", "IBAN_CODE",
                        "SWIFT_BIC", "CRYPTO_WALLET"
                    ]
                )

                if not analyzer_results:
                    return text

                # Store into vault if requested
                if preserve_in_vault:
                    for res in analyzer_results:
                        val = text[res.start:res.end]
                        token = f"<{res.entity_type}_{abs(hash(val)) % 1000000:06d}>"
                        self._vault[token] = val
                        self._vault[f"<{res.entity_type}>"] = val

                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=analyzer_results
                )
                anonymized_text = anonymized_result.text

                # Ensure phone numbers are also sanitized if libphonenumbers skipped fictitious ranges
                anonymized_text = re.sub(
                    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                    "<PHONE_NUMBER>",
                    anonymized_text
                )

                # If mask_accounts is requested, also ensure any stray account IDs are masked
                if mask_accounts and not preserve_in_vault:
                    anonymized_text = re.sub(
                        r"\b([CM]\d{3})\d{2,6}(\d{3})\b",
                        r"\1***\2",
                        anonymized_text
                    )

                return anonymized_text

            except Exception as e:
                logger.error(f"Presidio redaction failed: {e}. Applying deterministic fallback redaction.")

        # Deterministic Fallback Redactor
        return self._fallback_regex_redact(text, mask_accounts=mask_accounts)

    def restore_vault_tokens(self, redacted_text: str, user_role: str) -> str:
        """
        Restores vaulted tokens only for authorized roles (investigator, administrator).
        """
        role = (user_role or "").lower()
        if role not in ("investigator", "administrator", "admin"):
            raise PermissionError(f"Role '{user_role}' is not authorized to unmask vaulted identifiers.")

        restored = redacted_text
        for token, original in self._vault.items():
            restored = restored.replace(token, original)
        return restored

    def mask_financial_account(self, account_id: str) -> str:
        """
        Masks single account ID preserving prefix and suffix:
        C1234567890 -> C123***890
        """
        if not account_id or not isinstance(account_id, str):
            return ""
        clean = account_id.strip()
        if len(clean) >= 7 and (clean.startswith("C") or clean.startswith("M")):
            return f"{clean[:4]}***{clean[-3:]}"
        return clean

    def sanitize_dictionary(self, data: Dict[str, Any], allowed_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Recursively sanitizes dictionaries and records for safe export or logging."""
        sanitized = {}
        for k, v in data.items():
            if allowed_fields and k in allowed_fields:
                sanitized[k] = v
            elif isinstance(v, str):
                if k in ("name_orig", "name_dest", "account_id"):
                    sanitized[k] = self.mask_financial_account(v)
                else:
                    sanitized[k] = self.redact_pii(v)
            elif isinstance(v, dict):
                sanitized[k] = self.sanitize_dictionary(v, allowed_fields=allowed_fields)
            elif isinstance(v, list):
                sanitized[k] = [
                    self.sanitize_dictionary(item, allowed_fields=allowed_fields) if isinstance(item, dict)
                    else (self.redact_pii(item) if isinstance(item, str) else item)
                    for item in v
                ]
            else:
                sanitized[k] = v
        return sanitized

    def _fallback_regex_analyze(self, text: str) -> List[Dict[str, Any]]:
        results = []
        patterns = {
            "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "PHONE_NUMBER": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "FINANCIAL_ACCOUNT": r"\b[CM]\d{7,12}\b",
            "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "IP_ADDRESS": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        }
        for entity, pat in patterns.items():
            for match in re.finditer(pat, text):
                results.append({
                    "entity_type": entity,
                    "start": match.start(),
                    "end": match.end(),
                    "score": 0.85,
                    "text": match.group(0)
                })
        return results

    def _fallback_regex_redact(self, text: str, mask_accounts: bool = True) -> str:
        s = text
        s = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "<EMAIL_REDACTED>", s)
        s = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "<PHONE_REDACTED>", s)
        s = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "<CREDIT_CARD_REDACTED>", s)
        s = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<IP_REDACTED>", s)
        if mask_accounts:
            s = re.sub(r"\b([CM]\d{3})\d{2,6}(\d{3})\b", r"\1***\2", s)
        return s


# Global singleton instance
pii_protector = FinancialPIIProtector()
