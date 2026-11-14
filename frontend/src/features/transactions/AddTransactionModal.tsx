import React, { useState } from 'react';
import { api } from '../../services/api';
import {
  X,
  PlusCircle,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  UploadCloud,
  FileSpreadsheet,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newTx: any) => void;
  onSuccessAndRun?: (newTx: any) => void;
  userRole?: string;
}

export const AddTransactionModal: React.FC<AddTransactionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  onSuccessAndRun,
  userRole = 'USER',
}) => {
  const normRole = (userRole || 'USER').toUpperCase();
  const isAdmin = normRole === 'ADMIN' || normRole === 'ADMINISTRATOR';

  const [activeTab, setActiveTab] = useState<'form' | 'csv'>('form');

  // Form states
  const [step, setStep] = useState<number>(1);
  const [type, setType] = useState<string>('PAYMENT');
  const [amount, setAmount] = useState<string>('84.50');
  const [nameOrig, setNameOrig] = useState<string>('C129384756');
  const [oldBalanceOrg, setOldBalanceOrg] = useState<string>('3500.00');
  const [newBalanceOrig, setNewBalanceOrig] = useState<string>('3415.50');
  const [nameDest, setNameDest] = useState<string>('M492817402');
  const [oldBalanceDest, setOldBalanceDest] = useState<string>('0.00');
  const [newBalanceDest, setNewBalanceDest] = useState<string>('0.00');

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // CSV bulk upload states
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvReport, setCsvReport] = useState<any | null>(null);
  const [uploadingCsv, setUploadingCsv] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleLoadSample = (sampleType: 'normal' | 'drain') => {
    setErrorMsg(null);
    if (sampleType === 'normal') {
      setType('PAYMENT');
      setAmount('84.50');
      setNameOrig('C129384756');
      setOldBalanceOrg('3500.00');
      setNewBalanceOrig('3415.50');
      setNameDest('M492817402');
      setOldBalanceDest('0.00');
      setNewBalanceDest('0.00');
    } else {
      setType('TRANSFER');
      setAmount('489000.00');
      setNameOrig('C839201948');
      setOldBalanceOrg('489000.00');
      setNewBalanceOrig('0.00');
      setNameDest('C192837465');
      setOldBalanceDest('0.00');
      setNewBalanceDest('0.00');
    }
  };

  const validateForm = (): string | null => {
    const amt = parseFloat(amount);
    if (isNaN(amt) || amt <= 0) {
      return 'Transaction amount must be strictly greater than $0.00.';
    }
    const oldO = parseFloat(oldBalanceOrg);
    const newO = parseFloat(newBalanceOrig);
    const oldD = parseFloat(oldBalanceDest);
    const newD = parseFloat(newBalanceDest);

    if (isNaN(oldO) || oldO < 0 || isNaN(newO) || newO < 0) {
      return 'Origin balances cannot be negative.';
    }
    if (isNaN(oldD) || oldD < 0 || isNaN(newD) || newD < 0) {
      return 'Destination balances cannot be negative.';
    }
    if (!nameOrig.trim() || !nameDest.trim()) {
      return 'Both Origin and Destination account numbers are required.';
    }

    if (['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT'].includes(type)) {
      if (newO > oldO) {
        return `Impossible ledger: Origin balance cannot increase from $${oldO.toLocaleString()} to $${newO.toLocaleString()} on an outbound ${type}.`;
      }
    } else if (type === 'CASH_IN') {
      if (newO < oldO) {
        return `Impossible ledger: Origin balance cannot decrease on a CASH_IN transaction.`;
      }
    }
    return null;
  };

  const handleSubmit = async (andRunAgents: boolean = false) => {
    const err = validateForm();
    if (err) {
      setErrorMsg(err);
      return;
    }

    setErrorMsg(null);
    setIsSubmitting(true);

    const payload = {
      step: Number(step) || 1,
      type,
      amount: parseFloat(amount),
      name_orig: nameOrig.trim(),
      old_balance_org: parseFloat(oldBalanceOrg),
      new_balance_orig: parseFloat(newBalanceOrig),
      name_dest: nameDest.trim(),
      old_balance_dest: parseFloat(oldBalanceDest),
      new_balance_dest: parseFloat(newBalanceDest),
    };

    try {
      const createdTx = await api.createTransaction(payload);
      if (andRunAgents && onSuccessAndRun) {
        onSuccessAndRun(createdTx);
      } else {
        onSuccess(createdTx);
      }
      onClose();
    } catch (apiErr: any) {
      setErrorMsg(apiErr.message || 'Failed to submit transaction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUploadCsvSubmit = async () => {
    if (!csvFile) {
      setErrorMsg('Please select a valid CSV file.');
      return;
    }
    setUploadingCsv(true);
    setErrorMsg(null);
    try {
      const res = await api.uploadTransactionsCSV(csvFile);
      setCsvReport(res);
      if (res.inserted_count > 0) {
        onSuccess(null);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'CSV upload failed.');
    } finally {
      setUploadingCsv(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-2xl bg-[#0c111e] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 md:p-5 border-b border-slate-800 flex items-center justify-between bg-[#080d19]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-700/60 text-cyan-400">
              <PlusCircle className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>Add Financial Transaction</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
                  Live Ledger Ingestion
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Ingest transactions with real-time ML risk scoring and optional multi-agent forensic triage.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Navigation if Admin */}
        {isAdmin && (
          <div className="flex border-b border-slate-800/80 bg-[#070b14] px-4">
            <button
              onClick={() => {
                setActiveTab('form');
                setErrorMsg(null);
              }}
              className={`py-2.5 px-4 text-xs font-mono font-medium border-b-2 transition ${
                activeTab === 'form'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Manual Single Ingestion
            </button>
            <button
              onClick={() => {
                setActiveTab('csv');
                setErrorMsg(null);
              }}
              className={`py-2.5 px-4 text-xs font-mono font-medium border-b-2 transition flex items-center gap-1.5 ${
                activeTab === 'csv'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
              Bulk CSV Upload (Admin)
            </button>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-4 md:p-6 overflow-y-auto space-y-4 text-xs">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {activeTab === 'form' ? (
            <>
              {/* Scenario Preset Buttons */}
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] font-mono text-slate-400">Quick Scenario Presets:</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleLoadSample('normal')}
                    className="px-2.5 py-1 rounded bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-700/60 text-emerald-300 text-[11px] font-mono transition cursor-pointer"
                  >
                    Load: Normal Payment ($84.50)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('drain')}
                    className="px-2.5 py-1 rounded bg-rose-950/60 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 text-[11px] font-mono transition cursor-pointer"
                  >
                    Load: Fraud-Like Drain ($489k)
                  </button>
                </div>
              </div>

              {/* Ingestion Form Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Transaction Type *
                  </label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="PAYMENT">PAYMENT (Merchant Payment)</option>
                    <option value="TRANSFER">TRANSFER (Account to Account)</option>
                    <option value="CASH_OUT">CASH_OUT (Atm / Counter Withdrawal)</option>
                    <option value="CASH_IN">CASH_IN (Deposit)</option>
                    <option value="DEBIT">DEBIT (Direct Debit)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Amount ($ USD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Origin Account (Sender) *
                  </label>
                  <input
                    type="text"
                    value={nameOrig}
                    onChange={(e) => setNameOrig(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Destination Account (Recipient) *
                  </label>
                  <input
                    type="text"
                    value={nameDest}
                    onChange={(e) => setNameDest(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Origin Old Balance *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={oldBalanceOrg}
                    onChange={(e) => setOldBalanceOrg(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Origin New Balance *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newBalanceOrig}
                    onChange={(e) => setNewBalanceOrig(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Destination Old Balance
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={oldBalanceDest}
                    onChange={(e) => setOldBalanceDest(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-mono text-[11px] mb-1">
                    Destination New Balance
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newBalanceDest}
                    onChange={(e) => setNewBalanceDest(e.target.value)}
                    className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:border-cyan-400 focus:outline-none"
                  />
                </div>
              </div>

              <div className="text-[10px] font-mono text-slate-500 pt-1">
                * Note: Evaluated without target label leakage. Ground-truth dataset label is assigned as NULL (unknown) for real production transactions.
              </div>
            </>
          ) : (
            /* CSV Upload Section (Admin) */
            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-xl p-6 text-center transition bg-[#080d19]">
                <UploadCloud className="h-8 w-8 text-cyan-400 mx-auto mb-2" />
                <div className="text-xs font-semibold text-slate-200">
                  Select CSV File for Bulk Ingestion
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Required headers: step, type, amount, name_orig, old_balance_org, new_balance_orig, name_dest
                </div>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
                  className="mt-3 text-xs text-slate-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-mono file:bg-cyan-950 file:text-cyan-300 hover:file:bg-cyan-900 cursor-pointer"
                />
              </div>

              {csvReport && (
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-emerald-400 font-semibold">
                      Successfully Ingested: {csvReport.inserted_count} rows
                    </span>
                    <span className="text-rose-400">
                      Errors: {csvReport.error_count} rows
                    </span>
                  </div>
                  {csvReport.errors && csvReport.errors.length > 0 && (
                    <div className="max-h-36 overflow-y-auto space-y-1 mt-2 text-[11px] font-mono text-rose-300">
                      {csvReport.errors.map((err: any, idx: number) => (
                        <div key={idx} className="p-1 rounded bg-rose-950/50">
                          Row {err.row}: {err.error}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Actions Footer */}
        <div className="p-4 md:p-5 border-t border-slate-800/80 bg-[#080d19] flex flex-wrap items-center justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-slate-700 text-slate-300 text-xs font-mono hover:bg-slate-800 transition"
          >
            Cancel
          </button>

          {activeTab === 'form' ? (
            <>
              <button
                type="button"
                onClick={() => handleSubmit(false)}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-mono font-semibold transition cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : 'Save only'}
              </button>

              <button
                type="button"
                onClick={() => handleSubmit(true)}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white text-xs font-mono font-semibold shadow-md transition cursor-pointer disabled:opacity-50"
              >
                <Zap className="h-3.5 w-3.5 text-amber-300" />
                <span>{isSubmitting ? 'Processing...' : 'Save & Run Agents'}</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleUploadCsvSubmit}
              disabled={uploadingCsv || !csvFile}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-semibold transition cursor-pointer disabled:opacity-50"
            >
              {uploadingCsv ? 'Ingesting Batch...' : 'Upload & Process CSV'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

