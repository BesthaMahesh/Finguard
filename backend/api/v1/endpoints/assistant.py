"""
FinGuard AI Risk Assistant & Investigation Copilot Endpoint.
Implements:
- User Ownership Isolation for Conversations & Messages
- Presidio PII Redaction on Inbound Queries and Evidence
- PromptGuard Injection & Delimiter Neutralization
- Request Decomposition for Multi-Step Transaction Investigations
- Temporal Versioned Policy Grounding
- Secure Streaming (SSE) with Equivalent Security Checks
"""

import json
import re
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.db.models import Conversation, ConversationMessage, Transaction, generate_uuid
from backend.rag.retriever import PolicyRetriever
from backend.security.prompt_guard import PromptGuard
from backend.security.pii_protection import pii_protector
from backend.agents.llm_client import llm_client
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission
from backend.graphs.investigation_graph import execute_investigation

router = APIRouter(prefix="/assistant", tags=["AI Risk Assistant"])

@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns authenticated user's conversations, enforcing user ownership isolation.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    convs = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(desc(Conversation.updated_at)).all()

    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "message_count": len(c.messages),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in convs
        ]
    }

@router.post("/conversations")
def create_new_conversation(
    payload: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Creates a new conversation container scoped to the authenticated user.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")
    raw_title = payload.get("title", "New Inquiry").strip() or "New Inquiry"
    title = pii_protector.redact_pii(raw_title)[:100]

    conv = Conversation(
        id=generate_uuid(),
        user_id=user_id,
        title=title
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat() if conv.created_at else None
    }

@router.get("/conversations/{conversation_id}")
def get_conversation_history(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns chronologically ordered messages for a conversation.
    Strictly verifies user ownership.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if conv.user_id != user_id and current_user["role"].upper() not in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot access conversations owned by other users."
        )

    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "text": m.text,
                "citations": json.loads(m.citations_json) if m.citations_json else [],
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in conv.messages
        ]
    }

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes conversation container and messages, verifying ownership.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if conv.user_id != user_id and current_user["role"].upper() not in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot delete conversations owned by other users."
        )

    db.delete(conv)
    db.commit()
    return {"status": "DELETED", "id": conversation_id}

