# FinGuard PII Handling & Data Privacy Architecture

**Module:** `backend/security/pii_protection.py`  
**Core Technologies:** Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`), Regex Fallback Engines  
**Regulatory Standards:** GDPR (Art. 25, 32), PCI-DSS v4.0, ISO/IEC 27001:2022 (A.8.11)  
**Document Version:** 1.0.0  

---

## 1. Overview & Privacy Principles

Financial crime risk intelligence systems must balance two competing imperatives:
1. **Investigative Utility:** Fraud analysts require accurate account numbers and counterparties to investigate money laundering and account takeovers.
2. **Data Minimization & Privacy:** Raw customer personal data (names, email addresses, phone numbers, tax IDs) must never be transmitted needlessly to third-party cloud LLMs or exposed in public logs.

FinGuard implements **Defense-in-Depth Privacy by Design**:
* Customer PII is scrubbed before prompt submission to cloud LLMs (Groq).
* Transaction account identifiers are masked as `C123***815` in telemetry and exported dockets.
* A cryptographic **Tokenization Vault** allows authorized investigators to reversibly resolve redacted entities when justified under an audited 4-Eyes workflow.

---

## 2. Supported PII Entity Recognizers

FinGuard combines standard Presidio Named Entity Recognition (NER) models with specialized banking pattern recognizers:

| Entity Type | Recognition Engine | Sample Pattern / Example | Default Anonymization Format |
| :--- | :--- | :--- | :--- |
| **FINANCIAL_ACCOUNT** | Custom FinGuard PatternRecognizer | `C1234567890`, `M9876543210` | Masked: `C123***890` or `<FINANCIAL_ACCOUNT>` |
| **IBAN_CODE** | Custom FinGuard PatternRecognizer | `GB82WEST12345698765432` | `<IBAN_CODE>` |
| **SWIFT_BIC** | Custom FinGuard PatternRecognizer | `CHASUS33XXX`, `DEUTDEFF` | `<SWIFT_BIC>` |
| **CRYPTO_WALLET** | Custom FinGuard PatternRecognizer | `0x71C...`, `1A1zP1...` | `<CRYPTO_WALLET>` |
| **EMAIL_ADDRESS** | Microsoft Presidio Standard | `john.doe@example.com` | `<EMAIL_ADDRESS>` |
| **PHONE_NUMBER** | Microsoft Presidio + Phonenumbers | `+1-555-839-2019` | `<PHONE_NUMBER>` |
| **PERSON** | Presidio spaCy NER | `Johnathan Smith` | `<PERSON>` |
| **IP_ADDRESS** | Microsoft Presidio Standard | `192.168.1.1` | `<IP_ADDRESS>` |
| **CREDIT_CARD** | Microsoft Presidio Luhn Check | `4532-XXXX-XXXX-1234` | `<CREDIT_CARD>` |
| **US_SSN** | Microsoft Presidio Standard | `XXX-XX-1234` | `<US_SSN>` |

---

## 3. Workflow Integration Architecture

```
[User Query / API Input]
         │
         ▼
[pii_protector.analyze_pii()]
         │
         ▼
[pii_protector.redact_pii()] ──────► (Optional: Token Vault for Reversible Lookup)
         │
         ├─► [PromptGuard Untrusted Context Sandbox]
         ├─► [Groq Cloud LLM Completion API] (Zero-Retention Safe)
         └─► [OpenTelemetry & AuditEvent Logger] (PII-Clean Logs)
```

### 3.1 LLM Request Path
Before any prompt payload is constructed for external model inference in `llm_client.py` or `assistant.py`, user prompts and retrieved context excerpts are passed through `pii_protector.redact_pii()`.

### 3.2 Audit Logging & Telemetry
In `backend/agents/audit_reporter.py` and `backend/observability/logger.py`, structured logs pass through `pii_protector.sanitize_dictionary()`. Account numbers are replaced with non-invertible masked strings (`C123***815`).

### 3.3 Reversible Tokenization Vault
When an investigation requires that an account identifier be tracked through multi-turn agent reasoning:
```python
redacted_text = pii_protector.redact_pii(raw_text, preserve_in_vault=True)
# Outputs token: <FINANCIAL_ACCOUNT_829102>

# Authorized unmasking (Investigator or Administrator role required):
original_text = pii_protector.restore_vault_tokens(redacted_text, user_role=current_user["role"])
```

### 3.4 Fallback Safety
If Microsoft Presidio encounters an internal exception (e.g. spaCy model failure or memory constraints), the system automatically falls back to deterministic regex masking and **never** emits raw unredacted text into system logs.
