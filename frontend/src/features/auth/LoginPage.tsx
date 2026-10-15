import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Eye,
  EyeOff,
  Lock,
  User,
  AlertCircle,
  ArrowRight,
  Shield,
  Server,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Check
} from 'lucide-react';
import { api, getBackendHost, setCustomBackendUrl } from '../../services/api';
import { UserProfile } from '../../types';

interface LoginPageProps {
  onLoginSuccess: (user: UserProfile, token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingTime, setLoadingTime] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Backend URL configuration
  const [showConfig, setShowConfig] = useState(false);
  const [backendUrl, setBackendUrl] = useState('');
  const [healthStatus, setHealthStatus] = useState<'idle' | 'checking' | 'healthy' | 'error'>('idle');
  const [healthMessage, setHealthMessage] = useState<string | null>(null);

  useEffect(() => {
    setBackendUrl(getBackendHost());
    checkHealth();
  }, []);

  // Timer for loading state to inform user about Render cold start
  useEffect(() => {
    let interval: any;
    if (loading) {
      setLoadingTime(0);
      interval = setInterval(() => {
        setLoadingTime((prev) => prev + 1);
      }, 1000);
    } else {
      setLoadingTime(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const checkHealth = async () => {
    setHealthStatus('checking');
    try {
      const res = await api.getHealth();
      if (res && res.status === 'HEALTHY') {
        setHealthStatus('healthy');
        setHealthMessage('Backend is online and responsive');
      } else {
        setHealthStatus('error');
        setHealthMessage('Received unexpected response from backend');
      }
    } catch (e: any) {
      setHealthStatus('error');
      setHealthMessage(e.message || 'Cannot reach backend server');
    }
  };

  const handleSaveBackendUrl = (e: React.FormEvent) => {
    e.preventDefault();
    setCustomBackendUrl(backendUrl);
    setErrorMessage(null);
    checkHealth();
    setShowConfig(false);
  };

  const fillCredentials = (id: string, pass: string) => {
    setIdentifier(id);
    setPassword(pass);
    setErrorMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    const trimmedIdentifier = identifier.trim();
    if (!trimmedIdentifier || !password) {
      setErrorMessage('Please enter both your account identifier and password.');
      return;
    }

    try {
      setLoading(true);
      setErrorMessage(null);
      const res = await api.login(trimmedIdentifier, password);
      if (res && res.access_token && res.user) {
        onLoginSuccess(res.user, res.access_token);
      } else {
        throw new Error('Authentication response was invalid.');
      }
    } catch (err: any) {
      const msg = err.message || '';
      if (msg.toLowerCase().includes('failed to fetch') || msg.toLowerCase().includes('network')) {
        setErrorMessage(
          'Unable to reach backend. If hosted on Render Free tier, the service may be asleep or waking up. You can check or update the Backend URL below.'
        );
      } else if (msg.includes('401') || msg.toLowerCase().includes('credential') || msg.toLowerCase().includes('password')) {
        setErrorMessage('Invalid credentials. Use user / 12345 or admin / 123456.');
      } else {
        setErrorMessage(msg || 'Authentication failed. Please verify your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen flex flex-col justify-center items-center bg-[#070b14] text-slate-100 p-4 font-sans select-none relative overflow-hidden">
      {/* Subtle Background Ambience */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[32rem] h-[32rem] bg-sky-950/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-80 h-80 bg-teal-950/15 rounded-full blur-3xl pointer-events-none" />

      {/* Main Centered Container */}
      <div className="w-full max-w-md relative z-10 space-y-5">
        {/* Brand & Platform Identity */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-[#0f172a] border border-slate-800 shadow-xl shadow-sky-950/20 mb-1">
            <ShieldCheck className="h-9 w-9 text-sky-400" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">FinGuard</h1>
            <span className="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
              Enterprise
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            Autonomous Financial Risk Intelligence
          </p>
        </div>

        {/* Backend Connection Status Pill */}
        <div className="flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] text-slate-300">
          <div className="flex items-center gap-2 truncate">
            <span
              className={`h-2 w-2 rounded-full shrink-0 ${
                healthStatus === 'healthy'
                  ? 'bg-emerald-400'
                  : healthStatus === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-400'
              }`}
            />
            <span className="text-slate-400 text-[10px]">API Host:</span>
            <span className="font-mono text-slate-200 truncate max-w-[200px]" title={backendUrl || 'Relative (/api/v1)'}>
              {backendUrl || '/api/v1 (relative)'}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowConfig(!showConfig)}
            className="text-[10px] text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1 cursor-pointer ml-2 shrink-0"
          >
            <Sliders className="h-3 w-3" />
            <span>{showConfig ? 'Close' : 'Configure'}</span>
          </button>
        </div>

        {/* Backend Configuration Drawer */}
        {showConfig && (
          <div className="rounded-xl bg-[#0b1324] border border-sky-900/60 p-4 space-y-3 animate-in fade-in text-xs">
            <div className="flex items-center justify-between text-slate-200 font-medium">
              <span className="flex items-center gap-1.5">
                <Server className="h-3.5 w-3.5 text-sky-400" />
                Configure Backend URL
              </span>
              <button
                type="button"
                onClick={checkHealth}
                disabled={healthStatus === 'checking'}
                className="text-[11px] text-sky-400 hover:text-sky-300 flex items-center gap-1"
              >
                <RefreshCw className={`h-3 w-3 ${healthStatus === 'checking' ? 'animate-spin' : ''}`} />
                Test
              </button>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              If your backend is hosted on Render, enter your service URL (e.g.{' '}
              <code className="text-sky-300 bg-sky-950/60 px-1 py-0.5 rounded">https://finguard-backend.onrender.com</code>).
            </p>
            <form onSubmit={handleSaveBackendUrl} className="space-y-2">
              <input
                type="url"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                placeholder="https://finguard-backend.onrender.com"
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-sky-500"
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs flex items-center gap-1.5 cursor-pointer"
                >
                  <Check className="h-3 w-3" />
                  Save URL
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setCustomBackendUrl('');
                    setBackendUrl('');
                    checkHealth();
                  }}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs cursor-pointer"
                >
                  Reset Default
                </button>
              </div>
            </form>
            {healthMessage && (
              <div
                className={`text-[11px] p-2 rounded flex items-start gap-1.5 ${
                  healthStatus === 'healthy'
                    ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/40'
                    : 'bg-rose-950/40 text-rose-300 border border-rose-800/40'
                }`}
              >
                {healthStatus === 'healthy' ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
                )}
                <span>{healthMessage}</span>
              </div>
            )}
          </div>
        )}

        {/* Login Card */}
        <div className="rounded-2xl bg-[#0f172a]/95 border border-slate-800 shadow-2xl p-7 sm:p-8 space-y-5 backdrop-blur-md">
          <div className="border-b border-slate-800/80 pb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">Secure Enterprise Access</h2>
              <p className="text-[11px] text-slate-400 mt-0.5">Authorized risk analysts and investigators</p>
            </div>
            <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/40">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              RBAC Protected
            </div>
          </div>

          {/* Quick Demo Credentials */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Quick Fill:</span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillCredentials('user', '12345')}
                className="p-2 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 text-left transition text-xs cursor-pointer group"
              >
                <div className="text-[11px] font-medium text-slate-200 group-hover:text-sky-300">👤 Risk Analyst</div>
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">user / 12345</div>
              </button>
              <button
                type="button"
                onClick={() => fillCredentials('admin', '123456')}
                className="p-2 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 text-left transition text-xs cursor-pointer group"
              >
                <div className="text-[11px] font-medium text-slate-200 group-hover:text-sky-300">🛡️ Administrator</div>
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">admin / 123456</div>
              </button>
            </div>
          </div>

          {errorMessage && (
            <div
              role="alert"
              className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in"
            >
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
              <div className="leading-tight">{errorMessage}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Account Identifier Field */}
            <div className="space-y-1.5">
              <label
                htmlFor="account-identifier"
                className="text-xs font-medium text-slate-300 flex items-center justify-between"
              >
                <span>Account Identifier</span>
                <span className="text-[10px] text-slate-500 font-mono">Username or Email</span>
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 pointer-events-none" />
                <input
                  id="account-identifier"
                  name="identifier"
                  type="text"
                  autoComplete="username"
                  required
                  value={identifier}
                  onChange={(e) => {
                    setIdentifier(e.target.value);
                    if (errorMessage) setErrorMessage(null);
                  }}
                  placeholder="user or admin"
                  className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition font-sans"
                />
              </div>
            </div>

            {/* Password Field with Visibility Toggle */}
            <div className="space-y-1.5">
              <label
                htmlFor="account-password"
                className="text-xs font-medium text-slate-300 flex items-center justify-between"
              >
                <span>Password</span>
                <span className="text-[10px] text-slate-500 font-mono">Secure Token</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 pointer-events-none" />
                <input
                  id="account-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errorMessage) setErrorMessage(null);
                  }}
                  placeholder="Enter password"
                  className="w-full bg-[#0a0f1d] border border-slate-700/80 rounded-lg pl-9 pr-10 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition cursor-pointer p-0.5"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Security Assurance Notice */}
            <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
              <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <Shield className="h-3.5 w-3.5 text-sky-400" />
                <span>Encrypted Session</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Rate-limited</span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-sky-600/20 disabled:opacity-50 transition cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>
                    {loadingTime > 4 ? `Waking up backend (${loadingTime}s)...` : 'Verifying Credentials...'}
                  </span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>

            {loading && loadingTime > 4 && (
              <p className="text-[10px] text-amber-300/90 text-center leading-normal animate-in fade-in">
                Render free tier services spin down when idle. The first request may take ~45–60s to wake up the server.
              </p>
            )}
          </form>
        </div>

        {/* Security Policy Footnote */}
        <div className="text-center text-[11px] text-slate-500 space-y-1">
          <div>FinGuard Financial Intelligence Platform</div>
          <div className="text-[10px] text-slate-500">
            Protected by salted PBKDF2 cryptography and role-based access control.
          </div>
        </div>
      </div>
    </div>
  );
};
