import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  resetKey?: any;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('FinGuard UI Error Boundary caught an unhandled exception:', error, errorInfo);
  }

  public componentDidUpdate(prevProps: Props) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] w-full flex items-center justify-center p-6 bg-[#070b14] text-slate-100">
          <div className="max-w-lg w-full rounded-2xl bg-[#0f172a] border border-rose-900/40 p-6 space-y-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800/60 text-rose-400 shrink-0">
                <AlertCircle className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-white font-sans">
                  {this.props.fallbackTitle || 'Component Rendering Safeguard'}
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  FinGuard caught an unexpected rendering error. The interface has prevented a complete screen failure to preserve your active workspace.
                </p>
                {this.state.error && (
                  <div className="mt-2 p-2.5 rounded bg-[#0a0f1d] border border-slate-800 text-[11px] font-mono text-rose-300 truncate">
                    {this.state.error.message || 'Unknown runtime error'}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
              {this.props.onReset && (
                <button
                  onClick={this.handleReset}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition cursor-pointer"
                >
                  <Home className="h-3.5 w-3.5" />
                  Return to Dashboard
                </button>
              )}
              <button
                onClick={this.handleReset}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition cursor-pointer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Reload Component
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
