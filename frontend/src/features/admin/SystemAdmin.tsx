import React, { useEffect, useState } from 'react';
import {
  Users,
  ShieldCheck,
  KeyRound,
  UserX,
  UserCheck,
  Settings,
  Server,
  Database,
  Cpu,
  Code,
  Play,
  CheckCircle2,
  AlertTriangle,
  Lock,
  RefreshCw,
  Search,
} from 'lucide-react';
import { api } from '../../services/api';
import { UserProfile, UserManagementItem } from '../../types';
import { PageHeader } from '../../components/common/PageHeader';
import { ConfirmActionDialog } from '../../components/common/ConfirmActionDialog';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

interface SystemAdminProps {
  currentUser?: UserProfile;
}

export const SystemAdmin: React.FC<SystemAdminProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'mcp' | 'infrastructure'>('users');
  const [users, setUsers] = useState<UserManagementItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userSearch, setUserSearch] = useState('');

  // User Actions State
  const [selectedUserForStatus, setSelectedUserForStatus] = useState<UserManagementItem | null>(null);
  const [statusConfirmOpen, setStatusConfirmOpen] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);

  const [selectedUserForReset, setSelectedUserForReset] = useState<UserManagementItem | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ message: string; isError?: boolean } | null>(null);

  // MCP Interactive Runner State
  const [mcpData, setMcpData] = useState<{ server: string; protocol: string; tools: any[] } | null>(null);
  const [selectedTool, setSelectedTool] = useState('lookup_transaction');
  const [toolArgs, setToolArgs] = useState('{\n  "transaction_id": 1\n}');
  const [toolResult, setToolResult] = useState<any>(null);
  const [executingTool, setExecutingTool] = useState(false);

  useEffect(() => {
    loadUsers();
    loadMcpData();
  }, []);

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const data = await api.getUsers();
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const loadMcpData = async () => {
    try {
      const data = await api.getMCPTools();
      setMcpData(data);
    } catch (err) {
      console.error('Failed to load MCP tools:', err);
    }
  };

  const handleToggleStatusClick = (u: UserManagementItem) => {
    if (currentUser && u.id === currentUser.id && u.is_active) {
      setActionFeedback({
        message: 'Security safeguard: You cannot disable your own active administrator account.',
        isError: true,
      });
      return;
    }
    setSelectedUserForStatus(u);
    setStatusConfirmOpen(true);
  };

  const handleConfirmStatusToggle = async () => {
    if (!selectedUserForStatus) return;
    try {
      setStatusLoading(true);
      const newStatus = !selectedUserForStatus.is_active;
      await api.updateUserStatus(selectedUserForStatus.id, newStatus);
      setActionFeedback({
        message: `Account "${selectedUserForStatus.username}" status updated to ${
          newStatus ? 'Active' : 'Disabled'
        }.`,
      });
      setStatusConfirmOpen(false);
      loadUsers();
    } catch (err: any) {
      setActionFeedback({ message: err.message || 'Failed to update account status.', isError: true });
    } finally {
      setStatusLoading(false);
    }
  };

  const handleOpenResetModal = (u: UserManagementItem) => {
    setSelectedUserForReset(u);
    setNewPassword('');
    setResetModalOpen(true);
  };

  const handleExecutePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserForReset || !newPassword.trim()) return;

    if (newPassword.trim().length < 4) {
      setActionFeedback({ message: 'Password must be at least 4 characters in length.', isError: true });
      return;
    }

    try {
      setResetLoading(true);
      await api.resetUserPassword(selectedUserForReset.id, newPassword.trim());
      setActionFeedback({
        message: `Password for user "${selectedUserForReset.username}" has been updated successfully.`,
      });
      setResetModalOpen(false);
      setNewPassword('');
    } catch (err: any) {
      setActionFeedback({ message: err.message || 'Failed to reset password.', isError: true });
    } finally {
      setResetLoading(false);
    }
  };

  const handleToolSelect = (toolName: string) => {
    setSelectedTool(toolName);
    if (toolName === 'lookup_transaction') {
      setToolArgs('{\n  "transaction_id": 1\n}');
    } else if (toolName === 'lookup_account') {
      setToolArgs('{\n  "account_id": "C1231006815"\n}');
    } else if (toolName === 'search_policies') {
      setToolArgs('{\n  "query": "rapid liquidation money mule",\n  "top_k": 2\n}');
    } else if (toolName === 'check_synthetic_watchlist') {
      setToolArgs('{\n  "entity_name": "C1305486145"\n}');
    } else if (toolName === 'calculate_risk') {
      setToolArgs('{\n  "step": 1,\n  "type": "TRANSFER",\n  "amount": 100000,\n  "name_orig": "C10001",\n  "old_balance_org": 100000,\n  "new_balance_orig": 0,\n  "name_dest": "C20002",\n  "old_balance_dest": 0,\n  "new_balance_dest": 0\n}');
    }
  };

  const handleExecuteMCP = async () => {
    try {
      setExecutingTool(true);
      setToolResult(null);
      const parsedArgs = JSON.parse(toolArgs);
      const res = await api.callMCPTool(selectedTool, parsedArgs);
      setToolResult(res);
    } catch (err: any) {
      setToolResult({ error: err.message || 'JSON parse or execution error' });
    } finally {
      setExecutingTool(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const q = userSearch.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.full_name && u.full_name.toLowerCase().includes(q)) ||
      u.role.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-3 sm:p-4 md:p-6 space-y-4 sm:space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Administration"
        subtitle="User access management, connected system actions, and platform configuration"
        icon={<Settings className="h-6 w-6 text-sky-400" />}
        breadcrumbs={['FinGuard', 'System', 'Administration']}
      />

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-4 text-xs font-medium overflow-x-auto scrollbar-thin">
        <button
          onClick={() => setActiveTab('users')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition cursor-pointer ${
            activeTab === 'users'
              ? 'border-sky-500 text-sky-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="h-4 w-4" />
          User Management ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('mcp')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition cursor-pointer ${
            activeTab === 'mcp'
              ? 'border-sky-500 text-sky-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code className="h-4 w-4" />
          Connected System Actions (MCP)
        </button>
        <button
          onClick={() => setActiveTab('infrastructure')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition cursor-pointer ${
            activeTab === 'infrastructure'
              ? 'border-sky-500 text-sky-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Server className="h-4 w-4" />
          Integration & Storage Status
        </button>
      </div>

      {actionFeedback && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
            actionFeedback.isError
              ? 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionFeedback.isError ? (
              <AlertTriangle className="h-4 w-4 text-rose-400" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="text-slate-400 hover:text-slate-200 text-[11px] underline ml-4 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tab 1: User Management */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#11192e] border border-slate-800/80 p-4 rounded-xl">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Users className="h-4 w-4 text-sky-400" />
                Active Platform User Accounts
              </h3>
              <p className="text-xs text-slate-400">
                Manage roles, account statuses, and trigger administrative password resets
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Filter users..."
                  className="bg-slate-900 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-44"
                />
              </div>

              <button
                onClick={loadUsers}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-400 hover:text-slate-200 transition cursor-pointer"
                title="Refresh user list"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {loadingUsers ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <div className="rounded-xl border border-slate-800/80 bg-[#11192e] overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#0b1220] border-b border-slate-800/80 text-slate-400 uppercase font-mono text-[10px]">
                    <tr>
                      <th className="px-4 py-3">Account / User</th>
                      <th className="px-4 py-3">Email Address</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Created</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {filteredUsers.map((u) => {
                      const isSelf = currentUser?.id === u.id;
                      const roleNorm = u.role.toUpperCase();
                      const isAdminRole = roleNorm === 'ADMIN' || roleNorm === 'ADMINISTRATOR';

                      return (
                        <tr key={u.id} className="hover:bg-slate-800/30 transition">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2.5">
                              <div
                                className={`h-7 w-7 rounded-full flex items-center justify-center font-bold text-[11px] uppercase border ${
                                  isAdminRole
                                    ? 'bg-purple-950/80 border-purple-800 text-purple-300'
                                    : 'bg-sky-950/80 border-sky-800 text-sky-300'
                                }`}
                              >
                                {u.username.slice(0, 2)}
                              </div>
                              <div>
                                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                                  {u.full_name || u.username}
                                  {isSelf && (
                                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-950 text-sky-400 border border-sky-800">
                                      You
                                    </span>
                                  )}
                                </div>
                                <div className="text-[10px] text-slate-400 font-mono">@{u.username}</div>
                              </div>
                            </div>
                          </td>

                          <td className="px-4 py-3 font-mono text-slate-300">{u.email}</td>

                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                                isAdminRole
                                  ? 'bg-purple-950/80 text-purple-300 border border-purple-800'
                                  : 'bg-sky-950/80 text-sky-300 border border-sky-800'
                              }`}
                            >
                              {isAdminRole ? 'ADMIN' : 'USER'}
                            </span>
                          </td>

                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${
                                u.is_active
                                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                                  : 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                              }`}
                            >
                              <span
                                className={`h-1.5 w-1.5 rounded-full ${
                                  u.is_active ? 'bg-emerald-400' : 'bg-rose-400'
                                }`}
                              />
                              {u.is_active ? 'Active' : 'Disabled'}
                            </span>
                          </td>

                          <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                            {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'Initial Setup'}
                          </td>

                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {/* Toggle Status Button */}
                              <button
                                onClick={() => handleToggleStatusClick(u)}
                                disabled={isSelf && u.is_active}
                                className={`px-2.5 py-1 rounded text-[11px] font-medium transition cursor-pointer border ${
                                  u.is_active
                                    ? 'bg-slate-900 hover:bg-rose-950/50 text-slate-300 hover:text-rose-300 border-slate-700/80 hover:border-rose-800/60'
                                    : 'bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border-emerald-800/60'
                                } disabled:opacity-40 disabled:cursor-not-allowed`}
                                title={
                                  isSelf && u.is_active
                                    ? 'Cannot disable your own active account'
                                    : u.is_active
                                    ? 'Disable Account'
                                    : 'Enable Account'
                                }
                              >
                                {u.is_active ? 'Disable' : 'Enable'}
                              </button>

                              {/* Reset Password Button */}
                              <button
                                onClick={() => handleOpenResetModal(u)}
                                className="px-2.5 py-1 rounded text-[11px] font-medium bg-slate-900 hover:bg-slate-800 text-sky-400 hover:text-sky-300 border border-slate-700/80 transition cursor-pointer flex items-center gap-1"
                                title="Reset User Password"
                              >
                                <KeyRound className="h-3 w-3" />
                                Reset
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Connected System Actions (MCP Tools) */}
      {activeTab === 'mcp' && (
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4">
          <div className="border-b border-slate-800 pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Code className="h-4 w-4 text-sky-400" />
                Model Context Protocol (MCP) Standardized Tools
              </h3>
              <p className="text-xs text-slate-400">
                Connected financial risk tools with explicit schemas and audit recording
              </p>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-sky-950 text-sky-300 border border-sky-800">
              {mcpData?.server || 'MCP Server v1.0'}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
            {/* Tool Selector List */}
            <div className="lg:col-span-4 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase font-mono">Available Actions</div>
              <div className="space-y-1.5 max-h-[320px] overflow-y-auto">
                {mcpData?.tools.map((t) => (
                  <button
                    key={t.name}
                    onClick={() => handleToolSelect(t.name)}
                    className={`w-full text-left p-2.5 rounded-lg text-xs transition cursor-pointer ${
                      selectedTool === t.name
                        ? 'bg-sky-600/20 text-sky-300 border border-sky-500/50 font-medium'
                        : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className="font-mono text-xs font-bold text-white">{t.name}</div>
                    <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{t.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Argument Input & Output */}
            <div className="lg:col-span-8 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between font-sans">
                <span className="text-slate-300 font-medium">Input Arguments (JSON):</span>
                <button
                  onClick={handleExecuteMCP}
                  disabled={executingTool}
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                >
                  <Play className="h-3.5 w-3.5" />
                  {executingTool ? 'Executing...' : 'Invoke Tool via MCP'}
                </button>
              </div>

              <textarea
                rows={6}
                value={toolArgs}
                onChange={(e) => setToolArgs(e.target.value)}
                className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-3 text-sky-300 focus:outline-none focus:border-sky-500 text-xs font-mono"
              />

              {toolResult && (
                <div className="space-y-1 pt-2">
                  <span className="text-emerald-400 text-[11px] font-sans font-medium">
                    Validated Response:
                  </span>
                  <pre className="p-3 rounded-lg bg-[#0a0f1d] border border-slate-800 text-slate-200 overflow-x-auto text-[11px] max-h-[220px]">
                    {JSON.stringify(toolResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Infrastructure Status */}
      {activeTab === 'infrastructure' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-[#11192e] border border-slate-800/80 space-y-2">
            <div className="flex justify-between items-center text-slate-400 font-sans">
              <span>Primary Transaction Ledger</span>
              <Database className="h-4 w-4 text-sky-400" />
            </div>
            <div className="text-sm font-bold text-white">SQLite (finguard.db)</div>
            <div className="text-[11px] text-slate-400 font-sans">
              12,000 verified PaySim transactions loaded • WAL mode enabled
            </div>
            <div className="pt-2 text-[10px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Operational & Seeded
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#11192e] border border-slate-800/80 space-y-2">
            <div className="flex justify-between items-center text-slate-400 font-sans">
              <span>Document Search Index</span>
              <Server className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-white">ChromaDB Vector Store</div>
            <div className="text-[11px] text-slate-400 font-sans">
              Indexed compliance manuals & regulatory policies • Persistent
            </div>
            <div className="pt-2 text-[10px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Operational
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#11192e] border border-slate-800/80 space-y-2">
            <div className="flex justify-between items-center text-slate-400 font-sans">
              <span>Fraud Detection Model</span>
              <Cpu className="h-4 w-4 text-purple-400" />
            </div>
            <div className="text-sm font-bold text-white">RandomForestClassifier</div>
            <div className="text-[11px] text-slate-400 font-sans">
              finguard_rf_model.joblib • Calibrated risk threshold: 0.65
            </div>
            <div className="pt-2 text-[10px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Active in inference pipeline
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog for Status Change */}
      <ConfirmActionDialog
        isOpen={statusConfirmOpen}
        title={
          selectedUserForStatus?.is_active
            ? `Disable Account "${selectedUserForStatus?.username}"?`
            : `Enable Account "${selectedUserForStatus?.username}"?`
        }
        message={
          selectedUserForStatus?.is_active
            ? `Disabling this account will prevent the user from logging in immediately. Existing sessions will be terminated.`
            : `Enabling this account will allow the user to authenticate and access their assigned role permissions.`
        }
        confirmLabel={selectedUserForStatus?.is_active ? 'Disable Account' : 'Enable Account'}
        isDestructive={selectedUserForStatus?.is_active}
        loading={statusLoading}
        onConfirm={handleConfirmStatusToggle}
        onCancel={() => setStatusConfirmOpen(false)}
      />

      {/* Password Reset Modal */}
      {resetModalOpen && selectedUserForReset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl bg-[#11192d] border border-slate-700/80 shadow-2xl p-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sky-950/60 text-sky-400 border border-sky-800/60">
                <KeyRound className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">
                  Reset Password for @{selectedUserForReset.username}
                </h3>
                <p className="text-xs text-slate-400">
                  Account: {selectedUserForReset.email}
                </p>
              </div>
            </div>

            <form onSubmit={handleExecutePasswordReset} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">New Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter secure replacement password"
                  className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-sky-500 font-mono"
                />
                <span className="text-[10px] text-slate-500">
                  Will be securely hashed with PBKDF2-HMAC-SHA256 and salted.
                </span>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setResetModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-white bg-sky-600 hover:bg-sky-500 transition cursor-pointer disabled:opacity-50"
                >
                  {resetLoading ? 'Updating...' : 'Set New Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
