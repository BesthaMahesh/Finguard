import React from 'react';

interface LoadingSkeletonProps {
  lines?: number;
  className?: string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  lines = 4,
  className = '',
}) => {
  return (
    <div className={`space-y-3 p-4 rounded-xl bg-slate-900/30 border border-slate-800/80 animate-pulse ${className}`}>
      <div className="h-4 bg-slate-800 rounded w-1/3"></div>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 bg-slate-800/60 rounded"
          style={{ width: `${85 - (i % 3) * 15}%` }}
        ></div>
      ))}
    </div>
  );
};
