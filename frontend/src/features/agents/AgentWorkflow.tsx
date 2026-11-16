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
  Lock,
  Unlock,
  PlusCircle,
  RefreshCw,
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

  // Loaded database transaction metadata & what-if simulation state
  const [loadedDbTx, setLoadedDbTx] = useState<any | null>(null);
  const [isSimulationMode, setIsSimulationMode] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Transaction fields for live execution
  const [txType, setTxType] = useState<string>('TRANSFER');
  const [amount, setAmount] = useState<string>('212,089.74');
  const [nameOrig, setNameOrig] = useState<string>('C378910639');
  const [oldBalanceOrg, setOldBalanceOrg] = useState<string>('212,089.74');
  const [newBalanceOrig, setNewBalanceOrig] = useState<string>('0.00');
  const [nameDest, setNameDest] = useState<string>('C982736182');
  const [oldBalanceDest, setOldBalanceDest] = useState<string>('0.00');
  const [newBalanceDest, setNewBalanceDest] = useState<string>('0.00');

  const formatCurrencyOnBlur = (val: string, setter: (v: string) => void) => {
    const clean = String(val).replace(/,/g, '').trim();
    if (!clean) return;
    const num = parseFloat(clean);
    if (!isNaN(num)) {
      setter(num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    }
  };

  const unformatCurrencyOnFocus = (val: string, setter: (v: string) => void) => {
    setter(String(val).replace(/,/g, ''));
  };

  const parseCleanFloat = (val: string | number): number => {
    const clean = String(val).replace(/,/g, '').trim();
    return parseFloat(clean) || 0;
  };

  const [workflowState, setWorkflowState] = useState<WorkflowRunState>(createInitialWorkflowState);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
        setLoadedDbTx(tx);
        setIsSimulationMode(false);
        setTxType(tx.type || 'TRANSFER');
        setAmount((tx.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        setNameOrig(tx.name_orig || '');
        setOldBalanceOrg((tx.old_balance_org || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        setNewBalanceOrig((tx.new_balance_orig || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        setNameDest(tx.name_dest || '');
        setOldBalanceDest((tx.old_balance_dest || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        setNewBalanceDest((tx.new_balance_dest || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        setTxIdInput(String(id));
      }
    } catch (e) {
      console.warn('Could not load transaction detail:', e);
    }
  };

  const handleApplyPreset = (preset: 'normal' | 'drain' | 'high_transfer') => {
    setSelectedPreset(preset);
    setTxIdInput('');
    setLoadedDbTx(null);
    setIsSimulationMode(false);

    if (preset === 'normal') {
      setTxType('PAYMENT');
      setAmount('84.50');
      setNameOrig('C192837465');
      setOldBalanceOrg('3,500.00');
      setNewBalanceOrig('3,415.50');
      setNameDest('M987654321');
      setOldBalanceDest('0.00');
      setNewBalanceDest('0.00');
    } else if (preset === 'drain') {
      setTxType('CASH_OUT');
      setAmount('1,161,495.82');
      setNameOrig('C165094398');
      setOldBalanceOrg('1,161,495.82');
      setNewBalanceOrig('0.00');
      setNameDest('C293847561');
      setOldBalanceDest('3,400.00');
      setNewBalanceDest('1,164,895.82');
    } else if (preset === 'high_transfer') {
      setTxType('TRANSFER');
      setAmount('212,089.74');
      setNameOrig('C378910639');
      setOldBalanceOrg('212,089.74');
      setNewBalanceOrig('0.00');
      setNameDest('C982736182');
      setOldBalanceDest('0.00');
      setNewBalanceDest('0.00');
    }
  };

  const handleAutoFillBalances = () => {
    const amt = parseCleanFloat(amount);
    const oldO = parseCleanFloat(oldBalanceOrg);
    if (['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT'].includes(txType)) {
      const calcNewO = Math.max(0, oldO - amt);
      setNewBalanceOrig(calcNewO.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    } else if (txType === 'CASH_IN') {
      const calcNewO = oldO + amt;
      setNewBalanceOrig(calcNewO.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    }
    if (nameDest.trim().startsWith('M')) {
      setOldBalanceDest('0.00');
      setNewBalanceDest('0.00');
    } else {
      const oldD = parseCleanFloat(oldBalanceDest);
      const calcNewD = oldD + amt;
      setNewBalanceDest(calcNewD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    }
  };

  const handleSaveAsNewTransaction = async () => {
    try {
      const created = await api.createTransaction({
        step: 1,
        type: txType,
        amount: parseCleanFloat(amount),
        name_orig: nameOrig,
        old_balance_org: parseCleanFloat(oldBalanceOrg),
        new_balance_orig: parseCleanFloat(newBalanceOrig),
        name_dest: nameDest,
        old_balance_dest: parseCleanFloat(oldBalanceDest),
        new_balance_dest: parseCleanFloat(newBalanceDest),
      });
      setLoadedDbTx(created);
      setIsSimulationMode(false);
      setTxIdInput(String(created.id));
      setSaveSuccessMsg(`Saved as new persisted transaction #${created.id} (Decision: ${created.decision || 'EVALUATED'})`);
      setTimeout(() => setSaveSuccessMsg(null), 5000);
    } catch (err: any) {
      setErrorMessage(`Failed to save new transaction: ${err.message}`);
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
      amount: parseCleanFloat(amount),
      name_orig: nameOrig,
      old_balance_org: parseCleanFloat(oldBalanceOrg),
      new_balance_orig: parseCleanFloat(newBalanceOrig),
      name_dest: nameDest,
      old_balance_dest: parseCleanFloat(oldBalanceDest),
      new_balance_dest: parseCleanFloat(newBalanceDest),
      step: 1,
      is_simulation: isSimulationMode,
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

  // Live ledger variance calculation
  const numAmt = parseCleanFloat(amount);
  const numOldO = parseCleanFloat(oldBalanceOrg);
  const numNewO = parseCleanFloat(newBalanceOrig);
  const numOldD = parseCleanFloat(oldBalanceDest);
  const numNewD = parseCleanFloat(newBalanceDest);
  const actualOrigChange = numNewO - numOldO;
  const expectedOrigChange = ['TRANSFER', 'CASH_OUT', 'PAYMENT', 'DEBIT'].includes(txType) ? -numAmt : numAmt;
  const hasOrigDiscrepancy = numAmt > 0 && Math.abs(actualOrigChange - expectedOrigChange) > 1.0;
  const isMerchant = nameDest.trim().startsWith('M');
  const hasMerchantDiscrepancy = isMerchant && (numOldD > 0 || numNewD > 0);

  const isFieldsReadOnly = loadedDbTx !== null && !isSimulationMode;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider">
            <Sparkles className="h-4 w-4" />
            Operations / Risk Analysis Workflow
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-white mt-1">
            Autonomous Risk Analysis Workflow
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Continuous risk evaluation across 10 specialized financial crime & compliance intelligence engines.
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
              Cancel Analysis
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStartWorkflow}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-950/50 transition cursor-pointer"
            >
              <Play className="h-4 w-4 fill-white" />
              {isSimulationMode ? 'Run Scenario Simulation' : 'Execute Live Risk Assessment'}
            </button>
          )}
        </div>
      </div>

      {/* Database Loaded Record or Simulation Mode Banner */}
      {loadedDbTx && (
        <div className={`p-3 rounded-xl border flex flex-wrap items-center justify-between gap-3 text-xs font-mono ${
          isSimulationMode
            ? 'bg-amber-950/40 border-amber-600/80 text-amber-200'
            : 'bg-sky-950/30 border-sky-800/60 text-sky-300'
        }`}>
          <div className="flex items-center gap-2">
            {isSimulationMode ? (
              <Unlock className="h-4 w-4 text-amber-400" />
            ) : (
              <Lock className="h-4 w-4 text-sky-400" />
            )}
            <span>
              {isSimulationMode ? (
                <strong className="text-amber-400">HYPOTHETICAL SIMULATION:</strong>
              ) : (
                <strong>SETTLED TRANSACTION RECORD:</strong>
              )}{' '}
              Transaction #{loadedDbTx.id} ({loadedDbTx.type} — ${loadedDbTx.amount?.toLocaleString()})
            </span>
          </div>

          <div className="flex items-center gap-2">
            {!isSimulationMode ? (
              <button
                type="button"
                onClick={() => setIsSimulationMode(true)}
                className="px-2.5 py-1 rounded bg-amber-950 hover:bg-amber-900 border border-amber-600 text-amber-300 text-[11px] font-mono transition cursor-pointer"
              >
                ✏️ Simulate Scenario (What-If)
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={handleSaveAsNewTransaction}
                  className="px-2.5 py-1 rounded bg-cyan-950 hover:bg-cyan-900 border border-cyan-600 text-cyan-300 text-[11px] font-mono transition cursor-pointer flex items-center gap-1.5"
                >
                  <PlusCircle className="h-3 w-3" />
                  Submit as Live Transaction
                </button>
                <button
                  type="button"
                  onClick={() => {
                    loadTransactionDetails(loadedDbTx.id);
                  }}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 text-[11px] font-mono transition cursor-pointer"
                >
                  Revert to Settled Record
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {saveSuccessMsg && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-700 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Configuration & Quick Scenario Presets */}
      <div className="rounded-xl bg-[#0b101d] border border-slate-800/80 p-4 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-slate-300">
            <Sliders className="h-3.5 w-3.5 text-cyan-400" />
            <span>Transaction Assessment Parameters</span>
            {isSimulationMode && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-amber-900/60 text-amber-300 border border-amber-600">
                SCENARIO SIMULATION
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-mono text-slate-400 mr-1">Scenario Templates:</span>
            <button
              type="button"
              onClick={() => handleApplyPreset('normal')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
                selectedPreset === 'normal'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              Routine Retail Payment (Fast-Track)
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
              Full Account Liquidation (Forensic Review)
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
              High-Value Transfer ($212k Forensic Review)
            </button>
            <button
              type="button"
              disabled={isFieldsReadOnly}
              onClick={handleAutoFillBalances}
              className="px-2.5 py-1 rounded bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-700/60 text-cyan-300 text-[11px] font-mono transition cursor-pointer disabled:opacity-50"
            >
              ⚡ Reconcile Balances
            </button>
          </div>
        </div>

        {/* Input Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9 gap-2.5 text-xs">
          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Transaction ID (Lookup)</label>
            <input
              type="text"
              placeholder="e.g. 199"
              value={txIdInput}
              onChange={(e) => {
                setTxIdInput(e.target.value);
                const idNum = parseInt(e.target.value, 10);
                if (!isNaN(idNum)) loadTransactionDetails(idNum);
                else {
                  setLoadedDbTx(null);
                  setIsSimulationMode(false);
                }
              }}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Transfer Type</label>
            <select
              value={txType}
              disabled={isFieldsReadOnly}
              onChange={(e) => setTxType(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <option value="PAYMENT">PAYMENT</option>
              <option value="TRANSFER">TRANSFER</option>
              <option value="CASH_OUT">CASH_OUT</option>
              <option value="CASH_IN">CASH_IN</option>
              <option value="DEBIT">DEBIT</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Transfer Amount ($)</label>
            <input
              type="text"
              value={amount}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setAmount(e.target.value)}
              onFocus={() => unformatCurrencyOnFocus(amount, setAmount)}
              onBlur={() => formatCurrencyOnBlur(amount, setAmount)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Origin Account (Sender)</label>
            <input
              type="text"
              value={nameOrig}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setNameOrig(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Pre-Transfer Bal (Sender)</label>
            <input
              type="text"
              value={oldBalanceOrg}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setOldBalanceOrg(e.target.value)}
              onFocus={() => unformatCurrencyOnFocus(oldBalanceOrg, setOldBalanceOrg)}
              onBlur={() => formatCurrencyOnBlur(oldBalanceOrg, setOldBalanceOrg)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Post-Transfer Bal (Sender)</label>
            <input
              type="text"
              value={newBalanceOrig}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setNewBalanceOrig(e.target.value)}
              onFocus={() => unformatCurrencyOnFocus(newBalanceOrig, setNewBalanceOrig)}
              onBlur={() => formatCurrencyOnBlur(newBalanceOrig, setNewBalanceOrig)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Dest Account (Beneficiary)</label>
            <input
              type="text"
              value={nameDest}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setNameDest(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Pre-Transfer Bal (Beneficiary)</label>
            <input
              type="text"
              value={oldBalanceDest}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setOldBalanceDest(e.target.value)}
              onFocus={() => unformatCurrencyOnFocus(oldBalanceDest, setOldBalanceDest)}
              onBlur={() => formatCurrencyOnBlur(oldBalanceDest, setOldBalanceDest)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-slate-400 mb-1">Post-Transfer Bal (Beneficiary)</label>
            <input
              type="text"
              value={newBalanceDest}
              readOnly={isFieldsReadOnly}
              onChange={(e) => setNewBalanceDest(e.target.value)}
              onFocus={() => unformatCurrencyOnFocus(newBalanceDest, setNewBalanceDest)}
              onBlur={() => formatCurrencyOnBlur(newBalanceDest, setNewBalanceDest)}
              className="w-full bg-[#070b14] border border-slate-700/80 rounded px-2 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-cyan-500 read-only:opacity-60 read-only:cursor-not-allowed"
            />
          </div>
        </div>

        {/* Live Ledger Warnings & Reconciliation Feedback */}
        {(hasOrigDiscrepancy || hasMerchantDiscrepancy) && (
          <div className="space-y-2 pt-1 border-t border-slate-800/60">
            {hasOrigDiscrepancy && (
              <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-700/60 text-amber-300 text-xs font-mono space-y-1">
                <div className="flex items-center gap-2 font-semibold">
                  <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
                  <span>
                    Origin balance delta ({actualOrigChange >= 0 ? `+${actualOrigChange.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : actualOrigChange.toLocaleString(undefined, { minimumFractionDigits: 2 })}) does not reconcile with transfer amount ({numAmt.toLocaleString(undefined, { minimumFractionDigits: 2 })}).
                  </span>
                </div>
                <div className="text-[11px] text-amber-300/80 pl-6 font-sans">
                  This transaction exhibits ledger discrepancies and is automatically escalated to 4-Eyes forensic review.
                </div>
              </div>
            )}
            {hasMerchantDiscrepancy && (
              <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-700/60 text-amber-300 text-xs font-mono flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
                <span>
                  Beneficiary account ({nameDest}) is designated as a commercial merchant terminal ("M") with an irregular nonzero balance.
                </span>
              </div>
            )}
          </div>
        )}
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
