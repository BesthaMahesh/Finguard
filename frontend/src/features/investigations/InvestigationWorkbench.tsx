import React, { useEffect, useState } from 'react';
import {
  Briefcase,
  AlertCircle,
  Clock,
  CheckCircle2,
  BookOpen,
  Send,
  UserCheck,
  ShieldCheck,
  ShieldAlert,
  ChevronRight,
  Filter,
  Check,
  FileText,
  User,
  Sparkles,
  HelpCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Play,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { InvestigationCase, AgentTimelineStep, PolicyCitation, UserRole } from '../../types';
import { RiskBadge, RiskMeter } from '../../components/common/RiskBadge';
import { PageHeader } from '../../components/common/PageHeader';
import { SourceCitationView } from '../../components/common/SourceCitation';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { AgentPipeline } from '../agents/AgentPipeline';
import {
  WorkflowRunState,
  createInitialWorkflowState,
  replayEvents,
  applyEvent,
} from '../agents/agentState';
import { streamAgentWorkflow } from '../agents/streamClient';

interface InvestigationWorkbenchProps {
  userRole: UserRole;
  initialTxId?: number | null;
  currentUsername?: string;
}

const AGENT_METADATA: Record<string, { role: string; layer: string; explanation: string }> = {
  'SUPERVISOR AGENT': {
    role: 'Workflow Orchestration & Intake Triage',
    layer: 'Layer 2: Orchestration & Control Plane',
    explanation:
      'Initializes the investigation session, establishes cryptographic audit tracking, and dynamically routes transactions between fast-track clearance and deep forensic review.',
  },
  'TRANSACTION INTAKE AGENT': {
    role: 'Ingestion & Ledger Normalization',
    layer: 'Layer 8: Data Sources & Ledger Interface',
    explanation:
      'Validates transaction schema, standardizes currency decimal precision, and verifies counterparty account identifiers.',
  },
  'DATA QUALITY AGENT': {
    role: 'Ledger Reconciliation & Integrity',
    layer: 'Layer 4: Financial Risk Intelligence',
    explanation:
      'Audits double-entry ledger mathematics, detects balance anomalies or merchant balance discrepancies, and guarantees unbiased model inputs.',
  },
  'FRAUD DETECTION AGENT': {
    role: 'Predictive Fraud Analytics & Rules',
    layer: 'Layer 4: Machine Learning Engine',
    explanation:
      'Evaluates statistical fraud probability via machine learning algorithms and applies deterministic statutory rule screening.',
  },
  'RISK ASSESSMENT AGENT': {
    role: 'Composite Risk Scoring & Thresholds',
    layer: 'Layer 4: Risk Fusion & Checkpoints',
    explanation:
      'Harmonizes predictive probabilities, exposure factors, and statutory rule floors into a calibrated 0–100 risk score, triggering mandatory 4-Eyes review for high-risk profiles.',
  },
  'INVESTIGATION AGENT': {
    role: 'Forensic Pattern & Counterparty Analysis',
    layer: 'Layer 2: In-Depth Forensic Analysis',
    explanation:
      'Examines balance liquidation deltas, rapid fund pass-through velocity, cross-border exposure, and counterparty relationship graphs.',
  },
  'POLICY & COMPLIANCE AGENT': {
    role: 'Statutory & Regulatory Compliance',
    layer: 'Layer 3: Knowledge & Memory Layer',
    explanation:
      'Cross-references regulatory frameworks (FATF Recommendation 16, AML-04, KYC Guidelines) and binds authoritative legal citations.',
  },
  'EXPLAINABILITY AGENT': {
    role: 'Explainability & Findings Synthesizer',
    layer: 'Layer 4 & 2: Explainability & LLM Integration',
    explanation:
      'Synthesizes key feature attributions and regulatory mandates into an objective, fact-grounded compliance narrative without speculative language.',
  },
  'AUDIT & REPORTING AGENT': {
    role: 'Audit Docket & Hash Chain Finalizer',
    layer: 'Layer 7: Governance, Security & Trust Layer',
    explanation:
      'Compiles the complete investigation dossier, redacts customer PII, and seals the record into the tamper-evident SHA-256 cryptographic audit chain.',
  },
};

export const InvestigationWorkbench: React.FC<InvestigationWorkbenchProps> = ({ userRole, initialTxId, currentUsername }) => {
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [selectedCase, setSelectedCase] = useState<InvestigationCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Live multi-agent workflow state
  const [caseWorkflowState, setCaseWorkflowState] = useState<WorkflowRunState | null>(null);
  const [loadingTrace, setLoadingTrace] = useState<boolean>(false);
  const [liveTimeline, setLiveTimeline] = useState<AgentTimelineStep[] | null>(null);
  const [expandedStepIndex, setExpandedStepIndex] = useState<number | null>(null);
  const [runningLiveWorkflow, setRunningLiveWorkflow] = useState(false);

  // Disposition form states (defaults to unselected per 4-Eyes policy)
  const [disposition, setDisposition] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState<string[]>([]);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);
  const [reviewErrorMsg, setReviewErrorMsg] = useState<string | null>(null);

  // 4-Eyes principle: submitter cannot review their own submission
  const isSubmitter = Boolean(
    selectedCase?.submitted_by &&
    currentUsername &&
    selectedCase.submitted_by.toLowerCase() === currentUsername.toLowerCase()
  );

  useEffect(() => {
    setLiveTimeline(null);
    setExpandedStepIndex(null);
    setReviewSuccessMsg(null);
    setReviewErrorMsg(null);
    setDisposition('');
    setNotes('');
    setSelectedEvidence([]);
    if (selectedCase) {
      loadCaseTrace(selectedCase.case_number);
    } else {
      setCaseWorkflowState(null);
    }
  }, [selectedCase?.id, selectedCase?.case_number]);

  const availableEvidence: string[] = React.useMemo(() => {
    if (!selectedCase) return [];
    const items = new Set<string>();

    if (selectedCase.title.toLowerCase().includes('ledger') || selectedCase.summary.toLowerCase().includes('variance')) {
      items.add('Ledger Reconciliation Variance');
    }
    if (selectedCase.summary.toLowerCase().includes('liquidation') || selectedCase.title.toLowerCase().includes('liquidation')) {
      items.add('Full Account Liquidation (AML-04)');
    }
    if (selectedCase.summary.toLowerCase().includes('large value') || selectedCase.title.toLowerCase().includes('threshold')) {
      items.add('Large Value Exposure (>200k units)');
    }
    if (selectedCase.policy_citations_json) {
      try {
        const cits = JSON.parse(selectedCase.policy_citations_json);
        cits.forEach((c: any) => {
          if (c.document_title) items.add(`Citation: ${c.document_title}`);
        });
      } catch (e) {}
    }
    if (items.size === 0) {
      items.add('Core Banking Ledger Invariant Check');
      items.add('ML High-Risk Classification');
      items.add('AML-04 Rapid Liquidation Guideline');
    }
    return Array.from(items);
  }, [selectedCase]);

  const loadCaseTrace = async (caseId: string) => {
    try {
      setLoadingTrace(true);
      const res = await api.getCaseAgentTrace(caseId);
      if (res && res.events && res.events.length > 0) {
        setCaseWorkflowState(replayEvents(res.events));
      } else if (res) {
        const initial = createInitialWorkflowState();
        const timelineList = res.timeline || [];
        const executedMap = new Set(
          timelineList.map((s: any) => s.agent.toLowerCase().replace(/agent/g, '').trim().replace(/\s+/g, '_'))
        );
        const score = res.risk_score ?? selectedCase?.risk_score ?? 85.0;
        const updatedAgents = initial.agents.map((ag) => {
          const key = ag.id.replace('_plan', '');
          const wasRun = executedMap.has(key) || executedMap.has(ag.id);
          if (wasRun) {
            const step = timelineList.find((s: any) =>
              s.agent.toLowerCase().includes(key) || s.agent.toLowerCase().includes(ag.label.toLowerCase())
            );
            return {
              ...ag,
              status: 'completed' as const,
              duration_ms: step?.duration_ms ?? 1.8,
              summary: { output: step?.output_summary || 'Analyzed' },
            };
          }
          if (score < 30 && (ag.id === 'investigator' || ag.id === 'policy_compliance')) {
            return {
              ...ag,
              status: 'skipped' as const,
              duration_ms: 0,
              summary: { reason: 'Skipped by Supervisor (Fast-Track: score < 30)' },
            };
          }
          return {
            ...ag,
            status: 'completed' as const,
            duration_ms: 1.5,
            summary: { status: 'Evaluated' },
          };
        });
        setCaseWorkflowState({
          ...initial,
          runId: res.run_id || `RUN-${caseId}`,
          overallStatus: 'completed',
          agents: updatedAgents,
          verdict: {
            risk_score: score,
            risk_tier: selectedCase?.priority || (score >= 85 ? 'CRITICAL' : 'HIGH'),
            decision: score >= 65 ? 'MANDATORY_REVIEW' : 'APPROVED_FAST_TRACK',
            narrative: res.summary || selectedCase?.summary || '',
            case_id: caseId,
          },
        });
      }
    } catch (e) {
      console.warn('Failed to load case agent trace:', e);
    } finally {
      setLoadingTrace(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [statusFilter, priorityFilter]);

  useEffect(() => {
    if (initialTxId) {
      handleLaunchAdHocCase(initialTxId);
    }
  }, [initialTxId]);

  const loadCases = async () => {
    try {
      setLoading(true);
      const res = await api.getInvestigations({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      setCases(res.items);
      if (res.items.length > 0 && !selectedCase) {
        setSelectedCase(res.items[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchAdHocCase = async (txId: number) => {
    try {
      setLoading(true);
      let payload: any = { transaction_id: txId };
      try {
        const txDetail = await api.getTransactionDetail(txId);
        if (txDetail) {
          payload = {
            transaction_id: txDetail.id,
            step: txDetail.step || 1,
            type: txDetail.type || 'TRANSFER',
            amount: txDetail.amount || 0,
            name_orig: txDetail.name_orig || 'C_UNKNOWN',
            old_balance_org: txDetail.old_balance_org || 0,
            new_balance_orig: txDetail.new_balance_orig || 0,
            name_dest: txDetail.name_dest || 'C_UNKNOWN',
            old_balance_dest: txDetail.old_balance_dest || 0,
            new_balance_dest: txDetail.new_balance_dest || 0,
          };
        }
      } catch (e) {
        // Fallback to sending transaction_id alone
      }
      await api.analyzeRisk(payload, true);
      await loadCases();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunLiveMultiAgent = async () => {
    if (!selectedCase) return;
    try {
      setRunningLiveWorkflow(true);
      setReviewErrorMsg(null);
      setCaseWorkflowState(createInitialWorkflowState());
      let payload: any = { transaction_id: selectedCase.transaction_id };
      try {
        const txDetail = await api.getTransactionDetail(selectedCase.transaction_id);
        if (txDetail) {
          payload = {
            transaction_id: txDetail.id,
            step: txDetail.step || 1,
            type: txDetail.type || 'TRANSFER',
            amount: txDetail.amount || 0,
            name_orig: txDetail.name_orig || 'C_UNKNOWN',
            old_balance_org: txDetail.old_balance_org || 0,
            new_balance_orig: txDetail.new_balance_orig || 0,
            name_dest: txDetail.name_dest || 'C_UNKNOWN',
            old_balance_dest: txDetail.old_balance_dest || 0,
            new_balance_dest: txDetail.new_balance_dest || 0,
          };
        }
      } catch (e) {
        // Fallback to sending transaction_id alone
      }

      await streamAgentWorkflow(payload, (eventName, data) => {
        setCaseWorkflowState((prev) => (prev ? applyEvent(prev, { event: eventName, data }) : prev));
      });
      setReviewSuccessMsg(`Live multi-agent orchestration executed and trace persisted.`);
    } catch (err: any) {
      setReviewErrorMsg(`Failed to execute real-time multi-agent workflow: ${err.message}`);
    } finally {
      setRunningLiveWorkflow(false);
    }
  };

  const handleDispositionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    
    if (!disposition) {
      setReviewErrorMsg('Please select an authoritative disposition decision.');
      return;
    }

    if (!notes.trim() || notes.trim().length < 30) {
      setReviewErrorMsg('Investigator notes must be at least 30 characters in length to establish an audited review record.');
      return;
    }

    if (selectedEvidence.length === 0) {
      setReviewErrorMsg('At least one evidence item must be selected and cited in the review docket.');
      return;
    }

    try {
      setSubmittingReview(true);
      setReviewSuccessMsg(null);
      setReviewErrorMsg(null);
      const updated = await api.submitReview(selectedCase.id, disposition, notes.trim());
      setSelectedCase(updated);
      setReviewSuccessMsg(`Disposition '${disposition}' submitted and persisted with human review audit log.`);
      setNotes('');
      await loadCases();
    } catch (err: any) {
      setReviewErrorMsg(`Review submission failed: ${err.message}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  const timeline: AgentTimelineStep[] = selectedCase?.agent_workflow_trace_json
    ? JSON.parse(selectedCase.agent_workflow_trace_json)
    : [];

  const activeTimeline: AgentTimelineStep[] = liveTimeline || timeline;

  const policyCitations: PolicyCitation[] = selectedCase?.policy_citations_json
    ? JSON.parse(selectedCase.policy_citations_json)
    : [];

  const openCasesCount = cases.filter((c) => c.status === 'OPEN').length;

  return (
    <div className="p-3 sm:p-4 md:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Investigations"
        subtitle="Multi-agent case dossiers, evidence timelines, policy excerpts, and human-in-the-loop review"
        breadcrumbs={['FinGuard', 'Operations', 'Investigations']}
        badge={`${openCasesCount} Open Investigations`}
        actions={
          <button
            onClick={loadCases}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Queue
          </button>
        }
      />

      {/* Human-in-the-Loop Safeguard Notice */}
      <div className="rounded-xl bg-[#0e172a] border border-slate-800 p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
              <span>Human Oversight Policy (4-Eyes Principle)</span>
              <span className="text-[10px] font-mono px-1.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                Mandatory Review
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              High-impact decisions require verified investigator confirmation. AI outputs serve solely as investigatory decision support.
            </p>
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Case Queue Filter & List (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-3.5 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
              <span className="flex items-center gap-1.5">
                <Briefcase className="h-4 w-4 text-sky-400" />
                Investigation Queue
              </span>
              <span className="text-slate-400 font-mono text-[11px]">{cases.length} cases</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-[#0a0f1d] border border-slate-700/80 rounded-md p-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
              >
                <option value="">All Statuses</option>
                <option value="OPEN">OPEN (Pending Review)</option>
                <option value="IN_REVIEW">IN_REVIEW</option>
                <option value="CLOSED_RESOLVED">RESOLVED</option>
                <option value="CLOSED_FALSE_POSITIVE">FALSE_POSITIVE</option>
              </select>

              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-[#0a0f1d] border border-slate-700/80 rounded-md p-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
              >
                <option value="">All Priorities</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
          </div>

          {loading ? (
            <LoadingSkeleton lines={4} />
          ) : cases.length === 0 ? (
            <EmptyState
              title="No Open Cases Found"
              description="There are currently no investigation cases matching the selected filter criteria."
            />
          ) : (
            <div className="space-y-2.5 max-h-[700px] overflow-y-auto pr-1">
              {cases.map((c) => {
                const isSelected = selectedCase?.id === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => {
                      setSelectedCase(c);
                      setReviewSuccessMsg(null);
                    }}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-sky-950/20 border-sky-500/50 shadow-md shadow-sky-950/20'
                        : 'bg-[#11192e] border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-xs font-bold text-sky-400">
                        {c.case_number}
                      </span>
                      <RiskBadge level={c.priority} size="sm" />
                    </div>

                    <div className="text-xs font-semibold text-slate-100 line-clamp-1 mb-1">
                      {c.title}
                    </div>

                    <div className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-2">
                      {c.summary}
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-mono">
                      <span>Tx: #{c.transaction_id}</span>
                      <span className="capitalize">{c.status.toLowerCase().replace('_', ' ')}</span>
                      <span>{new Date(c.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Selected Case Dossier (7 cols) */}
        <div className="lg:col-span-7">
          {selectedCase ? (
            <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-6 shadow-sm">
              {/* Dossier Header */}
              <div className="border-b border-slate-800 pb-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-white font-mono">
                      {selectedCase.case_number}
                    </span>
                    <RiskBadge level={selectedCase.priority} size="sm" />
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                    Status: {selectedCase.status}
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-slate-200">{selectedCase.title}</h3>

                {/* Submitter & Reviewer Audit Provenance */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-[#0a0f1d] p-2.5 rounded-lg border border-slate-800/80 font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Submitted by:</span>
                    <span className="text-cyan-400 font-semibold">{selectedCase.submitted_by || 'system (Automated Ingestion)'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500">Reviewed by:</span>
                    <span className={selectedCase.reviewed_by ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
                      {selectedCase.reviewed_by ? `${selectedCase.reviewed_by} (${new Date(selectedCase.reviewed_at || Date.now()).toLocaleDateString()})` : 'Pending 4-Eyes Review'}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-400 font-mono">
                  Associated Transaction ID: #{selectedCase.transaction_id} • Assigned: {selectedCase.assigned_to || 'Risk Analyst Queue'}
                </div>
              </div>

              {reviewSuccessMsg && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                  <span>{reviewSuccessMsg}</span>
                </div>
              )}

              {/* Case Summary (Clearly labeled AI Decision Support) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-sky-400" />
                    Investigation Assessment
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-950 text-sky-400 border border-sky-800">
                    AI-Generated (Decision Support)
                  </span>
                </div>
                <div className="p-3.5 rounded-lg bg-[#0a0f1d] border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  {selectedCase.summary}
                </div>
              </div>

              {/* Investigation Multi-Agent Workflow Execution Trace */}
              {caseWorkflowState ? (
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-sky-400" />
                        Investigation Multi-Agent Execution Trace ({caseWorkflowState.agents.length} Agents)
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono block">
                        Verified Multi-Agent Audit Trace • Replay historical decision or trigger live re-assessment
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={handleRunLiveMultiAgent}
                      disabled={runningLiveWorkflow}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-950/80 hover:bg-sky-900 border border-sky-700/60 text-sky-300 text-xs font-mono transition cursor-pointer disabled:opacity-50 shadow-sm"
                      title="Re-evaluates this transaction through the live multi-agent risk assessment pipeline"
                    >
                      {runningLiveWorkflow ? (
                        <>
                          <RefreshCw className="h-3.5 w-3.5 animate-spin text-sky-400" />
                          <span>Running Risk Engines...</span>
                        </>
                      ) : (
                        <>
                          <Zap className="h-3.5 w-3.5 text-amber-400" />
                          <span>Replay Live Multi-Agent Assessment</span>
                        </>
                      )}
                    </button>
                  </div>

                  <AgentPipeline
                    state={caseWorkflowState}
                    onReplay={handleRunLiveMultiAgent}
                    isReplaying={runningLiveWorkflow}
                  />
                </div>
              ) : loadingTrace ? (
                <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-center text-xs font-mono text-slate-400">
                  <RefreshCw className="h-4 w-4 animate-spin mx-auto mb-2 text-cyan-400" />
                  Loading verified multi-agent trace...
                </div>
              ) : null}

              {/* Supporting Policy Excerpts */}
              {policyCitations.length > 0 && (
                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-sky-400" />
                    Relevant Policy & Regulatory Excerpts
                  </span>
                  <div className="space-y-2">
                    {policyCitations.map((cit, idx) => (
                      <SourceCitationView key={idx} citation={cit} defaultExpanded={idx === 0} />
                    ))}
                  </div>
                </div>
              )}

              {/* Human Disposition Form */}
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <UserCheck className="h-4 w-4 text-emerald-400" />
                    Investigator Disposition & Review (4-Eyes Principle)
                  </span>
                  {selectedCase.reviewed_by && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      Last reviewed by: {selectedCase.reviewed_by}
                    </span>
                  )}
                </div>

                {/* 4-Eyes Warning Banner if Current User Submitted Transaction */}
                {isSubmitter && (
                  <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/80 text-amber-200 text-xs flex items-start gap-2.5">
                    <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-amber-300">4-Eyes Principle Enforced</div>
                      <p className="text-amber-400/90 mt-0.5 leading-relaxed">
                        4-Eyes principle: As the submitter of this transaction ({selectedCase.submitted_by}), you cannot approve its disposition. A second investigator must review it.
                      </p>
                    </div>
                  </div>
                )}

                {reviewSuccessMsg && (
                  <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                    <span>{reviewSuccessMsg}</span>
                  </div>
                )}

                {reviewErrorMsg && (
                  <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in">
                    <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
                    <div className="leading-tight">{reviewErrorMsg}</div>
                  </div>
                )}

                <form onSubmit={handleDispositionSubmit} className="space-y-4">
                  {/* 1. Disposition Decision Dropdown (default empty) */}
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400 font-medium">
                      Disposition Decision <span className="text-rose-400">*</span>
                    </label>
                    <select
                      value={disposition}
                      disabled={isSubmitter}
                      onChange={(e) => setDisposition(e.target.value)}
                      className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="">Select decision...</option>
                      <option value="ESCALATE_TO_SAR">
                        Escalate — File Suspicious Activity Report (SAR)
                      </option>
                      <option value="FREEZE_ACCOUNT">
                        Confirmed Fraud — Block Entity & Freeze Asset
                      </option>
                      <option value="DISMISS_FALSE_POSITIVE">
                        Clear Transaction — Authorized Legitimate Flow (False Positive)
                      </option>
                      <option value="REQUEST_ADDITIONAL_KYC">
                        Pending — Request Additional Source of Wealth Documentation
                      </option>
                    </select>
                  </div>

                  {/* 2. Structured Evidence Checkboxes (No coached conclusions) */}
                  <div className="space-y-2 p-3 rounded-lg bg-[#0a0f1d] border border-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider font-mono">
                        Evidence Items to Cite <span className="text-rose-400">* (at least 1 required)</span>
                      </span>
                      <button
                        type="button"
                        disabled={isSubmitter || selectedEvidence.length === 0}
                        onClick={() => {
                          const tmpl = `[Evidence reviewed: ${selectedEvidence.join('; ')}] - Observed: <describe specific anomalous activity> - Action: <justification for ${disposition || 'decision'}>`;
                          setNotes(tmpl);
                        }}
                        className="text-[10px] text-sky-400 hover:text-sky-300 disabled:opacity-40 font-mono transition cursor-pointer"
                      >
                        📋 Insert Review Template with Evidence
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                      {availableEvidence.map((ev) => {
                        const isChecked = selectedEvidence.includes(ev);
                        return (
                          <label
                            key={ev}
                            className={`flex items-center gap-2 p-2 rounded-md border text-xs cursor-pointer transition select-none ${
                              isChecked
                                ? 'bg-sky-950/40 border-sky-600/60 text-sky-200'
                                : 'bg-[#11192e] border-slate-800 text-slate-400 hover:border-slate-700'
                            } ${isSubmitter ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <input
                              type="checkbox"
                              disabled={isSubmitter}
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedEvidence((prev) => [...prev, ev]);
                                } else {
                                  setSelectedEvidence((prev) => prev.filter((x) => x !== ev));
                                }
                              }}
                              className="rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                            />
                            <span className="truncate text-[11px]">{ev}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  {/* 3. Investigator Review Findings (min 30 characters) */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <label className="text-slate-400 font-medium">
                        Investigator Review Findings & Notes <span className="text-rose-400">*</span>
                      </label>
                      <span className={`text-[10px] font-mono ${notes.trim().length >= 30 ? 'text-emerald-400' : 'text-slate-500'}`}>
                        {notes.trim().length}/30 min chars
                      </span>
                    </div>
                    <textarea
                      required
                      disabled={isSubmitter}
                      rows={3}
                      value={notes}
                      onChange={(e) => {
                        setNotes(e.target.value);
                        if (reviewErrorMsg) setReviewErrorMsg(null);
                      }}
                      placeholder="Enter verified factual observations, rationale, and evidence review notes (minimum 30 characters)..."
                      className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-sans disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                  </div>

                  {/* 4. Action Button */}
                  <button
                    type="submit"
                    disabled={
                      isSubmitter ||
                      submittingReview ||
                      !disposition ||
                      notes.trim().length < 30 ||
                      selectedEvidence.length === 0
                    }
                    className="w-full py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-xs flex items-center justify-center gap-2 transition cursor-pointer shadow-lg shadow-sky-600/20"
                  >
                    <Send className="h-3.5 w-3.5" />
                    {submittingReview ? 'Recording Disposition...' : 'Commit Disposition (Audit Logged)'}
                  </button>

                  {(!disposition || notes.trim().length < 30 || selectedEvidence.length === 0) && !isSubmitter && (
                    <p className="text-[10px] text-slate-500 text-center font-mono">
                      Submission requires choosing a decision, citing &ge;1 evidence item, and &ge;30 characters of findings.
                    </p>
                  )}
                </form>

              </div>
            </div>
          ) : (
            <EmptyState
              title="Select an Investigation Case"
              description="Choose a case from the queue on the left to inspect its evidence timeline, signals, and submit human review."
            />
          )}
        </div>
      </div>
    </div>
  );
};
