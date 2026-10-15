import React, { useState } from 'react';
import { ShieldCheck, Eye, EyeOff, Lock, User, AlertCircle, ArrowRight, Shield } from 'lucide-react';
import { api } from '../../services/api';
import { UserProfile } from '../../types';

interface LoginPageProps {
  onLoginSuccess: (user: UserProfile, token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
        setErrorMessage('Unable to reach the authentication service. Please verify server connectivity.');
      } else if (msg.includes('401') || msg.toLowerCase().includes('credential') || msg.toLowerCase().includes('password')) {
        setErrorMessage('Invalid credentials. Please verify your account identifier and password.');
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
      <div className="w-full max-w-md relative z-10 space-y-6">
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
                  placeholder="Enter your username or email"
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
                  placeholder="Enter your account password"
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
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
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
