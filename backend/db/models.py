from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.db.session import Base
import uuid
import hashlib

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), default="analyst", nullable=False)  # analyst, investigator, auditor, administrator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer, nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN
    amount = Column(Float, nullable=False)
    name_orig = Column(String(40), nullable=False, index=True)
    old_balance_org = Column(Float, nullable=False)
    new_balance_orig = Column(Float, nullable=False)
    name_dest = Column(String(40), nullable=False, index=True)
    old_balance_dest = Column(Float, nullable=False)
    new_balance_dest = Column(Float, nullable=False)
    is_fraud = Column(Integer, default=0, nullable=False)  # Ground-truth dataset label
    is_flagged_fraud = Column(Integer, default=0, nullable=False)
    
    # Model & Risk inference fields (dynamically evaluated or persisted)
    predicted_fraud = Column(Integer, nullable=True)
    fraud_probability = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)  # 0 to 100
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), default="UNREVIEWED")  # UNREVIEWED, UNDER_INVESTIGATION, CLEARED, ESCALATED, CONFIRMED_FRAUD
    rule_flags = Column(Text, nullable=True)  # JSON list of triggered rule IDs
    created_at = Column(DateTime, default=utc_now)

    investigation_cases = relationship("InvestigationCase", back_populates="transaction")

    __table_args__ = (
        Index("idx_tx_type_amount", "type", "amount"),
        Index("idx_tx_risk_level", "risk_level"),
    )

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_number = Column(String(30), unique=True, nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(30), default="OPEN")  # OPEN, IN_REVIEW, ESCALATED, CLOSED_RESOLVED, CLOSED_FALSE_POSITIVE
    priority = Column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to = Column(String(50), default="agent_system")
    risk_score = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    model_features_json = Column(Text, nullable=True)
    policy_citations_json = Column(Text, nullable=True)
    agent_workflow_trace_json = Column(Text, nullable=True)
    disposition = Column(String(50), nullable=True)  # ESCALATE_TO_SAR, FREEZE_ACCOUNT, REQUEST_ADDITIONAL_KYC, DISMISS_FALSE_POSITIVE
    disposition_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(50), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="investigation_cases")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    correlation_id = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(50), nullable=False, index=True)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(60), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(50), nullable=False)
    outcome = Column(String(20), default="SUCCESS")  # SUCCESS, FAILURE, DENIED
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    policy_version_applied = Column(String(30), nullable=True)
    event_hash = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    doc_id = Column(String(60), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # AML, KYC, FRAUD_TYPOLOGY, SANCTIONS, INTERNAL_POLICY
    version = Column(String(20), default="1.0")
    status = Column(String(30), default="ACTIVE")  # ACTIVE, SUPERSEDED, EXPIRED
    effective_from = Column(String(20), nullable=True)
    effective_to = Column(String(20), nullable=True)
    jurisdiction = Column(String(30), default="GLOBAL")
    approval_status = Column(String(30), default="APPROVED")
    supersedes_version = Column(String(20), nullable=True)
    content_hash = Column(String(64), nullable=True)
    classification = Column(String(30), default="INTERNAL")
    document_access_scope = Column(String(30), default="ALL")
    chunk_count = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    ingested_at = Column(DateTime, default=utc_now)

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_version = Column(String(40), unique=True, nullable=False)
    algorithm = Column(String(100), nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    dataset_rows = Column(Integer, default=0)
    fraud_instances = Column(Integer, default=0)
    pr_auc = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    threshold = Column(Float, default=0.65)
    confusion_matrix_json = Column(Text, nullable=False)
    feature_importance_json = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # 'user' or 'assistant'
    text = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

