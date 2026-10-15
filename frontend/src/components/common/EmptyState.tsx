import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-10 text-center rounded-xl bg-slate-900/40 border border-slate-800/80 my-4">
      <div className="h-12 w-12 rounded-full bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-3">
        {icon || <Inbox className="h-6 w-6" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition cursor-pointer"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
