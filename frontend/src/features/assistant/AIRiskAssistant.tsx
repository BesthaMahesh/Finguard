import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  BookOpen,
  ShieldCheck,
  AlertCircle,
  User,
  Copy,
  Check,
  RotateCcw,
  RefreshCw,
  Plus,
  MessageSquare,
  Clock,
  Trash2,
  ChevronDown,
  Layers,
} from 'lucide-react';
import { api } from '../../services/api';
import { PolicyCitation } from '../../types';
import { PageHeader } from '../../components/common/PageHeader';
import { MarkdownView } from '../../components/common/MarkdownView';
import { SourceCitationView } from '../../components/common/SourceCitation';
import { ErrorBoundary } from '../../components/common/ErrorBoundary';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: PolicyCitation[];
  latency_ms?: number;
  timestamp: string;
}

interface ConversationSummary {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
}

const DEFAULT_WELCOME: Message = {
  id: 'welcome',
  sender: 'assistant',
  text: '### FinGuard AI Risk Assistant Operational\n\nI am your enterprise financial crime intelligence copilot, grounded in your indexed compliance policies, AML manuals, and risk procedures. Ask any question regarding transaction typologies, threshold rules, or investigative protocols.',
  citations: [
    {
      document_id: 'GOV-AI-2024-09',
      document_title: 'FinGuard Model Governance Policy',
      section: 'Section 1 - Principle of Decision Support',
      excerpt: 'FinGuard is an AI-powered Decision Support System. Under no circumstances may an automated ML score execute an autonomous, unreviewed filing of a criminal SAR.',
      relevance_score: 0.98,
    },
  ],
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

const SUGGESTED_QUERIES = [
  'What are the red flags for account takeover under the indexed fraud policies?',
  'What criteria require human investigator review?',
  'What is the four-eyes principle, and when does it apply?',
  'How does the platform distinguish a model-generated fraud score from verified fraud?',
  'What should the system do when a question is not supported by indexed policies?',
];

export interface AIRiskAssistantProps {
  currentUserId?: string;
}

// In-memory user-scoped session cache to survive tab navigation while isolating across users
const _USER_SESSION_CACHE = new Map<string, { activeConvId: string | null; messages: Message[] }>();

export function clearAssistantSessionCache() {
  _USER_SESSION_CACHE.clear();
}

export const AIRiskAssistant: React.FC<AIRiskAssistantProps> = ({ currentUserId }) => {
  const userKey = currentUserId || 'current_user';
  const initialCache = _USER_SESSION_CACHE.get(userKey) || {
    activeConvId: null,
    messages: [DEFAULT_WELCOME],
  };

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(initialCache.activeConvId);
  const [messages, setMessages] = useState<Message[]>(initialCache.messages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Sync cache and reload list whenever currentUserId changes
  useEffect(() => {
    const cached = _USER_SESSION_CACHE.get(userKey) || {
      activeConvId: null,
      messages: [DEFAULT_WELCOME],
    };
    setActiveConvId(cached.activeConvId);
    setMessages(cached.messages);
    loadConversationList();
  }, [userKey]);

  useEffect(() => {
    _USER_SESSION_CACHE.set(userKey, { activeConvId, messages });
    scrollToBottom();
  }, [messages, activeConvId, userKey]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversationList = async () => {
    try {
      const res = await api.getAssistantConversations();
      if (res && res.conversations) {
        setConversations(res.conversations);
      }
    } catch (err) {
      console.warn('Failed to load conversation history:', err);
    }
  };

  const handleSelectConversation = async (convId: string) => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const detail = await api.getAssistantConversationDetail(convId);
      setActiveConvId(convId);
      if (detail.messages && detail.messages.length > 0) {
        const formatted: Message[] = detail.messages.map((m: any) => ({
          id: m.id,
          sender: m.sender,
          text: m.text,
          citations: m.citations,
          latency_ms: m.latency_ms,
          timestamp: m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        }));
        setMessages(formatted);
      } else {
        setMessages([DEFAULT_WELCOME]);
      }
      setShowHistory(false);
    } catch (err: any) {
      setErrorMessage(`Failed to load conversation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'assistant',
        text: '### New Inquiry Thread\n\nHow can I assist you with financial risk compliance, threshold rules, or suspicious activity investigation?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setShowHistory(false);
    setErrorMessage(null);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    try {
      await api.deleteAssistantConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        handleNewConversation();
      }
    } catch (err: any) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || input).trim();
    if (!textToSend || loading) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.chatAssistant(textToSend, activeConvId || undefined);
      if (res.conversation_id && res.conversation_id !== activeConvId) {
        setActiveConvId(res.conversation_id);
        loadConversationList();
      }

      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: res.reply,
        citations: res.citations,
        latency_ms: res.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      // Preserve prior messages, append error notice
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ **Inquiry Request Failed**: ${err.message || 'Unable to connect with assistant service. Please retry.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setErrorMessage(err.message || 'Error occurred while querying Risk Assistant.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <ErrorBoundary fallbackTitle="Risk Assistant Safeguard">
      <div className="p-4 md:p-6 space-y-5 max-w-5xl mx-auto flex flex-col h-[calc(100vh-5rem)]">
        <PageHeader
          title="Risk Assistant"
          subtitle="Natural language investigation copilot grounded in AML/KYC policies and regulatory manuals"
          breadcrumbs={['FinGuard', 'Intelligence', 'Risk Assistant']}
          actions={
            <div className="flex items-center gap-2">
              <div className="relative">
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition cursor-pointer"
                >
                  <Clock className="h-3.5 w-3.5 text-sky-400" />
                  <span>Conversations ({conversations.length})</span>
                  <ChevronDown className="h-3 w-3 text-slate-400" />
                </button>

                {showHistory && (
                  <div className="absolute right-0 mt-1.5 w-72 rounded-xl bg-[#11192e] border border-slate-800 shadow-2xl p-2 z-50 space-y-1 animate-in fade-in max-h-80 overflow-y-auto">
                    <div className="px-2 py-1.5 text-[11px] font-semibold text-slate-400 border-b border-slate-800 flex items-center justify-between">
                      <span>Saved Inquiries</span>
                      <button
                        onClick={handleNewConversation}
                        className="text-sky-400 hover:underline flex items-center gap-1 text-[10px]"
                      >
                        <Plus className="h-3 w-3" /> New
                      </button>
                    </div>

                    {conversations.length === 0 ? (
                      <div className="p-3 text-[11px] text-slate-500 text-center">
                        No previous inquiries saved.
                      </div>
                    ) : (
                      conversations.map((c) => (
                        <div
                          key={c.id}
                          onClick={() => handleSelectConversation(c.id)}
                          className={`p-2 rounded-lg text-xs flex items-center justify-between transition cursor-pointer ${
                            c.id === activeConvId
                              ? 'bg-sky-950/60 text-sky-300 border border-sky-800/60'
                              : 'text-slate-300 hover:bg-slate-800/50'
                          }`}
                        >
                          <div className="truncate max-w-[190px]">
                            <div className="truncate font-medium">{c.title}</div>
                            <div className="text-[10px] text-slate-500">
                              {c.message_count} messages
                            </div>
                          </div>
                          <button
                            onClick={(e) => handleDeleteConversation(e, c.id)}
                            className="p-1 text-slate-500 hover:text-rose-400 transition"
                            title="Delete conversation"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <button
                onClick={handleNewConversation}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition cursor-pointer shadow-sm"
              >
                <Plus className="h-3.5 w-3.5" />
                New Chat
              </button>
            </div>
          }
        />

        {/* Suggested Questions Quick Access */}
        <div className="space-y-1.5 shrink-0">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>RECOMMENDED INQUIRIES</span>
            <span className="text-[10px] text-slate-500">Click to populate</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUERIES.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#11192e] hover:bg-[#16213d] border border-slate-800/80 hover:border-sky-500/50 text-[11px] text-slate-300 transition cursor-pointer disabled:opacity-40"
              >
                <Sparkles className="h-3 w-3 text-sky-400 shrink-0" />
                <span className="truncate max-w-xs">{q}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages Viewport */}
        <div className="flex-1 rounded-2xl bg-[#0c1221] border border-slate-800/80 p-4 md:p-5 space-y-4 overflow-y-auto shadow-inner flex flex-col justify-between">
          <div className="space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'assistant' && (
                  <div className="h-8 w-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl p-4 text-xs space-y-3 leading-relaxed shadow-sm ${
                    m.sender === 'user'
                      ? 'bg-sky-600 text-white shadow-sky-600/20'
                      : 'bg-[#121a2f] border border-slate-800 text-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-2 text-[10px]">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold uppercase tracking-wider font-mono">
                        {m.sender === 'user' ? 'Investigator Query' : 'Grounded Compliance Synthesis'}
                      </span>
                      {m.latency_ms !== undefined && (
                        <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-sky-400 border border-slate-700">
                          {m.latency_ms.toFixed(0)}ms
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <span>{m.timestamp}</span>
                      {m.sender === 'assistant' && (
                        <button
                          onClick={() => handleCopy(m.id, m.text)}
                          className="hover:text-white transition p-0.5 cursor-pointer"
                          title="Copy response"
                        >
                          {copiedId === m.id ? (
                            <Check className="h-3 w-3 text-emerald-400" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="prose prose-invert prose-xs max-w-none">
                    <MarkdownView content={m.text} />
                  </div>

                  {/* Grounded Policy Citations */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/60 space-y-2">
                      <span className="text-[10px] font-semibold text-sky-400 uppercase font-mono tracking-wider flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5" />
                        Grounded Sources & Policy Excerpts ({m.citations.length})
                      </span>
                      <div className="space-y-1.5">
                        {m.citations.map((c, cIdx) => (
                          <SourceCitationView key={cIdx} citation={c} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {m.sender === 'user' && (
                  <div className="h-8 w-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 justify-start items-center text-xs text-slate-400 font-mono">
                <div className="h-8 w-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
                  <Bot className="h-4 w-4 animate-spin" />
                </div>
                <div className="p-3 rounded-xl bg-[#121a2f] border border-slate-800 flex items-center gap-2.5">
                  <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse" />
                  Retrieving indexed compliance guidance & synthesizing answer...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Controls */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2 shrink-0"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question grounded in AML/KYC policies or fraud typologies..."
            className="flex-1 bg-[#0c1221] border border-slate-700/80 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 shadow-sm font-sans"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-sky-600/20 transition cursor-pointer"
          >
            <Send className="h-4 w-4" />
            <span>Send</span>
          </button>
        </form>
      </div>
    </ErrorBoundary>
  );
};
