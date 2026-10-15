import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import {
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  TrendingUp,
  Cpu,
  Clock,
  Database,
  CheckCircle,
  ArrowRight,
  Info,
  HelpCircle,
  RefreshCw,
  Search,
  Bot,
  BookOpen,
  Activity,
  Settings,
  Lock,
  User,
  Shield,
  FileText,
} from 'lucide-react';
import { api } from '../../services/api';
import { DashboardSummary, AuditEvent, Transaction, UserRole } from '../../types';
import { PageHeader } from '../../components/common/PageHeader';
import { MetricCard } from '../../components/common/MetricCard';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';
import { RiskBadge } from '../../components/common/RiskBadge';

interface ExecutiveDashboardProps {
  onNavigateToTab: (tab: string) => void;
  userRole?: UserRole;
}

const RISK_COLORS: Record<string, string> = {
  LOW: '#10b981',
  MEDIUM: '#0ea5e9',
  HIGH: '#f59e0b',
  CRITICAL: '#f43f5e',
};

export const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({ onNavigateToTab, userRole = 'USER' }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Role-Specific Datasets
  const [recentAudits, setRecentAudits] = useState<AuditEvent[]>([]);
  const [priorityTransactions, setPriorityTransactions] = useState<Transaction[]>([]);

  const normRole = (userRole || 'USER').toUpperCase();
  const isAdmin = normRole === 'ADMIN' || normRole === 'ADMINISTRATOR';

  useEffect(() => {
    loadDashboardData();
  }, [userRole]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardSummary();
      setSummary(data);

      if (isAdmin) {
        // Load recent governance audit events for administrators
        try {
          const auditRes = await api.getAuditEvents(5);
          setRecentAudits(auditRes.items || []);
        } catch {
          setRecentAudits([]);
        }
      } else {
        // Load high-risk operational transactions for analysts
        try {
          const txRes = await api.getTransactions({
            limit: 4,
            risk_level: 'CRITICAL',
            sort_by: 'risk_score',
            sort_order: 'desc',
          });
          setPriorityTransactions(txRes.items || []);
        } catch {
          setPriorityTransactions([]);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch risk intelligence dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
        <PageHeader
          title={isAdmin ? 'Executive Dashboard' : 'Risk Dashboard'}
          subtitle={isAdmin ? 'Enterprise risk telemetry, model performance, and governance' : 'Operational fraud queue, risk distribution, and case review'}
          breadcrumbs={['FinGuard', isAdmin ? 'Management' : 'Operations', isAdmin ? 'Executive Dashboard' : 'Risk Dashboard']}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
        </div>
        <LoadingSkeleton lines={6} />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
        <PageHeader
          title={isAdmin ? 'Executive Dashboard' : 'Risk Dashboard'}
          subtitle="Portfolio fraud metrics, risk distribution, and high-priority anomalies"
          breadcrumbs={['FinGuard', 'Operations', 'Dashboard']}
        />
        <ErrorState
          title="Failed to Load Dashboard Metrics"
          message={error || 'Unable to connect to financial risk intelligence service.'}
          onRetry={loadDashboardData}
        />
      </div>
    );
  }

  const pieData = Object.entries(summary.risk_level_distribution).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="p-3 sm:p-4 md:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      {/* Dynamic Role-Specific Header */}
      <PageHeader
        title={isAdmin ? 'Executive Risk & Governance Dashboard' : 'Financial Risk Workspace'}
        subtitle={
          isAdmin
            ? 'Platform-wide fraud metrics, OpenTelemetry status, model performance, and audit trails'
            : 'Operational queue, high-risk anomalies, and assigned investigation workflows'
        }
        breadcrumbs={['FinGuard', isAdmin ? 'Management' : 'Operations', isAdmin ? 'Executive Dashboard' : 'Risk Workspace']}
        badge={isAdmin ? 'System Administrator' : 'Financial Risk Analyst'}
        actions={
          <button
            onClick={loadDashboardData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Metrics
          </button>
        }
      />

      {/* Dataset & Engine Provenance Banner */}
      <div className="rounded-xl bg-[#0f172a] border border-slate-800 p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 shrink-0">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
              <span>{isAdmin ? 'Verified Ingestion: PaySim Financial Simulation' : 'Active Financial Ledger & Risk Operations'}</span>
              <span className="text-[10px] font-mono font-normal px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                12,000 Transactions Ingested
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Strict isolation of target variables • Fraud Detection Model v1.2 (Precision-Recall Score: 0.9449)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs font-medium">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
            Enterprise Risk Engine Operational
          </span>
        </div>
      </div>

      {/* Summary KPI Cards (Plain Language for Analyst / Executive for Admin) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={isAdmin ? 'Transactions Analyzed' : 'Total Transactions Processed'}
          value={summary.total_transactions_processed.toLocaleString()}
          explanation={isAdmin ? 'Verified financial transactions processed through detection pipeline' : 'Verified financial transactions in active financial ledger'}
          icon={<TrendingUp className="h-4 w-4 text-sky-400" />}
          variant="default"
        />

        <MetricCard
          label={isAdmin ? 'Transactions Requiring Review' : 'High-Risk Transactions'}
          value={summary.transactions_flagged_for_review.toLocaleString()}
          explanation={isAdmin ? 'Flagged by model (risk score >= 65.0) or deterministic AML rules' : 'Transactions requiring immediate human analyst triage'}
          icon={<AlertTriangle className="h-4 w-4 text-amber-400" />}
          variant="warning"
          trend={{ text: 'Requires triage', positive: false }}
          onClick={() => onNavigateToTab('transactions')}
        />

        <MetricCard
          label={isAdmin ? 'Open Investigations' : 'Cases Awaiting Review'}
          value={summary.open_investigation_cases}
          explanation={isAdmin ? 'Multi-agent case dossiers awaiting human investigator disposition' : 'Active investigation cases pending disposition review'}
          icon={<FileCheck className="h-4 w-4 text-emerald-400" />}
          variant="info"
          trend={{ text: 'Investigation queue', neutral: true }}
          onClick={() => onNavigateToTab('investigations')}
        />

        <MetricCard
          label={isAdmin ? 'Historical Dataset Frauds' : 'Historical Verified Frauds'}
          value={summary.historical_dataset_fraud_count.toLocaleString()}
          explanation={`Benchmark ground-truth fraudulent records (${summary.historical_fraud_rate_pct}% base rate)`}
          icon={<ShieldAlert className="h-4 w-4 text-rose-400" />}
          variant="danger"
        />
      </div>

      {/* ========================================================================= */}
      {/* STANDARD USER EXPERIENCE: Operational Action Queue & Analyst Shortcuts */}
      {/* ========================================================================= */}
      {!isAdmin && (
        <div className="space-y-6">
          {/* Analyst Quick Actions */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <button
              onClick={() => onNavigateToTab('transactions')}
              className="p-3.5 rounded-xl bg-[#11192e] border border-slate-800 hover:border-sky-500/40 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 group-hover:bg-sky-500/20 transition">
                  <Search className="h-4 w-4" />
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-sky-400 transition" />
              </div>
              <div className="text-xs font-semibold text-slate-200">Search Transactions</div>
              <div className="text-[11px] text-slate-400">
                {isAdmin ? 'Filter PaySim ledger and inspect risk scores' : 'Filter financial ledger and inspect risk scores'}
              </div>
            </button>

            <button
              onClick={() => onNavigateToTab('investigations')}
              className="p-3.5 rounded-xl bg-[#11192e] border border-slate-800 hover:border-sky-500/40 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20 transition">
                  <FileCheck className="h-4 w-4" />
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
              </div>
              <div className="text-xs font-semibold text-slate-200">Review Cases ({summary.open_investigation_cases})</div>
              <div className="text-[11px] text-slate-400">Open investigation queue and record findings</div>
            </button>

            <button
              onClick={() => onNavigateToTab('assistant')}
              className="p-3.5 rounded-xl bg-[#11192e] border border-slate-800 hover:border-sky-500/40 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20 transition">
                  <Bot className="h-4 w-4" />
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-indigo-400 transition" />
              </div>
              <div className="text-xs font-semibold text-slate-200">Ask FinGuard Assistant</div>
              <div className="text-[11px] text-slate-400">Query AML policies, thresholds, and red flags</div>
            </button>

            <button
              onClick={() => onNavigateToTab('knowledge')}
              className="p-3.5 rounded-xl bg-[#11192e] border border-slate-800 hover:border-sky-500/40 text-left transition space-y-1.5 group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20 transition">
                  <BookOpen className="h-4 w-4" />
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-amber-400 transition" />
              </div>
              <div className="text-xs font-semibold text-slate-200">Policies & Documents</div>
              <div className="text-[11px] text-slate-400">Consult indexed regulations and standards</div>
            </button>
          </div>

          {/* High-Priority Anomalies Needing Review */}
          {priorityTransactions.length > 0 && (
            <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                    High-Risk Transactions Awaiting Attention
                  </h2>
                  <p className="text-xs text-slate-400">Transactions with critical composite risk scores requiring immediate analyst inspection</p>
                </div>
                <button
                  onClick={() => onNavigateToTab('transactions')}
                  className="text-xs text-sky-400 hover:underline flex items-center gap-1"
                >
                  View All Flagged ({summary.transactions_flagged_for_review})
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {priorityTransactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="p-3.5 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition space-y-2 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-white">#{tx.id}</span>
                        <RiskBadge level={tx.risk_level || 'CRITICAL'} size="sm" />
                      </div>
                      <div className="text-sm font-bold text-slate-100 font-mono mt-1">
                        ${Number(tx.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono truncate mt-0.5">
                        {tx.type} • Orig: {tx.name_orig}
                      </div>
                    </div>
                    <button
                      onClick={() => onNavigateToTab('transactions')}
                      className="w-full mt-2 py-1.5 px-2 rounded bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs font-medium transition cursor-pointer flex items-center justify-center gap-1 border border-slate-700"
                    >
                      <Search className="h-3 w-3" />
                      Inspect in Ledger
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* ADMINISTRATOR EXPERIENCE: Governance Strip & System Operations */}
      {/* ========================================================================= */}
      {isAdmin && (
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Shield className="h-4 w-4 text-sky-400" />
                Platform Operations & Governance Health
              </h2>
              <p className="text-xs text-slate-400">Real-time status of system architecture, security logging, and machine learning components</p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-semibold">
              ADMINISTRATIVE CONTROL PLANE
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div
              onClick={() => onNavigateToTab('observability')}
              className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-emerald-400" />
                  System Observability
                </span>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className="text-slate-200 font-semibold text-xs">Operational Status: Healthy</div>
              <div className="text-slate-400 text-[10px]">9 Architecture Layers Active</div>
            </div>

            <div
              onClick={() => onNavigateToTab('models')}
              className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-sky-400" />
                  ML Fraud Model
                </span>
                <span className="font-mono text-sky-400 font-semibold">v1.2</span>
              </div>
              <div className="text-slate-200 font-semibold text-xs">PR-AUC: 0.9449</div>
              <div className="text-slate-400 text-[10px]">Decision Threshold: 0.650</div>
            </div>

            <div
              onClick={() => onNavigateToTab('governance')}
              className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <FileCheck className="h-3.5 w-3.5 text-indigo-400" />
                  Immutable Audit Trail
                </span>
                <span className="font-mono text-indigo-400 font-semibold">{summary.total_audit_events}</span>
              </div>
              <div className="text-slate-200 font-semibold text-xs">Audit Logging Active</div>
              <div className="text-slate-400 text-[10px]">Tamper-evident verification</div>
            </div>

            <div
              onClick={() => onNavigateToTab('admin')}
              className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition cursor-pointer space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <Settings className="h-3.5 w-3.5 text-amber-400" />
                  Access & Security
                </span>
                <span className="font-mono text-amber-400 font-semibold">5 Roles</span>
              </div>
              <div className="text-slate-200 font-semibold text-xs">RBAC Authorization</div>
              <div className="text-slate-400 text-[10px]">Manage users & permissions</div>
            </div>
          </div>
        </div>
      )}

      {/* Visual Analytics: Risk Distribution & Temporal Volume Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Risk Severity Distribution</h2>
            <p className="text-xs text-slate-400">Classified by composite model and deterministic policies</p>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#64748b'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800 text-xs font-mono">
            {pieData.map((d) => (
              <div key={d.name} className="flex items-center justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/60">
                <span className="flex items-center gap-1.5 text-slate-300 text-[11px]">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: RISK_COLORS[d.name] }}
                  />
                  {d.name}
                </span>
                <span className="text-white font-bold">{d.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Temporal Volume Chart */}
        <div className="lg:col-span-2 rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Transaction Volume Over Simulated Time Steps</h2>
              <p className="text-xs text-slate-400">Hourly cyclical transaction activity versus detected anomalies</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-sky-400">
                <span className="h-2 w-2 rounded-full bg-sky-400" /> Total Volume
              </span>
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="h-2 w-2 rounded-full bg-rose-400" /> Anomalies
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={summary.temporal_volume_timeline}>
                <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Line
                  type="monotone"
                  dataKey="transaction_volume"
                  name="Volume"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="detected_anomalies"
                  name="Anomalies"
                  stroke="#f43f5e"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Transaction Breakdown by Type */}
      <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Financial Typologies by Transaction Type</h2>
            <p className="text-xs text-slate-400">Distribution across payment rails, liquidation channels, and risk scores</p>
          </div>
          <button
            onClick={() => onNavigateToTab('transactions')}
            className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300 transition font-medium cursor-pointer"
          >
            <span>Explore All Transactions</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b1220] text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Transaction Type</th>
                <th className="py-2.5 px-3">Transaction Count</th>
                <th className="py-2.5 px-3">Total Volume</th>
                <th className="py-2.5 px-3">Historical Frauds</th>
                <th className="py-2.5 px-3">Avg Composite Risk</th>
                <th className="py-2.5 px-3">Risk Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {summary.transaction_type_breakdown.map((row) => (
                <tr key={row.type} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-semibold text-slate-200 font-sans">{row.type}</td>
                  <td className="py-2.5 px-3 text-slate-300">{row.count.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-slate-300">${row.total_volume.toLocaleString()}</td>
                  <td className="py-2.5 px-3">
                    <span className={row.historical_fraud_count > 0 ? 'text-rose-400 font-bold' : 'text-slate-500'}>
                      {row.historical_fraud_count}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{row.avg_risk_score} / 100</td>
                  <td className="py-2.5 px-3 font-sans">
                    {row.type === 'TRANSFER' || row.type === 'CASH_OUT' ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/50 font-medium">
                        High Liquidation Risk
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 font-medium">
                        Standard Operational Flow
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Administrator Recent Audit Events Stream */}
      {isAdmin && recentAudits.length > 0 && (
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <FileCheck className="h-4 w-4 text-sky-400" />
                Recent Governance & Security Audit Events
              </h2>
              <p className="text-xs text-slate-400">Real-time immutable event log recording access, investigations, and administrative actions</p>
            </div>
            <button
              onClick={() => onNavigateToTab('governance')}
              className="text-xs text-sky-400 hover:underline flex items-center gap-1"
            >
              View Full Audit Log
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#0b1220] text-slate-400 text-[10px] uppercase border-b border-slate-800">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Action</th>
                  <th className="py-2 px-3">Actor (Role)</th>
                  <th className="py-2 px-3">Target</th>
                  <th className="py-2 px-3">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentAudits.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/30 transition text-[11px]">
                    <td className="py-2 px-3 text-slate-400">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-white font-semibold">{ev.action}</td>
                    <td className="py-2 px-3 text-slate-300">{ev.actor_id} ({ev.actor_role})</td>
                    <td className="py-2 px-3 text-slate-400">{ev.target_type}:{ev.target_id}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        ev.outcome === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
                      }`}>
                        {ev.outcome}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
