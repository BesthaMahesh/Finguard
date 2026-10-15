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
} from 'lucide-react';
import { api } from '../../services/api';
import { InvestigationCase, AgentTimelineStep, PolicyCitation, UserRole } from '../../types';
import { RiskBadge, RiskMeter } from '../../components/common/RiskBadge';
import { PageHeader } from '../../components/common/PageHeader';
import { SourceCitationView } from '../../components/common/SourceCitation';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';

interface InvestigationWorkbenchProps {
  userRole: UserRole;
  initialTxId?: number | null;
}

export const InvestigationWorkbench: React.FC<InvestigationWorkbenchProps> = ({ userRole, initialTxId }) => {
  const [cases, setCases] = useState<InvestigationCase[]>([]);
  const [selectedCase, setSelectedCase] = useState<InvestigationCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Disposition form states
  const [disposition, setDisposition] = useState('ESCALATE_TO_SAR');
  const [notes, setNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);
  const [reviewErrorMsg, setReviewErrorMsg] = useState<string | null>(null);

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
      await api.analyzeRisk({ transaction_id: txId }, true);
      await loadCases();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDispositionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    
    if (!notes.trim() || notes.trim().length < 5) {
      setReviewErrorMsg('Investigator notes are required (minimum 5 characters) to establish an audited review record.');
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

  const policyCitations: PolicyCitation[] = selectedCase?.policy_citations_json
    ? JSON.parse(selectedCase.policy_citations_json)
    : [];

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Investigations"
        subtitle="Multi-agent case dossiers, evidence timelines, policy excerpts, and human-in-the-loop review"
        breadcrumbs={['FinGuard', 'Operations', 'Investigations']}
        badge={`${cases.length} Active Cases`}
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
              <div className="border-b border-slate-800 pb-4 space-y-2">
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

              {/* Investigation Workflow Timeline */}
              {timeline.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-sky-400" />
                      Investigation Workflow Steps
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Sequential multi-agent execution
                    </span>
                  </div>

                  <div className="space-y-2">
                    {timeline.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-semibold text-sky-300 flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
                            {step.agent.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {step.duration_ms}ms • {step.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300 leading-relaxed pt-0.5">
                          {step.output_summary}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
                    Investigator Disposition & Review
                  </span>
                  {selectedCase.reviewed_by && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      Last reviewed by: {selectedCase.reviewed_by}
                    </span>
                  )}
                </div>

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

                <form onSubmit={handleDispositionSubmit} className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-xs text-slate-400 font-medium">Disposition Decision</label>
                    <select
                      value={disposition}
                      onChange={(e) => setDisposition(e.target.value)}
                      className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 cursor-pointer"
                    >
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

                  <div className="space-y-1">
                    <label className="text-xs text-slate-400 font-medium">
                      Investigator Review Findings & Notes
                    </label>
                    <textarea
                      required
                      minLength={5}
                      rows={3}
                      value={notes}
                      onChange={(e) => {
                        setNotes(e.target.value);
                        if (reviewErrorMsg) setReviewErrorMsg(null);
                      }}
                      placeholder="Enter verified factual observations, rationale, and evidence review notes (minimum 5 characters)..."
                      className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-sans"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={submittingReview}
                    className="w-full py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-medium text-xs flex items-center justify-center gap-2 transition cursor-pointer shadow-lg shadow-sky-600/20"
                  >
                    <Send className="h-3.5 w-3.5" />
                    {submittingReview ? 'Recording Disposition...' : 'Commit Disposition (Audit Logged)'}
                  </button>
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
