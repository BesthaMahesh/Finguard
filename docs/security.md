# FinGuard Security, Governance & Trust Layer Architecture

## 1. Authentication & Session Management
- **Protocol**: JSON Web Token (JWT) bearer authentication utilizing HS256 algorithm with configurable secret rotation.
- **Expiration**: Standard 8-hour session validity.
- **Credential Storage**: Cryptographic SHA-256 password hashing.

## 2. Server-Side Role-Based Access Control (RBAC)
FinGuard enforces strict role permissions on the FastAPI server before dispatching any operation:

| Permission | Analyst | Investigator | Auditor | Administrator |
| :--- | :---: | :---: | :---: | :---: |
| `view_transactions` | YES | YES | YES | YES |
| `run_risk_analysis` | YES | YES | NO | YES |
| `create_case` | YES | YES | NO | YES |
| `update_disposition` | NO | **YES** | NO | **YES** |
| `view_audit_trail` | NO | NO | **YES** | **YES** |
| `view_observability` | NO | NO | **YES** | **YES** |
| `system_config` | NO | NO | NO | **YES** |

## 3. Defense-in-Depth Guardrails
1. **PII Masking**: Account numbers (`C1231006815`) are masked as `C123***815` in public exports.
2. **Prompt Injection Defense (`PromptGuard`)**: Sanitizes incoming user queries to AI assistants to prevent jailbreaks, prompt injection, and unauthorized data exfiltration attempts.
3. **4-Eyes Review Principle**: Severe actions (`FREEZE_ACCOUNT`, `ESCALATE_TO_SAR`) require documented investigator notes and authorized reviewer role verification.
4. **Immutable Audit Trail**: All case creations, risk evaluations, and reviews are captured in `AuditEvent` records with cryptographic UUID correlation IDs.
