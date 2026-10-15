import React from 'react';
import { HelpCircle } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  explanation?: string;
  icon?: React.ReactNode;
  trend?: {
    text: string;
    positive?: boolean;
    neutral?: boolean;
  };
  variant?: 'default' | 'danger' | 'warning' | 'success' | 'info';
  loading?: boolean;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  explanation,
  icon,
  trend,
  variant = 'default',
  loading = false,
  onClick,
}) => {
  const borderVariants = {
    default: 'border-slate-800/80 bg-[#121a2f]',
    danger: 'border-rose-900/40 bg-[#1e131d]',
    warning: 'border-amber-900/40 bg-[#1d1a15]',
    success: 'border-emerald-900/40 bg-[#111e1c]',
    info: 'border-sky-900/40 bg-[#101b2e]',
  };

  const textVariants = {
    default: 'text-slate-100',
    danger: 'text-rose-400',
    warning: 'text-amber-400',
    success: 'text-emerald-400',
    info: 'text-sky-400',
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-800/80 bg-[#121a2f] p-4 shadow-sm animate-pulse space-y-3">
        <div className="h-3.5 bg-slate-800 rounded w-1/2"></div>
        <div className="h-7 bg-slate-800 rounded w-3/4"></div>
        <div className="h-3 bg-slate-800/60 rounded w-full"></div>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border ${borderVariants[variant]} p-4 shadow-sm transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:border-slate-700 hover:shadow-md' : ''
      }`}
    >
      <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
        <span className="font-medium tracking-wide flex items-center gap-1.5">
          {label}
          {explanation && (
            <span className="relative group cursor-help">
              <HelpCircle className="h-3.5 w-3.5 text-slate-500 hover:text-slate-300 transition-colors" />
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block w-48 p-2 bg-slate-900 border border-slate-700 rounded text-[11px] text-slate-300 shadow-xl z-30 font-normal leading-tight">
                {explanation}
              </span>
            </span>
          )}
        </span>
        {icon && <div className="text-slate-400 opacity-80">{icon}</div>}
      </div>

      <div className={`text-2xl font-bold font-mono tracking-tight ${textVariants[variant]}`}>
        {value}
      </div>

      {(explanation || trend) && (
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/40">
          {trend ? (
            <span
              className={`font-medium ${
                trend.neutral
                  ? 'text-slate-400'
                  : trend.positive
                  ? 'text-emerald-400'
                  : 'text-rose-400'
              }`}
            >
              {trend.text}
            </span>
          ) : (
            <span className="text-slate-400 truncate">{explanation}</span>
          )}
        </div>
      )}
    </div>
  );
};
