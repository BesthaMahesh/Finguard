import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Info,
  X,
  ExternalLink,
  SlidersHorizontal,
  HelpCircle,
  RefreshCw,
  TrendingUp,
  ArrowLeft,
  Clock,
  History,
  FileText,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  User,
  Building,
} from 'lucide-react';
import { api } from '../../services/api';
import { Transaction, FeatureContribution, RuleViolation } from '../../types';
import { RiskBadge, RiskMeter } from '../../components/common/RiskBadge';
import { PageHeader } from '../../components/common/PageHeader';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { ErrorBoundary } from '../../components/common/ErrorBoundary';
import { Modal } from '../../components/common/Modal';

interface TransactionIntelligenceProps {
  onOpenCase: (txId: number) => void;
}

const formatCurrency = (val: number | null | undefined): string => {
  if (val === null || val === undefined || isNaN(val)) return '$0.00';
  return '$' + Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatNumber = (val: number | null | undefined): string => {
  if (val === null || val === undefined || isNaN(val)) return '0.00';
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const parseRuleFlags = (flags: any): RuleViolation[] => {
  if (!flags) return [];
  if (typeof flags === 'string') {
    try {
      const parsed = JSON.parse(flags);
      return parseRuleFlags(parsed);
    } catch {
      const list = flags.includes(',') ? flags.split(',') : [flags];
      return list.map((item: string, idx: number) => ({
        rule_id: item.trim() || `RULE-${idx + 1}`,
        name: item.trim().replace(/_/g, ' ') || 'Flagged Rule',
        penalty: 15,
        description: 'Triggered business rule threshold'
      }));
    }
  }
  if (Array.isArray(flags)) {
    return flags.map((item: any, idx: number) => {
      if (typeof item === 'string') {
        return {
          rule_id: item || `RULE-${idx + 1}`,
          name: item.replace(/_/g, ' ') || 'Flagged Rule',
          penalty: 15,
          description: 'Triggered business rule threshold'
        };
      }
      if (item && typeof item === 'object') {
        return {
          rule_id: item.rule_id || item.id || `RULE-${idx + 1}`,
          name: item.name || item.rule_name || item.rule_id || 'Flagged Rule',
          penalty: typeof item.penalty === 'number' ? item.penalty : 10,
          description: item.description || ''
        };
      }
      return {
        rule_id: `RULE-${idx + 1}`,
        name: String(item),
        penalty: 10,
        description: ''
      };
    });
  }
  return [];
};

export const TransactionIntelligence: React.FC<TransactionIntelligenceProps> = ({ onOpenCase }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedTx, setSelectedTx] = useState<(Transaction & { rule_flags?: RuleViolation[]; feature_contributions?: FeatureContribution[]; audit_history?: any[] }) | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState<string | null>(null);

  // Filter & Pagination States
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;
  const [sortBy, setSortBy] = useState('risk_score');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    fetchTransactions();
  }, [page, typeFilter, riskFilter, sortBy, sortOrder]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const res = await api.getTransactions({
        limit,
        offset: page * limit,
        type: typeFilter || undefined,
        risk_level: riskFilter || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setTransactions(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to query transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchTransactions();
  };

  const openDetailDrawer = async (tx: Transaction) => {
    try {
      setDrawerLoading(true);
      setDrawerError(null);
      setSelectedTx({
        ...tx,
        rule_flags: parseRuleFlags(tx.rule_flags),
        feature_contributions: [],
        audit_history: []
      } as any);
      const detail = await api.getTransactionDetail(tx.id);
      setSelectedTx({
        ...detail,
        rule_flags: parseRuleFlags(detail.rule_flags),
        feature_contributions: Array.isArray(detail.feature_contributions) ? detail.feature_contributions : [],
        audit_history: Array.isArray((detail as any).audit_history) ? (detail as any).audit_history : []
      } as any);
    } catch (err: any) {
      console.error('Failed to load transaction detail:', err);
      setDrawerError(err.message || 'Failed to fetch complete transaction details.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <ErrorBoundary fallbackTitle="Transactions Module Error">
      <div className="p-3 sm:p-4 md:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
        <PageHeader
          title="Transactions"
          subtitle="Audit, search, and analyze financial transaction flows with calibrated risk assessments"
          breadcrumbs={['FinGuard', 'Operations', 'Transactions']}
          actions={
            <button
              onClick={fetchTransactions}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
          }
        />

        {/* Search & Filters Bar */}
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-4 space-y-3 shadow-sm">
          <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search origin account (e.g. C123...), destination entity (e.g. M987...), or transaction ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition cursor-pointer"
            >
              Search
            </button>
          </form>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5 text-slate-400">
                <Filter className="h-3.5 w-3.5 text-slate-500" />
                <span>Filters:</span>
              </div>

              {/* Type Filter */}
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value);
                  setPage(0);
                }}
                className="bg-[#0a0f1d] border border-slate-700/80 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="">All Typologies</option>
                <option value="TRANSFER">TRANSFER (Liquidation)</option>
                <option value="CASH_OUT">CASH_OUT (ATM/Branch)</option>
                <option value="PAYMENT">PAYMENT (Merchant)</option>
                <option value="CASH_IN">CASH_IN (Deposit)</option>
                <option value="DEBIT">DEBIT (Direct Debit)</option>
              </select>

              {/* Risk Level Filter */}
              <select
                value={riskFilter}
                onChange={(e) => {
                  setRiskFilter(e.target.value);
                  setPage(0);
                }}
                className="bg-[#0a0f1d] border border-slate-700/80 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="">All Risk Tiers</option>
                <option value="CRITICAL">CRITICAL (&ge; 85)</option>
                <option value="HIGH">HIGH (65 - 84)</option>
                <option value="MEDIUM">MEDIUM (40 - 64)</option>
                <option value="LOW">LOW (&lt; 40)</option>
              </select>
            </div>

            {/* Sorting */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-[#0a0f1d] border border-slate-700/80 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-sky-500 cursor-pointer"
              >
                <option value="risk_score">Risk Score</option>
                <option value="amount">Amount</option>
                <option value="step">Step (Time)</option>
                <option value="id">Transaction ID</option>
              </select>

              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-1 rounded bg-[#0a0f1d] border border-slate-700/80 text-slate-300 hover:text-white transition cursor-pointer"
                title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
              >
                <ArrowUpDown className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Transactions Table View */}
        {loading ? (
          <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-6 space-y-4">
            <LoadingSkeleton lines={8} />
          </div>
        ) : transactions.length === 0 ? (
          <EmptyState
            title="No Transactions Match Filters"
            description="Adjust your typology, risk tier, or search keyword to review ledger records."
          />
        ) : (
          <div className="rounded-xl bg-[#11192e] border border-slate-800/80 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0b1220] border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                  <tr>
                    <th className="px-4 py-3">Tx ID</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3 text-right">Amount (USD)</th>
                    <th className="px-4 py-3">Origin</th>
                    <th className="px-4 py-3">Destination</th>
                    <th className="px-4 py-3">Model Prob.</th>
                    <th className="px-4 py-3">Risk Tier</th>
                    <th className="px-4 py-3">Ground Truth</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {transactions.map((tx) => (
                    <tr
                      key={tx.id}
                      onClick={() => openDetailDrawer(tx)}
                      className="hover:bg-slate-800/30 transition cursor-pointer group"
                    >
                      <td className="px-4 py-3 text-sky-400 font-bold group-hover:underline">
                        #{tx.id}
                      </td>
                      <td className="px-4 py-3 font-sans">
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[11px] font-mono">
                          {tx.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-slate-200 font-medium">
                        {formatCurrency(tx.amount)}
                      </td>
                      <td className="px-4 py-3 text-slate-300 truncate max-w-[120px]">{tx.name_orig}</td>
                      <td className="px-4 py-3 text-slate-300 truncate max-w-[120px]">{tx.name_dest}</td>
                      <td className="px-4 py-3 text-slate-300">
                        {tx.fraud_probability !== undefined && tx.fraud_probability !== null
                          ? `${(tx.fraud_probability * 100).toFixed(1)}%`
                          : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <RiskBadge level={tx.risk_level || 'LOW'} size="sm" />
                      </td>
                      <td className="px-4 py-3 font-sans">
                        {tx.is_fraud === 1 ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800 font-mono">
                            FRAUD
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500 font-mono">Normal</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-sans">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            openDetailDrawer(tx);
                          }}
                          className="text-xs text-sky-400 hover:text-sky-300 font-medium hover:underline cursor-pointer"
                        >
                          Inspect &rarr;
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="p-4 border-t border-slate-800/80 bg-[#0b1220] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="text-slate-400 font-mono">
                Showing <strong className="text-slate-200">{page * limit + 1}</strong> to{' '}
                <strong className="text-slate-200">{Math.min(total, (page + 1) * limit)}</strong> of{' '}
                <strong className="text-slate-200">{total.toLocaleString()}</strong> transactions
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <span className="text-slate-400 font-mono">
                  Page {page + 1} of {Math.max(1, totalPages)}
                </span>
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(page + 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-300 hover:text-white disabled:opacity-40 transition cursor-pointer"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Centered Transaction Inspection Modal */}
        {selectedTx && (
          <Modal
            isOpen={!!selectedTx}
            onClose={() => setSelectedTx(null)}
            maxWidth="5xl"
            icon={<FileText className="h-5 w-5 text-sky-400" />}
            title={
              <span className="flex items-center gap-2">
                <span>Transaction #{selectedTx.id}</span>
                <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {selectedTx.type}
                </span>
              </span>
            }
            subtitle={`Time Step: ${selectedTx.step} • Initial Settlement Status: ${selectedTx.status || 'UNREVIEWED'}`}
            badge={<RiskBadge level={selectedTx.risk_level || 'LOW'} size="sm" />}
            actions={
              <div className="flex items-center justify-between w-full">
                <button
                  onClick={() => setSelectedTx(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition cursor-pointer"
                >
                  Close Inspection
                </button>
                <div className="flex items-center gap-2">
                  {selectedTx.investigation ? (
                    <button
                      onClick={() => {
                        setSelectedTx(null);
                        onOpenCase(selectedTx.id);
                      }}
                      className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium flex items-center gap-1.5 transition cursor-pointer shadow-lg shadow-sky-950/40"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open Investigation ({selectedTx.investigation.case_number})
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setSelectedTx(null);
                        onOpenCase(selectedTx.id);
                      }}
                      className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium flex items-center gap-1.5 transition cursor-pointer shadow-lg shadow-sky-950/40"
                    >
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Initiate Investigation Case
                    </button>
                  )}
                </div>
              </div>
            }
          >
            <div className="space-y-5">
              {/* Drawer Error Notice */}
              {drawerError && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center justify-between">
                  <span>{drawerError}</span>
                  <button
                    onClick={() => openDetailDrawer(selectedTx)}
                    className="text-sky-400 hover:underline font-mono text-[11px] ml-2"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Core Transaction Value Card */}
              <div className="rounded-xl bg-[#0b1220] border border-slate-800 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider font-mono">
                    Transaction Amount
                  </span>
                  <div className="text-2xl font-bold text-white font-mono mt-0.5">
                    {formatCurrency(selectedTx.amount)} <span className="text-xs text-slate-400 font-sans">USD</span>
                  </div>
                </div>
                <div className="sm:text-right">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider font-mono">
                    Settlement Status
                  </span>
                  <div className="text-xs font-semibold text-slate-200 font-mono mt-0.5">
                    {selectedTx.status || 'UNREVIEWED'}
                  </div>
                </div>
              </div>

              {/* Comparative Analysis: Model Prediction vs Ground-Truth Label */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Model Risk Assessment */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-sky-300 font-mono uppercase tracking-wider">
                      AI Model Risk Prediction
                    </span>
                    <RiskBadge level={selectedTx.risk_level || 'LOW'} size="sm" />
                  </div>
                  <RiskMeter score={selectedTx.risk_score || 0} threshold={65} />
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Estimated Fraud Likelihood:</span>
                    <span className="font-mono text-white font-bold">
                      {selectedTx.fraud_probability !== undefined && selectedTx.fraud_probability !== null
                        ? `${(selectedTx.fraud_probability * 100).toFixed(2)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">
                    Calculated by calibrated Random Forest + deterministic heuristics.
                  </p>
                </div>

                {/* Dataset Ground Truth */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
                  <span className="text-xs font-semibold text-amber-300 font-mono uppercase tracking-wider">
                    Historical Dataset Ground Truth
                  </span>
                  <div className="pt-1">
                    {selectedTx.is_fraud === 1 ? (
                      <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-200 text-xs font-bold font-mono flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                        <span>CONFIRMED FRAUD (Dataset Label)</span>
                      </div>
                    ) : (
                      <div className="p-2.5 rounded-lg bg-emerald-950/50 border border-emerald-800 text-emerald-200 text-xs font-bold font-mono flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                        <span>NORMAL TRANSACTION</span>
                      </div>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight pt-1">
                    Historical benchmark settlement label. Isolated from model scoring features to prevent target leakage.
                  </p>
                </div>
              </div>

              {/* Associated Investigation Case */}
              <div className="p-4 rounded-xl bg-[#0e172a] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <ShieldAlert className="h-4 w-4 text-sky-400" />
                    Associated Investigation Case
                  </span>
                  {selectedTx.investigation ? (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Active Case Exists
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono text-slate-500">None</span>
                  )}
                </div>

                {selectedTx.investigation ? (
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-white font-bold">{selectedTx.investigation.case_number}</span>
                      <span className="text-slate-400 text-[11px]">
                        Status: <strong className="text-slate-200">{selectedTx.investigation.status}</strong>
                      </span>
                    </div>
                    <p className="text-xs text-slate-300">{selectedTx.investigation.title}</p>
                    <button
                      onClick={() => {
                        setSelectedTx(null);
                        onOpenCase(selectedTx.id);
                      }}
                      className="w-full mt-2 py-2 px-3 rounded-lg bg-sky-600/90 hover:bg-sky-600 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition cursor-pointer"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open in Investigation Workbench
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2 pt-1">
                    <p className="text-xs text-slate-400">
                      No active investigation dossier has been opened for transaction #{selectedTx.id}.
                    </p>
                    <button
                      onClick={() => {
                        setSelectedTx(null);
                        onOpenCase(selectedTx.id);
                      }}
                      className="w-full mt-1 py-2 px-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition cursor-pointer"
                    >
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Initiate Investigation Case
                    </button>
                  </div>
                )}
              </div>

              {/* Ledger Flow Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                  Ledger Flow Accounts & Balances
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                      <User className="h-3.5 w-3.5 text-sky-400" />
                      <span>Origin Account</span>
                    </div>
                    <div className="font-mono text-white font-bold truncate">{selectedTx.name_orig}</div>
                    <div className="text-[11px] text-slate-300 font-mono space-y-0.5 pt-1">
                      <div>Initial: {formatCurrency(selectedTx.old_balance_org)}</div>
                      <div>Post-Tx: {formatCurrency(selectedTx.new_balance_orig)}</div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                      <Building className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Destination Entity</span>
                    </div>
                    <div className="font-mono text-white font-bold truncate">{selectedTx.name_dest}</div>
                    <div className="text-[11px] text-slate-300 font-mono space-y-0.5 pt-1">
                      <div>Initial: {formatCurrency(selectedTx.old_balance_dest)}</div>
                      <div>Post-Tx: {formatCurrency(selectedTx.new_balance_dest)}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Triggered Business Rules */}
              {(() => {
                const ruleFlags = parseRuleFlags(selectedTx.rule_flags);
                if (ruleFlags.length === 0) return null;
                return (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                      Triggered Rules ({ruleFlags.length})
                    </h4>
                    <div className="space-y-2">
                      {ruleFlags.map((r: RuleViolation, idx: number) => (
                        <div key={idx} className="p-3 rounded-lg bg-amber-950/30 border border-amber-900/50 text-xs">
                          <div className="flex justify-between items-center text-amber-300 font-semibold">
                            <span>{r.name || r.rule_id}</span>
                            <span className="font-mono text-[10px]">Penalty: +{r.penalty}</span>
                          </div>
                          {r.description && <div className="text-slate-300 text-[11px] mt-1">{r.description}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}

              {/* Model Explainability / SHAP */}
              {(() => {
                const featureContributions = Array.isArray(selectedTx.feature_contributions) ? selectedTx.feature_contributions : [];
                if (featureContributions.length === 0) return null;
                return (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                      Feature Importance & SHAP Drivers
                    </h4>
                    <div className="space-y-1.5">
                      {featureContributions.map((f: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
                        >
                          <div>
                            <div className="font-medium text-slate-200">{f.display_name || f.feature_name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">Value: {formatNumber(f.feature_value)}</div>
                          </div>
                          <span
                            className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                              f.impact === 'INCREASES_RISK'
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            {f.impact === 'INCREASES_RISK' ? '+ Risk' : '- Risk'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}

              {/* Audit History */}
              {(() => {
                const auditHistory = Array.isArray((selectedTx as any).audit_history) ? (selectedTx as any).audit_history : [];
                if (auditHistory.length === 0) return null;
                return (
                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                      <History className="h-3.5 w-3.5 text-slate-400" />
                      Recorded Audit Events
                    </h4>
                    <div className="space-y-1.5">
                      {auditHistory.map((a: any, idx: number) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800 text-[11px] font-mono flex items-center justify-between">
                          <span className="text-slate-200 font-semibold">{a.action}</span>
                          <span className="text-slate-400">{a.actor_id} ({a.actor_role})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          </Modal>
        )}
      </div>
    </ErrorBoundary>
  );
};
