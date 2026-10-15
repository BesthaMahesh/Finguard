import React, { useEffect, useState } from 'react';
import {
  FileCheck,
  Search,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Lock,
  Key,
  Filter,
  RefreshCw,
  Clock,
  User,
  Shield,
} from 'lucide-react';
import { api } from '../../services/api';
import { AuditEvent } from '../../types';
import { PageHeader } from '../../components/common/PageHeader';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { EmptyState } from '../../components/common/EmptyState';

export const GovernanceAudit: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('');

  useEffect(() => {
    loadAuditEvents();
  }, [actionFilter, outcomeFilter]);

  const loadAuditEvents = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditEvents(50);
      setEvents(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      ev.action.toLowerCase().includes(q) ||
      ev.actor_id.toLowerCase().includes(q) ||
      ev.actor_role.toLowerCase().includes(q) ||
      ev.target_id.toLowerCase().includes(q) ||
      (ev.correlation_id && ev.correlation_id.toLowerCase().includes(q));

    const matchesAction = !actionFilter || ev.action === actionFilter;
    const matchesOutcome = !outcomeFilter || ev.outcome === outcomeFilter;
    return matchesSearch && matchesAction && matchesOutcome;
  });

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Security & Audit"
        subtitle="Structured audit trail, authentication events, and role-based permissions matrix"
        breadcrumbs={['FinGuard', 'Governance', 'Security & Audit']}
        badge={`${total} Stored Events`}
        actions={
          <button
            onClick={loadAuditEvents}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Log
          </button>
        }
      />

      {/* Role-Based Access Control Entitlements Table */}
      <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-3 shadow-sm">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Lock className="h-4 w-4 text-sky-400" />
            Active Role Entitlements & Permissions Matrix
          </h3>
          <p className="text-xs text-slate-400">
            Authorization enforced by backend API dependencies on every request
          </p>
        </div>

        <div className="overflow-x-auto pt-1">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0b1220] text-slate-400 border-b border-slate-800 font-sans text-[10px] uppercase">
              <tr>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Risk Dashboard</th>
                <th className="py-2.5 px-3">Transactions</th>
                <th className="py-2.5 px-3">Investigations & Review</th>
                <th className="py-2.5 px-3">Risk Assistant & Docs</th>
                <th className="py-2.5 px-3">Audit Logs</th>
                <th className="py-2.5 px-3">User & System Admin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              <tr className="hover:bg-slate-800/20 transition">
                <td className="py-2.5 px-3 font-bold text-sky-400 font-mono">
                  USER (Standard User)
                </td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES (Review Notes)</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES</td>
                <td className="py-2.5 px-3 text-rose-400 font-bold">NO (Restricted to Admin)</td>
                <td className="py-2.5 px-3 text-rose-400 font-bold">NO (Restricted)</td>
              </tr>
              <tr className="hover:bg-slate-800/20 transition">
                <td className="py-2.5 px-3 font-bold text-purple-400 font-mono">
                  ADMIN (Administrator)
                </td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES (Full)</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES (Full)</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES (Full)</td>
                <td className="py-2.5 px-3 text-emerald-400 font-bold">YES (Manage Users & Config)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-4 space-y-3 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter by action, actor, target, or correlation ID..."
              className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="bg-[#0a0f1d] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Action Types</option>
              <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
              <option value="LOGIN_FAILED">LOGIN_FAILED</option>
              <option value="LOGIN_DENIED">LOGIN_DENIED</option>
              <option value="USER_STATUS_CHANGE">USER_STATUS_CHANGE</option>
              <option value="PASSWORD_RESET">PASSWORD_RESET</option>
              <option value="CASE_DISPOSITION_UPDATE">CASE_DISPOSITION_UPDATE</option>
            </select>

            <select
              value={outcomeFilter}
              onChange={(e) => setOutcomeFilter(e.target.value)}
              className="bg-[#0a0f1d] border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="">All Outcomes</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAILURE">FAILURE</option>
              <option value="DENIED">DENIED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      {loading ? (
        <LoadingSkeleton lines={6} />
      ) : filteredEvents.length === 0 ? (
        <EmptyState
          title="No Audit Records Found"
          description="No security or audit events matched your filter criteria."
        />
      ) : (
        <div className="rounded-xl border border-slate-800/80 bg-[#11192e] overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#0b1220] border-b border-slate-800/80 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Timestamp (UTC)</th>
                  <th className="px-4 py-3">Actor / Role</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Outcome</th>
                  <th className="px-4 py-3">Correlation ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredEvents.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 text-slate-400 text-[11px]">
                      {new Date(ev.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-200">{ev.actor_id}</div>
                      <div className="text-[10px] text-slate-500 uppercase">{ev.actor_role}</div>
                    </td>
                    <td className="px-4 py-3 text-sky-300 font-semibold">{ev.action}</td>
                    <td className="px-4 py-3 text-slate-300">
                      <span className="text-[10px] text-slate-500">{ev.target_type}: </span>
                      {ev.target_id}
                    </td>
                    <td className="px-4 py-3 font-sans">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold font-mono ${
                          ev.outcome === 'SUCCESS'
                            ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                            : 'bg-rose-950/80 text-rose-300 border border-rose-800'
                        }`}
                      >
                        {ev.outcome === 'SUCCESS' ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : (
                          <XCircle className="h-3 w-3" />
                        )}
                        {ev.outcome}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-[10px] truncate max-w-[140px]">
                      {ev.correlation_id}
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
