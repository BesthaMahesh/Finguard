import json
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.db.models import Conversation, ConversationMessage, generate_uuid
from backend.rag.retriever import PolicyRetriever
from backend.security.prompt_guard import PromptGuard
from backend.agents.llm_client import llm_client
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

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
    title = payload.get("title", "New Inquiry").strip() or "New Inquiry"

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
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "text": m.text,
                "citations": json.loads(m.citations_json) if m.citations_json else [],
                "tokens_used": m.tokens_used,
                "latency_ms": m.latency_ms,
                "timestamp": m.created_at.isoformat() if m.created_at else None
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
    Deletes conversation and associated messages.
    """
    check_permission(current_user["role"], "ask_ai_assistant")
    user_id = current_user.get("username") or current_user.get("user_id")

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if conv.user_id != user_id and current_user["role"].upper() not in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(status_code=403, detail="Access forbidden: You cannot delete another user's conversation.")

    db.delete(conv)
    db.commit()
    return {"status": "DELETED", "id": conversation_id}

@router.post("/chat")
def chat_with_risk_assistant(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "ask_ai_assistant")
    t0 = time.time()
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
        # Create a new conversation container with concise question title
        title = message[:40] + ("..." if len(message) > 40 else "")
        conv = Conversation(id=generate_uuid(), user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 1. Prompt Injection Defense
    is_safe, guard_msg = PromptGuard.check_prompt(message)
    if not is_safe:
        reply_blocked = f"Security Notice: Your query triggered enterprise prompt guardrails ({guard_msg}). Unauthorized system instructions or bypass attempts are blocked and logged."
        # Persist blocked attempt
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

    # 2. Policy-Grounded RAG Retrieval (with in-memory cache & singleton embedder)
    citations = PolicyRetriever.search_policies(query=message, top_k=2)
    context_str = "\n\n".join(
        [f"[{c['document_id']} | {c['section']}]: {c['excerpt']}" for c in citations]
    )

    # 3. LLM Reasoning via Groq with structured prompt
    system_prompt = (
        "You are FinGuard AI Risk Assistant, an enterprise copilot for financial crime analysts and investigators.\n"
        "Guidelines:\n"
        "1. Strictly ground your response in the provided compliance and policy guidelines.\n"
        "2. Format your response cleanly in GitHub-flavored Markdown using section headings (###), bullet points (- ), and bold highlights (**).\n"
        "3. If the policy context does not contain the answer, explicitly state that verified policy guidance is unavailable.\n"
        "4. Cite policy documents (e.g., AML-04, POL-FRAUD-2024-01, RBI KYC Guidelines) where applicable.\n"
        "5. Never state that an individual or transaction is a definitively proven crime. Maintain neutral, objective risk terminology."
    )

    user_prompt = (
        f"User Query: {message}\n\n"
        f"Retrieved Policy Evidence:\n{context_str or 'No direct policy matching this specific query found in index.'}\n\n"
        f"Provide a structured, authoritative answer for the risk analyst:"
    )

    llm_resp = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=600)
    reply_text = llm_resp.get("content", "").strip()

    if not reply_text:
        if citations:
            reply_text = (
                f"### Compliance Policy Guidance ({citations[0]['document_id']} — {citations[0]['section']})\n\n"
                f"{citations[0]['excerpt']}\n\n"
                "- **Human Oversight**: Investigators must follow the 4-Eyes principle for any transaction scoring above the 70.0 risk threshold.\n"
                "- **Next Step**: Corroborate counterparty beneficiary details in the transaction ledger."
            )
        else:
            reply_text = (
                "### Insufficient Policy Evidence\n\n"
                "No indexed compliance procedure directly covers this specific query. "
                "Please consult the Financial Crimes Intelligence Manual or file an inquiry with the Chief Risk Office."
            )

    elapsed_ms = round((time.time() - t0) * 1000.0, 2)
    tokens = llm_resp.get("tokens_used", 0)

    # Persist user question and assistant answer in the database
    u_msg = ConversationMessage(
        conversation_id=conv.id,
        sender="user",
        text=message
    )
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
        "model": llm_resp.get("model", "qwen/qwen3.8-27b"),
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
    Streaming SSE endpoint for progressive token generation.
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

    # 2. Retrieval
    citations = PolicyRetriever.search_policies(query=message, top_k=2)
    context_str = "\n\n".join(
        [f"[{c['document_id']} | {c['section']}]: {c['excerpt']}" for c in citations]
    )

    system_prompt = (
        "You are FinGuard AI Risk Assistant, an enterprise copilot for financial crime analysts and investigators.\n"
        "Strictly ground your response in the provided compliance and policy guidelines."
    )
    user_prompt = f"User Query: {message}\n\nEvidence:\n{context_str}\n\nProvide authoritative answer:"

    def event_generator():
        yield f"event: citations\ndata: {json.dumps({'citations': citations, 'conversation_id': conv.id})}\n\n"
        collected_reply = []
        for token in llm_client.stream_completion(system_prompt=system_prompt, user_prompt=user_prompt):
            collected_reply.append(token)
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        full_text = "".join(collected_reply).strip()
        yield f"event: done\ndata: {json.dumps({'conversation_id': conv.id, 'status': 'SUCCESS'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
