from typing import TypedDict, Dict, Any, List, Optional
from datetime import datetime

class AgentTimelineStep(TypedDict):
    agent: str
    status: str
    duration_ms: float
    output_summary: str
    timestamp: str

class InvestigationState(TypedDict):
    # Workflow Execution State
    correlation_id: str
    transaction_id: Optional[int]
    raw_transaction_data: Dict[str, Any]
    user_query: Optional[str]
    current_user_role: str
    
    # Agent Outputs
    intake_status: str
    validated_transaction: Dict[str, Any]
    data_quality_report: Dict[str, Any]
    
    model_prediction: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    investigation_evidence: Dict[str, Any]
    policy_citations: List[Dict[str, Any]]
    explanation_summary: str
    feature_attributions: List[Dict[str, Any]]
    
    # Governance & Routing
    workflow_next_step: str
    requires_human_review: bool
    review_checkpoint_reason: Optional[str]
    final_report: Dict[str, Any]
    
    # Audit & Observability
    timeline: List[AgentTimelineStep]
    tokens_consumed: int
    error: Optional[str]
