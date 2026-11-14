import React, { useState } from 'react';
import {
  WorkflowRunState,
  AgentNodeState,
} from './agentState';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  FastForward,
  Activity,
  Layers,
  Terminal,
  ExternalLink,
} from 'lucide-react';

interface AgentPipelineProps {
  state: WorkflowRunState;
  onOpenCase?: (caseId: string) => void;
  onReplay?: () => void;
  isReplaying?: boolean;
}

export const AgentPipeline: React.FC<AgentPipelineProps> = ({
  state,
  onOpenCase,
  onReplay,
  isReplaying = false,
}) => {
  const [expandedAgentId, setExpandedAgentId] = useState<string | null>(null);

  const totalAgents = state.agents.length;
  const finishedCount = state.agents.filter(
    (a) => a.status === 'completed' || a.status === 'skipped' || a.status === 'failed'
  ).length;
  const progressPct = totalAgents > 0 ? Math.round((finishedCount / totalAgents) * 100) : 0;

  const toggleExpand = (id: string) => {
    setExpandedAgentId((prev) => (prev === id ? null : id));
  };

  const getStatusBadge = (status: AgentNodeState['status']) => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-sky-950/80 text-sky-400 border border-sky-500/40 animate-pulse">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-ping" />
            RUNNING
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-500/40">
            <CheckCircle2 className="h-3 w-3" />
            COMPLETED
          </span>
        );
      case 'skipped':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-amber-950/60 text-amber-300 border border-amber-500/40">
            <FastForward className="h-3 w-3" />
            SKIPPED (FAST-TRACK)
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium bg-rose-950/80 text-rose-400 border border-rose-500/40">
            <AlertTriangle className="h-3 w-3" />
            FAILED
          </span>
        );
      case 'waiting':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-slate-400 bg-slate-900 border border-slate-800">
            <Clock className="h-3 w-3" />
            WAITING
          </span>
        );
    }
  };

  const getCardBorder = (status: AgentNodeState['status']) => {
    switch (status) {
      case 'running':
        return 'border-sky-500/80 bg-sky-950/10 shadow-[0_0_20px_rgba(56,189,248,0.15)] ring-1 ring-sky-500/40';
      case 'completed':
        return 'border-emerald-500/30 bg-[#0c1324]';
      case 'skipped':
        return 'border-dashed border-amber-600/40 bg-[#0c111e]/60 opacity-75';
      case 'failed':
        return 'border-rose-500/60 bg-rose-950/10';
      case 'waiting':
      default:
        return 'border-slate-800/80 bg-[#0b0f19]/70 opacity-60';
    }
  };

  const renderChips = (agent: AgentNodeState) => {
    const s = agent.summary;
    if (!s || Object.keys(s).length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1.5 mt-2">
        {Object.entries(s).map(([key, val]) => {
          if (val === null || val === undefined || typeof val === 'object') return null;
          return (
            <span
              key={key}
              className="inline-flex items-center px-2 py-0.5 rounded bg-slate-900/90 border border-slate-700/60 text-[10px] font-mono text-slate-300"
            >
              <span className="text-slate-500 mr-1">{key.replace(/_/g, ' ')}:</span>
              <span className="text-sky-300 font-semibold">{String(val)}</span>
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* 1. Orchestration Flow Strip (Horizontal Pipeline Matrix) */}
      <div className="rounded-xl bg-[#0b101d] border border-slate-800/90 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              LangGraph Multi-Agent Flow Strip ({finishedCount}/{totalAgents} Active Nodes)
            </span>
          </div>
          {onReplay && (
            <button
              onClick={onReplay}
              disabled={isReplaying || state.overallStatus === 'running'}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-sky-950 hover:bg-sky-900 border border-sky-700/60 text-sky-300 text-xs font-mono transition cursor-pointer disabled:opacity-40"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isReplaying ? 'animate-spin' : ''}`} />
              Replay Trace
            </button>
          )}
        </div>

        {/* Dynamic Progress Bar */}
        <div className="w-full bg-slate-900 rounded-full h-1.5 mb-4 overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-500 ${
              state.overallStatus === 'failed'
                ? 'bg-rose-500'
                : state.overallStatus === 'completed'
                ? 'bg-emerald-400'
                : 'bg-gradient-to-r from-cyan-500 via-sky-400 to-indigo-500'
            }`}
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* 10-Node Horizontal Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
          {state.agents.map((agent, index) => {
            let statusColor = 'border-slate-800 bg-slate-900/40 text-slate-400';
            let dotColor = 'bg-slate-600';
            if (agent.status === 'running') {
              statusColor = 'border-cyan-400 bg-cyan-950/40 text-cyan-200 ring-1 ring-cyan-400/50 animate-pulse';
              dotColor = 'bg-cyan-400 animate-ping';
            } else if (agent.status === 'completed') {
              statusColor = 'border-emerald-500/50 bg-emerald-950/20 text-emerald-300';
              dotColor = 'bg-emerald-400';
            } else if (agent.status === 'skipped') {
              statusColor = 'border-amber-600/40 bg-amber-950/10 text-amber-300 border-dashed';
              dotColor = 'bg-amber-400';
            } else if (agent.status === 'failed') {
              statusColor = 'border-rose-500 bg-rose-950/30 text-rose-300';
              dotColor = 'bg-rose-400';
            }

            return (
              <div
                key={agent.id}
                onClick={() => toggleExpand(agent.id)}
                className={`p-2 rounded-lg border text-left cursor-pointer transition select-none flex flex-col justify-between ${statusColor}`}
                title={`${agent.label}: ${agent.role}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] text-slate-400">#{index + 1}</span>
                  <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
                </div>
                <div className="font-semibold text-[11px] truncate leading-tight">
                  {agent.label.replace(' Agent', '')}
                </div>
                <div className="text-[9px] font-mono text-slate-400 mt-1 capitalize truncate">
                  {agent.status} {agent.duration_ms !== null ? `(${agent.duration_ms}ms)` : ''}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Orchestrator Verdict Card (Appears upon run completion) */}
      {state.verdict && (
        <div
          className={`rounded-xl border p-5 shadow-lg transition-all ${
            state.verdict.risk_tier === 'CRITICAL'
              ? 'bg-[#150a12] border-rose-600/70 ring-1 ring-rose-500/40'
              : state.verdict.risk_tier === 'HIGH'
              ? 'bg-[#161208] border-amber-600/70 ring-1 ring-amber-500/40'
              : 'bg-[#081514] border-emerald-600/60 ring-1 ring-emerald-500/30'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3 mb-3">
            <div className="flex items-center gap-3">
              {state.verdict.risk_tier === 'CRITICAL' || state.verdict.risk_tier === 'HIGH' ? (
                <ShieldAlert className="h-6 w-6 text-rose-400" />
              ) : (
                <ShieldCheck className="h-6 w-6 text-emerald-400" />
              )}
              <div>
                <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  Orchestrator Final Verdict
                </div>
                <div className="text-lg font-bold text-white flex items-center gap-2">
                  <span>Composite Risk: {state.verdict.risk_score.toFixed(1)}/100</span>
                  <span
                    className={`text-xs font-mono px-2 py-0.5 rounded font-semibold ${
                      state.verdict.risk_tier === 'CRITICAL'
                        ? 'bg-rose-950 text-rose-300 border border-rose-700'
                        : state.verdict.risk_tier === 'HIGH'
                        ? 'bg-amber-950 text-amber-300 border border-amber-700'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                    }`}
                  >
                    {state.verdict.risk_tier}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-3 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-300">
                Decision: <strong className="text-white">{state.verdict.decision}</strong>
              </span>

              {state.verdict.case_id && onOpenCase && (
                <button
                  type="button"
                  onClick={() => onOpenCase(state.verdict!.case_id!)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold shadow-md transition cursor-pointer"
                >
                  <span>Open Case {state.verdict.case_id}</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          <div className="text-xs text-slate-300 leading-relaxed font-sans bg-black/40 rounded-lg p-3 border border-slate-800/80">
            <span className="font-mono text-cyan-400 font-semibold uppercase text-[10px] block mb-1">
              Objective Explainability Narrative:
            </span>
            {state.verdict.narrative || state.liveNarrative}
          </div>
        </div>
      )}

      {/* 3. Vertical Timeline of Agent Execution Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider px-1">
          <span>Agent Execution Timeline</span>
          {state.duration_ms !== null && (
            <span>Total Graph Latency: {state.duration_ms.toFixed(1)}ms</span>
          )}
        </div>

        {state.agents.map((agent, idx) => {
          const isExpanded = expandedAgentId === agent.id;
          const isExplainability = agent.id === 'explainability';

          return (
            <div
              key={agent.id}
              className={`rounded-xl border transition-all duration-200 overflow-hidden ${getCardBorder(
                agent.status
              )}`}
            >
              {/* Card Header */}
              <div
                onClick={() => toggleExpand(agent.id)}
                className="p-3.5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center gap-3">
                  <div className="font-mono text-xs text-slate-500 w-5">#{idx + 1}</div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100">{agent.label}</span>
                      {getStatusBadge(agent.status)}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{agent.role}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {agent.duration_ms !== null && agent.status !== 'waiting' && (
                    <span className="font-mono text-xs text-slate-400">
                      {agent.duration_ms.toFixed(1)}ms
                    </span>
                  )}
                  <button className="text-slate-400 hover:text-white transition">
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Live Streaming Narrative for Explainability Agent */}
              {isExplainability && (agent.status === 'running' || agent.tokens) && (
                <div className="px-4 pb-3 pt-1">
                  <div className="rounded-lg bg-[#070b14] border border-cyan-900/60 p-3 text-xs text-cyan-200 font-sans leading-relaxed">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-cyan-400 uppercase font-semibold mb-1">
                      <Sparkles className="h-3 w-3 animate-spin" />
                      Live Token Stream from Groq LLM:
                    </div>
                    <span>{agent.tokens || state.liveNarrative}</span>
                    {agent.status === 'running' && (
                      <span className="inline-block w-2 h-3 bg-cyan-400 ml-1 animate-pulse" />
                    )}
                  </div>
                </div>
              )}

              {/* Key Output Chips Preview */}
              {agent.status === 'completed' && !isExpanded && (
                <div className="px-4 pb-3 pt-0">{renderChips(agent)}</div>
              )}

              {/* Skipped Reason Notice */}
              {agent.status === 'skipped' && (
                <div className="px-4 pb-3 pt-0 text-[11px] font-mono text-amber-400/90 italic">
                  ↳ Skipped by Supervisor: Transaction identified as low-risk fast-track pattern.
                </div>
              )}

              {/* Expanded Details & Raw JSON Payload */}
              {isExpanded && (
                <div className="border-t border-slate-800/80 p-4 bg-[#080d19]/90 space-y-3 text-xs">
                  {renderChips(agent)}

                  {agent.summary && Object.keys(agent.summary).length > 0 && (
                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-400 mb-1">
                        Synthesized Summary:
                      </div>
                      <pre className="p-2.5 rounded-lg bg-black/60 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                        {JSON.stringify(agent.summary, null, 2)}
                      </pre>
                    </div>
                  )}

                  {agent.output && Object.keys(agent.output).length > 0 && (
                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-400 mb-1">
                        Trimmed Graph State Output:
                      </div>
                      <pre className="p-2.5 rounded-lg bg-black/60 border border-slate-800 font-mono text-[11px] text-cyan-300 overflow-x-auto">
                        {JSON.stringify(agent.output, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

