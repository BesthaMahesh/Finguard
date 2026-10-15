import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmActionDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const ConfirmActionDialog: React.FC<ConfirmActionDialogProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm Action',
  cancelLabel = 'Cancel',
  isDestructive = false,
  onConfirm,
  onCancel,
  loading = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-xl bg-[#11192d] border border-slate-700/80 shadow-2xl p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`p-2 rounded-lg ${
                isDestructive
                  ? 'bg-rose-950/60 text-rose-400 border border-rose-800/60'
                  : 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
              }`}
            >
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">{title}</h3>
              <p className="text-xs text-slate-400 mt-0.5">Please confirm your decision</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-200 transition p-1"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800">
          {message}
        </p>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800/80">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition cursor-pointer"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium text-white transition cursor-pointer ${
              isDestructive
                ? 'bg-rose-600 hover:bg-rose-500 shadow-rose-950/50'
                : 'bg-sky-600 hover:bg-sky-500'
            } disabled:opacity-50`}
          >
            {loading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
