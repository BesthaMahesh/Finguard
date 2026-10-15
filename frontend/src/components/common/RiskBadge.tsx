import React from 'react';

interface RiskBadgeProps {
  level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  size?: 'sm' | 'md';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level = 'LOW', size = 'sm' }) => {
  const norm = level.toUpperCase();
  let styles = 'bg-slate-800 text-slate-300 border-slate-700';

  if (norm === 'CRITICAL') {
    styles = 'bg-rose-950/70 text-rose-300 border-rose-700/60 font-semibold';
  } else if (norm === 'HIGH') {
    styles = 'bg-amber-950/70 text-amber-300 border-amber-700/60 font-medium';
  } else if (norm === 'MEDIUM') {
    styles = 'bg-sky-950/70 text-sky-300 border-sky-700/60';
  } else if (norm === 'LOW') {
    styles = 'bg-emerald-950/60 text-emerald-300 border-emerald-700/50';
  }

  const sizeStyles = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border ${sizeStyles} ${styles}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        norm === 'CRITICAL' ? 'bg-rose-400 animate-pulse' :
        norm === 'HIGH' ? 'bg-amber-400' :
        norm === 'MEDIUM' ? 'bg-sky-400' : 'bg-emerald-400'
      }`} />
      {norm}
    </span>
  );
};

export const RiskMeter: React.FC<{ score: number; threshold?: number }> = ({ score, threshold = 65 }) => {
  const getColor = (s: number) => {
    if (s >= 85) return 'bg-rose-500';
    if (s >= 65) return 'bg-amber-500';
    if (s >= 40) return 'bg-sky-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-center text-xs mb-1">
        <span className="text-slate-400 font-mono">Score: <strong className="text-white">{score.toFixed(1)}</strong>/100</span>
        <span className="text-slate-500 text-[10px]">Threshold: {threshold}</span>
      </div>
      <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden relative border border-slate-700/50">
        <div
          className={`h-full ${getColor(score)} transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
        {/* Threshold marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-rose-400 z-10"
          style={{ left: `${threshold}%` }}
          title={`Review Threshold: ${threshold}`}
        />
      </div>
    </div>
  );
};