@router.post("/chat")
def chat_with_risk_assistant(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Core AI Risk Assistant chat endpoint.
    Supports complex request decomposition:
    If inquiry requests check on a specific transaction (e.g. TX-1001 or transaction 1),
    routes through the LangGraph multi-agent investigation workflow with temporal policy retrieval.
    """
    t0 = time.time()
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = payload.get("conversation_id")
    conv = None
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv and conv.user_id != user_id and current_user["role"].upper() not in ("ADMIN", "ADMINISTRATOR"):
            raise HTTPException(status_code=403, detail="Access forbidden: You cannot write to another user's conversation.")

    if not conv:
        title = message[:40] + ("..." if len(message) > 40 else "")
        conv = Conversation(id=generate_uuid(), user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 1. Prompt Injection Defense
    is_safe, guard_msg = PromptGuard.check_prompt(message)
    if not is_safe:
        reply_blocked = (
            f"Security Notice: Your query triggered enterprise prompt guardrails ({guard_msg}). "
            f"Unauthorized system instructions or bypass attempts are blocked and logged."
        )
        u_msg = ConversationMessage(conversation_id=conv.id, sender="user", text=message)
        a_msg = ConversationMessage(conversation_id=conv.id, sender="assistant", text=reply_blocked, tokens_used=0)
        db.add_all([u_msg, a_msg])
        db.commit()
        return {
            "reply": reply_blocked,
            "citations": [],
            "conversation_id": conv.id,
            "status": "BLOCKED_GUARDRAIL",
            "latency_ms": round((time.time() - t0) * 1000.0, 2)
        }

    # 2. Decomposed Request Routing for Transaction Investigations
    # Matches patterns like "TX-1001", "transaction 1", "check tx #250"
    tx_match = re.search(r"\b(?:tx|transaction)[-_\s#]*([0-9]+)\b", message, re.IGNORECASE)
    if tx_match:
        target_tx_id = int(tx_match.group(1))
        # Validate that transaction exists and user has view_transactions permission
        check_permission(current_user["role"], "view_transactions")
        tx_record = db.query(Transaction).filter_by(id=target_tx_id).first()

        if tx_record:
            # Execute full multi-agent decomposed workflow
            investigation_state = execute_investigation(
                transaction_id=target_tx_id,
                user_query=message,
                user_role=current_user["role"]
            )
            final_report = investigation_state.get("final_report", {})
            citations = investigation_state.get("policy_citations", [])
            narrative = investigation_state.get("explanation_summary", "")
            risk_info = investigation_state.get("risk_assessment", {})
            requires_hr = investigation_state.get("requires_human_review", False)
            corr_id = investigation_state.get("correlation_id", "")

            # Compose structured response
            reply_lines = [
                f"### Automated Multi-Agent Risk Assessment: Transaction #{target_tx_id}\n",
                f"**Composite Risk Score:** `{risk_info.get('composite_risk_score', 0)}/100` ({risk_info.get('operational_risk_level', 'UNREVIEWED')})\n",
                f"**Transaction Overview:** Type: `{tx_record.type}`, Amount: `${tx_record.amount:,.2f}`, Origin: `{pii_protector.mask_financial_account(tx_record.name_orig)}`\n",
                f"\n#### Investigative Findings:\n{narrative}\n",
                f"\n#### Governance & Human Review Disposition:\n",
                f"- **Human Review Required:** `{'YES - Mandatory Review Checkpoint' if requires_hr else 'NO - Routine Low Risk'}`\n",
                f"- **Checkpoint Reason:** {investigation_state.get('review_checkpoint_reason') or 'Standard threshold protocol'}\n",
                f"- **Investigation Trace ID:** `{corr_id}`\n"
            ]
            if citations:
                reply_lines.append(f"\n#### Applicable Governing Policies:\n")
                for c in citations[:3]:
                    reply_lines.append(f"- **{c.get('document_title')}** ({c.get('source_file')}, v{c.get('version', '1.0')}): {c.get('citation_location')}\n")

            reply_text = "".join(reply_lines)
            elapsed_ms = round((time.time() - t0) * 1000.0, 2)

            u_msg = ConversationMessage(conversation_id=conv.id, sender="user", text=message)
            a_msg = ConversationMessage(
                conversation_id=conv.id,
                sender="assistant",
                text=reply_text,
                citations_json=json.dumps(citations),
                tokens_used=investigation_state.get("tokens_consumed", 0),
                latency_ms=elapsed_ms
            )
            db.add_all([u_msg, a_msg])
            db.commit()

            return {
                "reply": reply_text,
                "citations": citations,
                "conversation_id": conv.id,
                "trace_id": corr_id,
                "requires_human_review": requires_hr,
                "status": "DECOMPOSED_WORKFLOW_COMPLETE",
                "latency_ms": elapsed_ms
            }

    # 3. Standard Policy-Grounded RAG Retrieval with PII Redaction
    safe_query = pii_protector.redact_pii(message)
    citations = PolicyRetriever.search_policies(
        query=safe_query,
        top_k=3,
        user_role=current_user["role"]
    )

    sandboxed_context = [
        PromptGuard.wrap_untrusted_context(c["excerpt"], source_label=f"{c['document_id']} ({c['section']}, v{c.get('version', '1.0')})")
        for c in citations
    ]
    context_str = "\n\n".join(sandboxed_context)

    # 4. LLM Reasoning via Groq with structured prompt
    system_prompt = (
        "You are FinGuard AI Risk Assistant, an enterprise copilot for financial crime analysts and investigators.\n"
        "Guidelines:\n"
        "1. Strictly ground your response in the provided compliance and policy guidelines.\n"
        "2. Format your response cleanly in GitHub-flavored Markdown using section headings (###), bullet points (- ), and bold highlights (**).\n"
        "3. If the policy context does not contain the answer, explicitly state that verified policy guidance is unavailable.\n"
        "4. Cite policy documents (e.g., AML-04, POL-FRAUD-2024-01, RBI KYC Guidelines, v1.0) where applicable.\n"
        "5. Never state that an individual or transaction is a definitively proven crime. Maintain neutral, objective risk terminology."
    )

    user_prompt = (
        f"User Query: {safe_query}\n\n"
        f"Retrieved Policy Evidence:\n{context_str or 'No direct policy matching this specific query found in index.'}\n\n"
        f"Provide a structured, authoritative answer for the risk analyst:"
    )

    llm_resp = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=600)
    reply_text = llm_resp.get("content", "").strip()

    if not reply_text:
        if citations:
            top_c = citations[0]
            sec = top_c.get("section", "Standard Compliance Guidance")
            doc = top_c.get("document_id", "POLICY")
            ver = top_c.get("version", "1.0")
            src = top_c.get("source_file", "Official Manual")
            full_text = top_c.get("full_text", top_c.get("excerpt", "")).strip()

            lines = [
                f"### Grounded Compliance Guidance: {sec}\n",
                f"**Governing Policy:** `{doc}` (Version {ver}, `{src}`)\n",
                f"{full_text}\n\n",
                f"> **Operational Principle:** Model-generated risk scores serve strictly as non-autonomous decision support alerts. Final disposition requires review and sign-off by an authorized human investigator."
            ]
            reply_text = "\n".join(lines)
        else:
            reply_text = (
                "### Insufficient Policy Evidence\n\n"
                "No indexed compliance procedure directly covers this specific query. "
                "Please consult the Financial Crimes Intelligence Manual or file an inquiry with the Chief Risk Office."
            )

    elapsed_ms = round((time.time() - t0) * 1000.0, 2)
    tokens = llm_resp.get("tokens_used", 0)

    u_msg = ConversationMessage(conversation_id=conv.id, sender="user", text=message)
    a_msg = ConversationMessage(
        conversation_id=conv.id,
        sender="assistant",
        text=reply_text,
        citations_json=json.dumps(citations),
        tokens_used=tokens,
        latency_ms=elapsed_ms
    )
    db.add_all([u_msg, a_msg])
    db.commit()

    return {
        "reply": reply_text,
        "citations": citations,
        "conversation_id": conv.id,
        "llm_provider": llm_resp.get("provider", "groq"),
        "latency_ms": elapsed_ms,
        "tokens_used": tokens,
        "status": "SUCCESS"
    }

@router.post("/stream")
def stream_risk_assistant(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Streaming SSE endpoint enforcing the exact same authentication,
    PromptGuard sanitization, and PII protection as the standard chat endpoint.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = payload.get("conversation_id")
    conv = None
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv and conv.user_id != user_id and current_user["role"].upper() not in ("ADMIN", "ADMINISTRATOR"):
            raise HTTPException(status_code=403, detail="Access forbidden.")

    if not conv:
        title = message[:40] + ("..." if len(message) > 40 else "")
        conv = Conversation(id=generate_uuid(), user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 1. Prompt check
    is_safe, guard_msg = PromptGuard.check_prompt(message)
    if not is_safe:
        def err_stream():
            yield f"data: {json.dumps({'error': f'Prompt guardrail triggered: {guard_msg}', 'conversation_id': conv.id})}\n\n"
        return StreamingResponse(err_stream(), media_type="text/event-stream")

    # 2. PII Redaction on user query
    safe_message = pii_protector.redact_pii(message)

    # 3. Retrieval with sandbox delimiter protection
    citations = PolicyRetriever.search_policies(query=safe_message, top_k=2, user_role=current_user["role"])
    sandboxed_context = [
        PromptGuard.wrap_untrusted_context(c["excerpt"], source_label=f"{c['document_id']} (v{c.get('version', '1.0')})")
        for c in citations
    ]
    context_str = "\n\n".join(sandboxed_context)

    system_prompt = (
        "You are FinGuard AI Risk Assistant, an enterprise copilot for financial crime analysts and investigators.\n"
        "Strictly ground your response in the provided compliance and policy guidelines."
    )
    user_prompt = f"User Query: {safe_message}\n\nEvidence:\n{context_str}\n\nProvide authoritative answer:"

    def event_generator():
        yield f"event: citations\ndata: {json.dumps({'citations': citations, 'conversation_id': conv.id})}\n\n"
        for token in llm_client.stream_completion(system_prompt=system_prompt, user_prompt=user_prompt):
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        yield f"event: done\ndata: {json.dumps({'conversation_id': conv.id, 'status': 'SUCCESS'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
