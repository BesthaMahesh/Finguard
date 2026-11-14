import React, { useState, useEffect, useRef } from 'react';
import { AgentPipeline } from './AgentPipeline';
import {
  WorkflowRunState,
  createInitialWorkflowState,
  applyEvent,
  replayEvents,
} from './agentState';
import { streamAgentWorkflow } from './streamClient';
import { api } from '../../services/api';
import {
  Sparkles,
  Zap,
  Play,
  RotateCcw,
  StopCircle,
  AlertCircle,
  FileText,
  Search,
  CheckCircle,
  Sliders,
  Database,
} from 'lucide-react';

interface AgentWorkflowProps {
  initialTxId?: number | null;
  onOpenCase?: (caseId: string) => void;
}

export const AgentWorkflow: React.FC<AgentWorkflowProps> = ({
  initialTxId = null,
  onOpenCase,
}) => {
  const [txIdInput, setTxIdInput] = useState<string>(initialTxId ? String(initialTxId) : '');
  const [selectedPreset, setSelectedPreset] = useState<string>('custom');

  // Transaction fields for live execution
  const [txType, setTxType] = useState<string>('TRANSFER');
  const [amount, setAmount] = useState<number>(212089.74);
  const [nameOrig, setNameOrig] = useState<string>('C378910639');
  const [oldBalanceOrg, setOldBalanceOrg] = useState<number>(212089.74);
  const [newBalanceOrig, setNewBalanceOrig] = useState<number>(0.0);
  const [nameDest, setNameDest] = useState<string>('C982736182');
  const [oldBalanceDest, setOldBalanceDest] = useState<number>(0.0);
  const [newBalanceDest, setNewBalanceDest] = useState<number>(0.0);

  const [workflowState, setWorkflowState] = useState<WorkflowRunState>(createInitialWorkflowState);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [isReplaying, setIsReplaying] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (initialTxId) {
      loadTransactionDetails(initialTxId);
    }
  }, [initialTxId]);

  const loadTransactionDetails = async (id: number) => {
    try {
      const tx = await api.getTransactionDetail(id);
      if (tx) {
        setTxType(tx.type || 'TRANSFER');
        setAmount(tx.amount || 0);
        setNameOrig(tx.name_orig || '');
        setOldBalanceOrg(tx.old_balance_org || 0);
        setNewBalanceOrig(tx.new_balance_orig || 0);
        setNameDest(tx.name_dest || '');
        setOldBalanceDest(tx.old_balance_dest || 0);
        setNewBalanceDest(tx.new_balance_dest || 0);
        setTxIdInput(String(id));
      }
    } catch (e) {
      console.warn('Could not load transaction detail:', e);
    }
  };

  const handleApplyPreset = (preset: 'normal' | 'drain' | 'high_transfer') => {
    setSelectedPreset(preset);
    setTxIdInput('');
    if (preset === 'normal') {
      setTxType('PAYMENT');
      setAmount(120.5);
      setNameOrig('C192837465');
      setOldBalanceOrg(4500.0);
      setNewBalanceOrig(4379.5);
      setNameDest('M987654321');
      setOldBalanceDest(0.0);
      setNewBalanceDest(0.0);
    } else if (preset === 'drain') {
      setTxType('CASH_OUT');
      setAmount(1161495.82);
      setNameOrig('C165094398');
      setOldBalanceOrg(1161495.82);
      setNewBalanceOrig(0.0);
      setNameDest('C293847561');
      setOldBalanceDest(3400.0);
      setNewBalanceDest(1164895.82);
    } else if (preset === 'high_transfer') {
      setTxType('TRANSFER');
      setAmount(212089.74);
      setNameOrig('C378910639');
      setOldBalanceOrg(212089.74);
      setNewBalanceOrig(0.0);
      setNameDest('C982736182');
      setOldBalanceDest(0.0);
      setNewBalanceDest(0.0);
    }
  };

  const handleStartWorkflow = async () => {
    if (isRunning) return;

    setIsRunning(true);
    setErrorMessage(null);
    setWorkflowState(createInitialWorkflowState());

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const payload: any = {
      type: txType,
      amount: Number(amount),
      name_orig: nameOrig,
      old_balance_org: Number(oldBalanceOrg),
      new_balance_orig: Number(newBalanceOrig),
      name_dest: nameDest,
      old_balance_dest: Number(oldBalanceDest),
      new_balance_dest: Number(newBalanceDest),
      step: 1,
    };

    if (txIdInput.trim()) {
      const parsedId = parseInt(txIdInput.trim(), 10);
      if (!isNaN(parsedId)) {
        payload.transaction_id = parsedId;
      }
    }

    try {
      await streamAgentWorkflow(
        payload,
        (eventName, data) => {
          setWorkflowState((prev) => applyEvent(prev, { event: eventName, data }));
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setErrorMessage('Workflow stream was cancelled by user.');
      } else {
        setErrorMessage(`Stream error: ${err.message || 'Workflow connection failure'}`);
      }
      setWorkflowState((prev) => ({
        ...prev,
        overallStatus: 'failed',
        error: err.message,
      }));
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider">
            <Sparkles className="h-4 w-4" />
            Autonomous Agent Control Plane
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-white mt-1">
            Agent Workflow Orchestration
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time event streaming across 10 specialized LangGraph agents with dynamic conditional routing.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {isRunning ? (
            <button
              type="button"
              onClick={handleAbort}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-semibold shadow-lg transition cursor-pointer"
            >
              <StopCircle className="h-4 w-4" />
              Abort Workflow
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStartWorkflow}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-950/50 transition cursor-pointer"
            >
              <Play className="h-4 w-4 fill-white" />
              Execute Live 10-Agent Workflow
            </button>
          )}
        </div>
      </div>

      {/* Configuration & Quick Scenario Presets */}
      <div className="rounded-xl bg-[#0b101d] border border-slate-800/80 p-4 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-slate-300">
            <Sliders className="h-3.5 w-3.5 text-cyan-400" />
            <span>Workflow Trigger & Ingestion Parameters</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-mono text-slate-400 mr-1">Load Preset:</span>
            <button
              type="button"
              onClick={() => handleApplyPreset('normal')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
                selectedPreset === 'normal'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              Normal Payment (Fast-Track)
            </button>
            <button
              type="button"
              onClick={() => handleApplyPreset('drain')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
                selectedPreset === 'drain'
                  ? 'bg-rose-950 text-rose-300 border border-rose-600'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              Total Liquidation Drain (Deep Track)
            </button>
            <button
              type="button"
              onClick={() => handleApplyPreset('high_transfer')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
                selectedPreset === 'high_transfer'
                  ? 'bg-amber-950 text-amber-300 border border-amber-600'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              $212k Transfer (Deep Track)
            </button>
          </div>
        </div>

        {/* Input Fields */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-xs">
          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Tx ID (DB Lookup)</label>
            <input
              type="text"
              placeholder="e.g. 199"
              value={txIdInput}
              onChange={(e) => {
                setTxIdInput(e.target.value);
                const idNum = parseInt(e.target.value, 10);
                if (!isNaN(idNum)) loadTransactionDetails(idNum);
              }}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Type</label>
            <select
              value={txType}
              onChange={(e) => setTxType(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="PAYMENT">PAYMENT</option>
              <option value="TRANSFER">TRANSFER</option>
              <option value="CASH_OUT">CASH_OUT</option>
              <option value="CASH_IN">CASH_IN</option>
              <option value="DEBIT">DEBIT</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Amount ($)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Origin Account</label>
            <input
              type="text"
              value={nameOrig}
              onChange={(e) => setNameOrig(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Old Balance (Orig)</label>
            <input
              type="number"
              value={oldBalanceOrg}
              onChange={(e) => setOldBalanceOrg(parseFloat(e.target.value) || 0)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">New Balance (Orig)</label>
            <input
              type="number"
              value={newBalanceOrig}
              onChange={(e) => setNewBalanceOrig(parseFloat(e.target.value) || 0)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Dest Account</label>
            <input
              type="text"
              value={nameDest}
              onChange={(e) => setNameDest(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">New Balance (Dest)</label>
            <input
              type="number"
              value={newBalanceDest}
              onChange={(e) => setNewBalanceDest(parseFloat(e.target.value) || 0)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Agent Pipeline Display */}
      <AgentPipeline
        state={workflowState}
        onOpenCase={onOpenCase}
        onReplay={() => {
          if (workflowState.overallStatus !== 'running') {
            handleStartWorkflow();
          }
        }}
      />
    </div>
  );
};

