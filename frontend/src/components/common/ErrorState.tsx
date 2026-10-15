import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Data Retrieval Error',
  message,
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center rounded-xl bg-rose-950/20 border border-rose-900/40 my-4">
      <div className="h-10 w-10 rounded-full bg-rose-900/30 border border-rose-800/50 flex items-center justify-center text-rose-400 mb-3">
        <AlertCircle className="h-5 w-5" />
      </div>
      <h3 className="text-sm font-semibold text-rose-200 mb-1">{title}</h3>
      <p className="text-xs text-rose-300/80 max-w-md mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-900/50 hover:bg-rose-900 text-rose-200 text-xs font-medium border border-rose-700/60 transition cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
};
