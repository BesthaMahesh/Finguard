export type UserRole = 'USER' | 'ADMIN' | 'analyst' | 'investigator' | 'auditor' | 'administrator';

export interface UserProfile {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface UserManagementItem {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export interface Transaction {
  id: number;
  step: number;
  type: string;
  amount: number;
  name_orig: string;
  old_balance_org: number;
  new_balance_orig: number;
  name_dest: string;
  old_balance_dest: number;
  new_balance_dest: number;
  is_fraud: number;
  is_flagged_fraud: number;
  predicted_fraud?: number;
  fraud_probability?: number;
  risk_score?: number;
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status?: string;
  rule_flags?: any;
  feature_contributions?: any;
  investigation?: {
    id: string;
    case_number: string;
    title: string;
    status: string;
    priority: string;
    assigned_to: string;
    disposition?: string;
    disposition_notes?: string;
    reviewed_by?: string;
    created_at?: string;
  } | null;
  audit_history?: Array<{
    id: string;
    action: string;
    actor_id: string;
    actor_role: string;
    outcome: string;
    timestamp?: string;
  }>;
  created_at?: string;
}

export interface RuleViolation {
  rule_id: string;
  name: string;
  description?: string;
  severity?: string;
  penalty: number;
}

export interface FeatureContribution {
  feature_name: string;
  display_name: string;
  feature_value: number;
  shap_value?: number;
  impact: 'INCREASES_RISK' | 'DECREASES_RISK';
  absolute_impact: number;
}

export interface PolicyCitation {
  document_id: string;
  document_title: string;
  section: string;
  source_file?: string;
  excerpt: string;
  relevance_score: number;
}

export interface AgentTimelineStep {
  agent: string;
  status: string;
  duration_ms: number;
  output_summary: string;
  timestamp: string;
}

export interface InvestigationCase {
  id: string;
  case_number: string;
  transaction_id: number;
  title: string;
  status: 'OPEN' | 'IN_REVIEW' | 'ESCALATED' | 'CLOSED_RESOLVED' | 'CLOSED_FALSE_POSITIVE';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  assigned_to: string;
  risk_score: number;
  summary: string;
  model_features_json?: string;
  policy_citations_json?: string;
  agent_workflow_trace_json?: string;
  disposition?: string;
  disposition_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  created_at: string;
}

export interface DashboardSummary {
  total_transactions_processed: number;
  transactions_flagged_for_review: number;
  historical_dataset_fraud_count: number;
  historical_fraud_rate_pct: number;
  open_investigation_cases: number;
  total_audit_events: number;
  risk_level_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  transaction_type_breakdown: Array<{
    type: string;
    count: number;
    total_volume: number;
    historical_fraud_count: number;
    avg_risk_score: number;
  }>;
  temporal_volume_timeline: Array<{
    hour: number;
    transaction_volume: number;
    detected_anomalies: number;
  }>;
  dataset_freshness: string;
  active_model_version: string;
}

export interface ModelEvaluation {
  model_version: string;
  algorithm: string;
  trained_at: string;
  test_sample_count: number;
  test_fraud_count: number;
  pr_auc: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  threshold: number;
  confusion_matrix: {
    true_negatives: number;
    false_positives: number;
    false_negatives: number;
    true_positives: number;
  };
  feature_importance: Array<{
    feature: string;
    importance: number;
  }>;
  threshold_analysis: Array<{
    threshold: number;
    precision: number;
    recall: number;
    f1_score: number;
  }>;
}

export interface AuditEvent {
  id: string;
  correlation_id: string;
  actor_id: string;
  actor_role: string;
  action: string;
  target_type: string;
  target_id: string;
  outcome: string;
  details_json: string;
  timestamp: string;
}

export interface ObservabilitySummary {
  total_requests?: number;
  total_errors?: number;
  error_rate_pct?: number;
  avg_api_latency_ms?: number;
  p95_api_latency_ms?: number;
  avg_ml_inference_ms?: number;
  total_agent_workflows?: number;
  avg_agent_workflow_ms?: number;
  total_tokens_used?: number;
  estimated_llm_cost_usd?: number;
  slo_targets?: {
    api_latency_slo_ms: number;
    availability_slo_pct: number;
    status: string;
  };
  active_model_version: string;
  telemetry_status: string;
  otel_service_name: string;
  access_tier?: string;
  service_status?: string;
  notice?: string;
  recent_traces: Array<{
    trace_id: string;
    span_id: string;
    name: string;
    duration_ms: number;
    status: string;
    attributes: Record<string, any>;
    timestamp: string;
  }>;
}

export interface KnowledgeDocItem {
  id: string;
  doc_id: string;
  title: string;
  category: string;
  version: string;
  chunk_count: number;
  page_count: number;
  character_count: number;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  source_type: string;
  content_hash?: string;
  status: string;
  ingested_at?: string;
}

export interface KnowledgeManifestStatus {
  status: string;
  chroma_collection: string;
  embedding_model: string;
  manifest: {
    total_discovered: number;
    total_indexed: number;
    total_skipped: number;
    total_failed: number;
    total_chunks: number;
    last_updated: string;
    categories: string[];
    file_types: string[];
  };
}

export interface KnowledgeSearchResponse {
  query: string;
  has_evidence: boolean;
  results_count: number;
  citations: Array<{
    document_id: string;
    document_title: string;
    category: string;
    source_type: string;
    file_type: string;
    source_file: string;
    page_number?: number;
    section: string;
    citation_location: string;
    excerpt: string;
    full_text: string;
    relevance_score: number;
  }>;
  synthesis?: string;
}

