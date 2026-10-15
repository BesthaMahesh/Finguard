import React from 'react';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { UserRole } from '../../types';

interface RoleGuardProps {
  currentRole: UserRole;
  allowedRoles: UserRole[];
  children: React.ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  onNavigateBack?: () => void;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  currentRole,
  allowedRoles,
  children,
  fallbackTitle = 'Access Restricted',
  fallbackMessage = 'This module requires administrative permissions. Your current role does not have authorization to view or execute actions here.',
  onNavigateBack,
}) => {
  const normCurrent = currentRole.toUpperCase();
  const isAllowed = allowedRoles.some((r) => {
    const norm = r.toUpperCase();
    if (normCurrent === norm) return true;
    if (normCurrent === 'ADMIN' && (norm === 'ADMINISTRATOR' || norm === 'ADMIN')) return true;
    if (normCurrent === 'ADMINISTRATOR' && (norm === 'ADMIN' || norm === 'ADMINISTRATOR')) return true;
    if (normCurrent === 'USER' && (norm === 'ANALYST' || norm === 'INVESTIGATOR' || norm === 'AUDITOR' || norm === 'USER')) return true;
    return false;
  });

  if (isAllowed) {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] p-8 text-center">
      <div className="rounded-2xl border border-slate-800 bg-[#11192e] p-8 max-w-md shadow-2xl space-y-4">
        <div className="h-12 w-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mx-auto">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h3 className="text-base font-bold text-slate-100">{fallbackTitle}</h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          {fallbackMessage}
        </p>
        <div className="pt-2 text-xs font-mono text-slate-500">
          Current Role: <span className="text-sky-400 uppercase font-semibold">{currentRole}</span>
        </div>
        {onNavigateBack && (
          <div className="pt-2">
            <button
              onClick={onNavigateBack}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Return to Risk Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
