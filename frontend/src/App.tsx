import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { LoginPage } from './features/auth/LoginPage';
import { ExecutiveDashboard } from './features/dashboard/ExecutiveDashboard';
import { TransactionIntelligence } from './features/transactions/TransactionIntelligence';
import { InvestigationWorkbench } from './features/investigations/InvestigationWorkbench';
import { AIRiskAssistant, clearAssistantSessionCache } from './features/assistant/AIRiskAssistant';
import { ModelIntelligence } from './features/models/ModelIntelligence';
import { GovernanceAudit } from './features/governance/GovernanceAudit';
import { ObservabilityCenter } from './features/observability/ObservabilityCenter';
import { SystemAdmin } from './features/admin/SystemAdmin';
import { KnowledgeBase } from './features/knowledge/KnowledgeBase';
import { RoleGuard } from './components/common/RoleGuard';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { UserProfile, UserRole } from './types';
import { api, setAuthToken } from './services/api';
import { LayoutDashboard, Search, Briefcase, Bot, Menu } from 'lucide-react';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authChecking, setAuthChecking] = useState<boolean>(true);

  // Navigation & Shell States
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [workbenchTxId, setWorkbenchTxId] = useState<number | null>(null);

  // Check existing session token on application mount
  useEffect(() => {
    checkActiveSession();
  }, []);

  const checkActiveSession = async () => {
    const existingToken = localStorage.getItem('finguard_token');
    if (!existingToken) {
      setAuthChecking(false);
      setIsAuthenticated(false);
      return;
    }

    try {
      setAuthToken(existingToken);
      const activeUser = await api.getCurrentUser();
      if (activeUser && activeUser.username) {
        setUser(activeUser);
        setIsAuthenticated(true);
      } else {
        setAuthToken(null);
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (e) {
      console.warn('Existing session invalid or expired:', e);
      setAuthToken(null);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setAuthChecking(false);
    }
  };

  const handleLoginSuccess = (loggedInUser: UserProfile, token: string) => {
    setAuthToken(token);
    setUser(loggedInUser);
    setIsAuthenticated(true);
    setCurrentTab('overview');
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn('Logout API error:', e);
    } finally {
      clearAssistantSessionCache();
      setAuthToken(null);
      setUser(null);
      setIsAuthenticated(false);
      setCurrentTab('overview');
    }
  };

  const handleOpenCaseFromTx = (txId: number) => {
    setWorkbenchTxId(txId);
    setCurrentTab('investigations');
  };

  const handleGlobalSearch = (term: string) => {
    setCurrentTab('transactions');
  };

  // Splash loading during initial token verification
  if (authChecking) {
    return (
      <div className="h-screen w-screen bg-[#070b14] flex flex-col items-center justify-center text-slate-300 font-sans">
        <div className="h-9 w-9 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mb-4" />
        <div className="text-sm font-semibold text-white tracking-tight">FinGuard Enterprise</div>
        <div className="text-xs text-slate-500 font-mono mt-1">Verifying authenticated session...</div>
      </div>
    );
  }

  // Unauthenticated State: Show Polished Enterprise Login Page
  if (!isAuthenticated || !user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const userRole = user.role || 'USER';

  return (
    <div className="flex h-screen w-screen bg-[#0a0f1d] text-slate-100 overflow-hidden font-sans">
      {/* 9-Layer Architecture Left Sidebar (Responsive Drawer on Mobile) */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setWorkbenchTxId(null);
          setCurrentTab(tab);
          setMobileSidebarOpen(false);
        }}
        userRole={userRole}
        openCasesCount={25}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Global Authenticated TopBar */}
        <Header
          currentTab={currentTab}
          user={user}
          onLogout={handleLogout}
          onToggleSidebar={() => setMobileSidebarOpen((prev) => !prev)}
          onGlobalSearch={handleGlobalSearch}
        />

        {/* Dynamic Feature Page Routing with Role-Based Protection */}
        <main className="flex-1 overflow-y-auto bg-[#070b14] pb-16 md:pb-0">
          <ErrorBoundary
            key={currentTab}
            resetKey={currentTab}
            fallbackTitle="View Rendering Safeguard"
            onReset={() => setCurrentTab('overview')}
          >
            {currentTab === 'overview' && (
              <ExecutiveDashboard onNavigateToTab={setCurrentTab} userRole={userRole} />
            )}

            {currentTab === 'transactions' && (
              <TransactionIntelligence onOpenCase={handleOpenCaseFromTx} />
            )}

            {currentTab === 'investigations' && (
              <InvestigationWorkbench userRole={userRole} initialTxId={workbenchTxId} />
            )}

            {currentTab === 'assistant' && (
              <AIRiskAssistant currentUserId={user.id || user.username} />
            )}

            {currentTab === 'knowledge' && <KnowledgeBase />}

            {currentTab === 'models' && <ModelIntelligence />}

            {currentTab === 'governance' && (
              <RoleGuard
                currentRole={userRole}
                allowedRoles={['ADMIN', 'administrator', 'auditor']}
                fallbackTitle="Administrator Access Required"
                fallbackMessage="Security & Audit trails, compliance logs, and permissions matrices are restricted to system administrators."
                onNavigateBack={() => setCurrentTab('overview')}
              >
                <GovernanceAudit />
              </RoleGuard>
            )}

            {currentTab === 'observability' && <ObservabilityCenter />}

            {currentTab === 'admin' && (
              <RoleGuard
                currentRole={userRole}
                allowedRoles={['ADMIN', 'administrator']}
                fallbackTitle="Administrator Access Required"
                fallbackMessage="System Administration and user access controls are restricted to users with the ADMIN role. Your account does not have permission to manage platform settings."
                onNavigateBack={() => setCurrentTab('overview')}
              >
                <SystemAdmin currentUser={user} />
              </RoleGuard>
            )}
          </ErrorBoundary>
        </main>

        {/* Mobile Bottom Navigation Bar (Visible only on screens < md) */}
        <nav className="md:hidden fixed bottom-0 inset-x-0 bg-[#090e1a]/95 backdrop-blur-md border-t border-slate-800/90 z-30 px-1 py-1 flex items-center justify-around shadow-2xl select-none">
          <button
            onClick={() => {
              setWorkbenchTxId(null);
              setCurrentTab('overview');
              setMobileSidebarOpen(false);
            }}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-medium transition cursor-pointer ${
              currentTab === 'overview' ? 'text-sky-400 bg-sky-950/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutDashboard className="h-4 w-4 mb-0.5" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => {
              setWorkbenchTxId(null);
              setCurrentTab('transactions');
              setMobileSidebarOpen(false);
            }}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-medium transition cursor-pointer ${
              currentTab === 'transactions' ? 'text-sky-400 bg-sky-950/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="h-4 w-4 mb-0.5" />
            <span>Ledger</span>
          </button>

          <button
            onClick={() => {
              setWorkbenchTxId(null);
              setCurrentTab('investigations');
              setMobileSidebarOpen(false);
            }}
            className={`relative flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-medium transition cursor-pointer ${
              currentTab === 'investigations' ? 'text-sky-400 bg-sky-950/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Briefcase className="h-4 w-4 mb-0.5" />
            <span>Cases</span>
            <span className="absolute top-0.5 right-1.5 h-3.5 px-1 rounded-full bg-rose-600 text-white text-[9px] font-bold flex items-center justify-center">
              25
            </span>
          </button>

          <button
            onClick={() => {
              setWorkbenchTxId(null);
              setCurrentTab('assistant');
              setMobileSidebarOpen(false);
            }}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-medium transition cursor-pointer ${
              currentTab === 'assistant' ? 'text-sky-400 bg-sky-950/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Bot className="h-4 w-4 mb-0.5" />
            <span>Assistant</span>
          </button>

          <button
            onClick={() => setMobileSidebarOpen((prev) => !prev)}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl text-[10px] font-medium transition cursor-pointer ${
              mobileSidebarOpen ? 'text-sky-400 bg-sky-950/50' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Menu className="h-4 w-4 mb-0.5" />
            <span>Menu</span>
          </button>
        </nav>
      </div>
    </div>
  );
}

export default App;
