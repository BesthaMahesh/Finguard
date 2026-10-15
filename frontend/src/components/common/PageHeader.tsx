import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  icon?: React.ReactNode;
  badge?: string;
  breadcrumbs?: string[];
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  icon,
  badge,
  breadcrumbs = ['FinGuard', title],
  actions,
}) => {
  return (
    <div className="mb-6 space-y-2">
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono tracking-tight">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span className="text-slate-600">/</span>}
              <span className={idx === breadcrumbs.length - 1 ? 'text-sky-400 font-medium' : 'text-slate-400'}>
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </div>
      )}

      {/* Title & Actions Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            {icon && <div className="text-sky-400 shrink-0">{icon}</div>}
            <h1 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
              {title}
              {badge && (
                <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-sky-950/80 text-sky-300 border border-sky-800">
                  {badge}
                </span>
              )}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {subtitle}
          </p>
        </div>

        {actions && (
          <div className="flex items-center gap-2.5 shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};
