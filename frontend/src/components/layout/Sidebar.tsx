import React, { useState } from 'react';
import {
  ShieldAlert,
  LayoutDashboard,
  Search,
  Briefcase,
  Bot,
  Cpu,
  FileCheck,
  Activity,
  Settings,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Lock,
} from 'lucide-react';
import { UserRole } from '../../types';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  userRole: UserRole;
  openCasesCount?: number;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: any;
  badge?: number;
  adminOnly?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  userRole,
  openCasesCount = 0,
  collapsed = false,
  onToggleCollapse,
}) => {
  const normRole = (userRole || 'USER').toUpperCase();
  const isAdmin = normRole === 'ADMIN' || normRole === 'ADMINISTRATOR';

  // Role-Specific Navigation Structures
  const adminSections: Array<{ group: string; items: NavItem[] }> = [
    {
      group: 'Overview',
      items: [
        { id: 'overview', label: 'Executive Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      group: 'Financial Operations',
      items: [
        { id: 'transactions', label: 'Transactions', icon: Search },
        { id: 'investigations', label: 'Investigations', icon: Briefcase, badge: openCasesCount },
        { id: 'models', label: 'Detection Performance', icon: Cpu },
      ],
    },
    {
      group: 'Intelligence',
      items: [
        { id: 'assistant', label: 'Risk Assistant', icon: Bot },
        { id: 'knowledge', label: 'Policies & Documents', icon: BookOpen },
      ],
    },
    {
      group: 'Security & Governance',
      items: [
        { id: 'governance', label: 'Security & Audit', icon: FileCheck },
      ],
    },
    {
      group: 'Platform Operations',
      items: [
        { id: 'observability', label: 'System Health', icon: Activity },
      ],
    },
    {
      group: 'Administration',
      items: [
        { id: 'admin', label: 'System Administration', icon: Settings },
      ],
    },
  ];

  const standardUserSections: Array<{ group: string; items: NavItem[] }> = [
    {
      group: 'Operations',
      items: [
        { id: 'overview', label: 'Risk Dashboard', icon: LayoutDashboard },
        { id: 'transactions', label: 'Transactions', icon: Search },
        { id: 'investigations', label: 'Case Investigations', icon: Briefcase, badge: openCasesCount },
      ],
    },
    {
      group: 'Assistance & Policies',
      items: [
        { id: 'assistant', label: 'FinGuard Assistant', icon: Bot },
        { id: 'knowledge', label: 'Policies & Regulations', icon: BookOpen },
      ],
    },
  ];

  const navSections = isAdmin ? adminSections : standardUserSections;

  return (
    <aside
      className={`${
        collapsed ? 'w-16' : 'w-64'
      } bg-[#090e1a] border-r border-slate-800/80 flex flex-col shrink-0 h-screen sticky top-0 transition-all duration-200 select-none z-40`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="h-9 w-9 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
            <ShieldAlert className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="font-bold text-slate-100 tracking-tight text-sm flex items-center gap-1.5">
                FinGuard
                <span className="text-[9px] uppercase font-mono px-1.5 py-0.2 bg-sky-950 text-sky-400 border border-sky-800 rounded font-semibold">
                  v1.2
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium truncate">
                Risk Intelligence
              </div>
            </div>
          )}
        </div>

        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded-md text-slate-500 hover:text-slate-300 hover:bg-slate-800/60 transition cursor-pointer"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        )}
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 p-2 space-y-4 overflow-y-auto">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            {!collapsed && (
              <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                {section.group}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              const isLockedForUser = item.adminOnly && !isAdmin;

              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`w-full flex items-center ${
                    collapsed ? 'justify-center px-2' : 'justify-between px-3'
                  } py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    isActive
                      ? 'bg-sky-600/15 text-sky-300 border border-sky-500/30 shadow-sm shadow-sky-950/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </div>

                  {!collapsed && (
                    <div className="flex items-center gap-1">
                      {isLockedForUser && (
                        <span className="p-0.5 text-slate-600" title="Admin only">
                          <Lock className="h-3 w-3" />
                        </span>
                      )}
                      {item.badge !== undefined && item.badge > 0 && (
                        <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-rose-950/80 text-rose-300 border border-rose-800 font-mono">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* System Status Footnote */}
      <div className="p-3 border-t border-slate-800/80 bg-[#070b14]/80">
        {!collapsed ? (
          <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2.5 text-xs">
            <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                {isAdmin ? 'System Administrator' : 'Financial Risk Analyst'}
              </span>
              <span className="font-mono text-emerald-400 text-[10px]">Active</span>
            </div>
            {isAdmin ? (
              <div className="text-[10px] text-slate-400 truncate">
                Dataset: PaySim (12,000 Records)
              </div>
            ) : (
              <div className="text-[10px] text-slate-400 truncate">
                Autonomous Risk Engine Active
              </div>
            )}
          </div>
        ) : (
          <div className="flex justify-center" title="FinGuard Risk Intelligence Platform Active">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
        )}
      </div>
    </aside>
  );
};
