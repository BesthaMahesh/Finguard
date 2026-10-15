import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck,
  Search,
  LogOut,
  ChevronDown,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Menu,
} from 'lucide-react';
import { UserProfile } from '../../types';
import { api } from '../../services/api';

interface HeaderProps {
  currentTab: string;
  user: UserProfile;
  onLogout: () => void;
  onToggleSidebar?: () => void;
  onGlobalSearch?: (term: string) => void;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  user,
  onLogout,
  onToggleSidebar,
  onGlobalSearch,
  onRefresh,
}) => {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    telemetry: string;
    layers: number;
  } | null>(null);

  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown when switching navigation tabs
  useEffect(() => {
    setShowProfileMenu(false);
  }, [currentTab]);

  // Close profile dropdown on outside click or Escape key
  useEffect(() => {
    if (!showProfileMenu) return;

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      if (
        profileMenuRef.current &&
        !profileMenuRef.current.contains(event.target as Node)
      ) {
        setShowProfileMenu(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('touchstart', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('touchstart', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showProfileMenu]);

  useEffect(() => {
    // Check actual health from backend
    api.getHealth()
      .then((res) => {
        setHealthStatus({
          status: res.status,
          telemetry: res.telemetry,
          layers: res.architecture_layers,
        });
      })
      .catch(() => {
        setHealthStatus(null);
      });
  }, []);

  // Professional Business-Friendly Terminology Map (Section 5)
  const titles: Record<string, { title: string; subtitle: string; category: string }> = {
    overview: {
      category: 'Operations',
      title: 'Risk Dashboard',
      subtitle: 'Portfolio fraud metrics, risk distribution, and high-priority anomalies',
    },
    transactions: {
      category: 'Operations',
      title: 'Transactions',
      subtitle: 'Financial ledger audit, entity search, and calibrated risk assessments',
    },
    investigations: {
      category: 'Operations',
      title: 'Investigations',
      subtitle: 'Case workbench, evidence timelines, policy excerpts, and analyst review',
    },
    assistant: {
      category: 'Intelligence',
      title: 'Risk Assistant',
      subtitle: 'Natural language investigation copilot grounded in AML/KYC policies',
    },
    knowledge: {
      category: 'Intelligence',
      title: 'Policies & Documents',
      subtitle: 'Indexed regulatory manuals, document search index, and compliance repository',
    },
    models: {
      category: 'Governance',
      title: 'Detection Performance',
      subtitle: 'Fraud detection quality (precision-recall), confusion matrix, and feature impact',
    },
    governance: {
      category: 'Governance',
      title: 'Security & Audit',
      subtitle: 'Structured audit events, actor tracking, and compliance verification',
    },
    observability: {
      category: 'System',
      title: 'System Health',
      subtitle: 'Request and workflow diagnostics, latency telemetry, and service status',
    },
    admin: {
      category: 'System',
      title: 'Administration',
      subtitle: 'User management, connected system actions, and platform configuration',
    },
  };

  const currentMeta = titles[currentTab] || {
    category: 'Platform',
    title: 'Risk Dashboard',
    subtitle: 'Autonomous Financial Risk Intelligence Platform',
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onGlobalSearch && searchTerm.trim()) {
      onGlobalSearch(searchTerm.trim());
    }
  };

  const roleNormalized = (user.role || 'USER').toUpperCase();
  const isAdmin = roleNormalized === 'ADMIN' || roleNormalized === 'ADMINISTRATOR';

  return (
    <header className="h-16 bg-[#0c1324] border-b border-slate-800/80 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 select-none">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 md:hidden transition cursor-pointer"
            title="Toggle Menu"
          >
            <Menu className="h-4 w-4" />
          </button>
        )}

        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider hidden sm:inline">
              {currentMeta.category} /
            </span>
            <h1 className="text-sm md:text-base font-bold text-slate-100 tracking-tight">
              {currentMeta.title}
            </h1>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block truncate max-w-md">
            {currentMeta.subtitle}
          </p>
        </div>
      </div>

      {/* Center: Global Transaction Search */}
      <div className="hidden lg:flex items-center flex-1 max-w-xs mx-6">
        <form onSubmit={handleSearchSubmit} className="w-full relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search transaction ID or entity..."
            className="w-full bg-[#080d19] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition"
          />
        </form>
      </div>

      {/* Right: Actual Health Indicator & User Profile Menu */}
      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-xs transition cursor-pointer"
            title="Refresh Data"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        )}

        {/* Live Backend Health Badge (Real Backend Status) */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-[11px] font-mono">
          {healthStatus ? (
            <>
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 font-medium">System Online</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400 text-[10px]">Enterprise</span>
            </>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-amber-400">Connecting...</span>
            </>
          )}
        </div>

        {/* User Profile & Menu */}
        <div className="relative" ref={profileMenuRef}>
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1.5 rounded-lg hover:bg-slate-800/60 border border-transparent hover:border-slate-800 transition cursor-pointer"
          >
            <div className={`h-7 w-7 rounded-full flex items-center justify-center font-bold text-xs uppercase border ${
              isAdmin
                ? 'bg-purple-950/80 border-purple-700/60 text-purple-300'
                : 'bg-sky-950/80 border-sky-700/60 text-sky-300'
            }`}>
              {user.username.slice(0, 2)}
            </div>

            <div className="text-left hidden md:block">
              <div className="text-xs font-semibold text-slate-200 leading-none">
                {user.full_name || user.username}
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`text-[9px] font-mono uppercase px-1 rounded font-semibold ${
                  isAdmin
                    ? 'bg-purple-950 text-purple-400 border border-purple-800'
                    : 'bg-sky-950 text-sky-400 border border-sky-800'
                }`}>
                  {isAdmin ? 'ADMIN' : 'USER'}
                </span>
                <span className="text-[10px] text-slate-500 truncate max-w-[120px]">
                  {user.email}
                </span>
              </div>
            </div>

            <ChevronDown className="h-3.5 w-3.5 text-slate-500 hidden md:block" />
          </button>

          {/* Profile Dropdown Menu */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl bg-[#0f172a] border border-slate-700/80 shadow-2xl p-2 z-50 animate-in fade-in duration-100">
              <div className="p-3 border-b border-slate-800/80 mb-1">
                <div className="text-xs font-bold text-white">{user.full_name || user.username}</div>
                <div className="text-[11px] text-slate-400 font-mono mt-0.5">{user.email}</div>
                <div className="mt-2 inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-sky-400">
                  <span>Role:</span>
                  <strong className="uppercase font-semibold">{isAdmin ? 'Administrator (ADMIN)' : 'Standard User (USER)'}</strong>
                </div>
              </div>

              <div className="p-1 space-y-1">
                <div className="px-2 py-1.5 text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                  Session Controls
                </div>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onLogout();
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium text-rose-300 hover:text-rose-100 hover:bg-rose-950/40 border border-transparent hover:border-rose-900/60 transition cursor-pointer"
                >
                  <LogOut className="h-3.5 w-3.5 text-rose-400" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
