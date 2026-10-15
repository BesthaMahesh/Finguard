import {
  UserProfile,
  DashboardSummary,
  Transaction,
  InvestigationCase,
  ModelEvaluation,
  AuditEvent,
  ObservabilitySummary,
  PolicyCitation,
} from '../types';

const RAW_API_URL = (import.meta.env.VITE_API_URL as string) || '';
const API_BASE = RAW_API_URL ? `${RAW_API_URL.replace(/\/$/, '')}/api/v1` : '/api/v1';

let currentToken: string | null = localStorage.getItem('finguard_token');

export const setAuthToken = (token: string | null) => {
  currentToken = token;
  if (token) {
    localStorage.setItem('finguard_token', token);
  } else {
    localStorage.removeItem('finguard_token');
  }
};

const getHeaders = () => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (currentToken) {
    headers['Authorization'] = `Bearer ${currentToken}`;
  }
  return headers;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    let msg = '';
    if (typeof errData.detail === 'string') {
      msg = errData.detail;
    } else if (Array.isArray(errData.detail)) {
      msg = errData.detail
        .map((d: any) => {
          if (typeof d === 'string') return d;
          const loc = d.loc ? d.loc.filter((x: any) => x !== 'body').join('.') : '';
          return loc ? `${loc}: ${d.msg || 'invalid'}` : (d.msg || JSON.stringify(d));
        })
        .join('; ');
    } else if (errData.error && typeof errData.error === 'string') {
      msg = errData.error;
    } else if (errData.message && typeof errData.message === 'string') {
      msg = errData.message;
    } else {
      msg = `HTTP Error ${res.status}: ${res.statusText || 'Request failed'}`;
    }
    throw new Error(msg || `HTTP Error ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(username: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
    const res = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await handleResponse<any>(res);
    setAuthToken(data.access_token);
    return {
      access_token: data.access_token,
      user: {
        id: data.user_id,
        username: data.username,
        full_name: data.full_name,
        email: data.email || `${data.username}@finguard.local`,
        role: data.role,
        is_active: true,
      },
    };
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: getHeaders(),
      });
    } finally {
      setAuthToken(null);
    }
  },

  async getCurrentUser(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    return handleResponse<UserProfile>(res);
  },

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard/summary`, { headers: getHeaders() });
    return handleResponse<DashboardSummary>(res);
  },

  // Transactions
  async getTransactions(params: {
    limit?: number;
    offset?: number;
    type?: string;
    risk_level?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<{ items: Transaction[]; total: number }> {
    const query = new URLSearchParams();
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset) query.set('offset', String(params.offset));
    if (params.type) query.set('type', params.type);
    if (params.risk_level) query.set('risk_level', params.risk_level);
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    const res = await fetch(`${API_BASE}/transactions?${query.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getTransactionDetail(id: number): Promise<Transaction & { rule_flags: any[]; feature_contributions: any[] }> {
    const res = await fetch(`${API_BASE}/transactions/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Risk
  async analyzeRisk(txData: any, useMultiAgent = true): Promise<any> {
    const res = await fetch(`${API_BASE}/risk/analyze`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ ...txData, use_multi_agent: useMultiAgent }),
    });
    return handleResponse(res);
  },

  // Investigations
  async getInvestigations(params?: { status?: string; priority?: string }): Promise<{ items: InvestigationCase[]; total: number }> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.priority) query.set('priority', params.priority);
    const res = await fetch(`${API_BASE}/investigations?${query.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getInvestigationDetail(id: string): Promise<InvestigationCase> {
    const res = await fetch(`${API_BASE}/investigations/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async submitReview(caseId: string, disposition: string, notes: string): Promise<InvestigationCase> {
    const res = await fetch(`${API_BASE}/investigations/${caseId}/review`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ disposition, disposition_notes: notes }),
    });
    return handleResponse(res);
  },

  // Models
  async getModelRegistry(): Promise<any> {
    const res = await fetch(`${API_BASE}/models`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getModelEvaluation(): Promise<ModelEvaluation> {
    const res = await fetch(`${API_BASE}/models/evaluation`, { headers: getHeaders() });
    return handleResponse<ModelEvaluation>(res);
  },

  // Knowledge / RAG
  async getKnowledgeStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/status`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getKnowledgeDocuments(params: { category?: string; file_type?: string; search?: string } = {}): Promise<{ total: number; items: any[] }> {
    const query = new URLSearchParams();
    if (params.category && params.category !== 'all') query.set('category', params.category);
    if (params.file_type && params.file_type !== 'all') query.set('file_type', params.file_type);
    if (params.search) query.set('search', params.search);

    const res = await fetch(`${API_BASE}/knowledge/documents?${query.toString()}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getKnowledgeDocumentDetail(documentId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/documents/${documentId}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async searchKnowledge(query: string, top_k = 4, category?: string, min_relevance_score = 0.40): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/search`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ query, top_k, category, min_relevance_score }),
    });
    return handleResponse(res);
  },

  async searchPolicies(query: string, top_k = 3): Promise<{ query: string; citations: PolicyCitation[] }> {
    const res = await fetch(`${API_BASE}/knowledge/search`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ query, top_k }),
    });
    return handleResponse(res);
  },

  async triggerKnowledgeIngest(forceReindex = false): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/ingest`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ force_reindex: forceReindex }),
    });
    return handleResponse(res);
  },

  async triggerDocumentReindex(docId?: string, reindexAll = false): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/reindex`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ doc_id: docId, reindex_all: reindexAll }),
    });
    return handleResponse(res);
  },

  async deleteKnowledgeDocument(docId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/knowledge/documents/${docId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async uploadKnowledgeDocument(file: File, category: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    const headers: Record<string, string> = {};
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`;
    }

    const res = await fetch(`${API_BASE}/knowledge/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return handleResponse(res);
  },

  // Audit
  async getAuditEvents(limit = 50): Promise<{ items: AuditEvent[]; total: number }> {
    const res = await fetch(`${API_BASE}/audit?limit=${limit}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // Observability
  async getObservabilitySummary(): Promise<ObservabilitySummary> {
    const res = await fetch(`${API_BASE}/observability/summary`, { headers: getHeaders() });
    return handleResponse<ObservabilitySummary>(res);
  },

  // AI Risk Assistant
  async getAssistantConversations(): Promise<{ conversations: Array<{ id: string; title: string; message_count: number; created_at: string; updated_at: string }> }> {
    const res = await fetch(`${API_BASE}/assistant/conversations`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async createAssistantConversation(title?: string): Promise<{ id: string; title: string; created_at: string }> {
    const res = await fetch(`${API_BASE}/assistant/conversations`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ title }),
    });
    return handleResponse(res);
  },

  async getAssistantConversationDetail(id: string): Promise<{ id: string; title: string; messages: any[] }> {
    const res = await fetch(`${API_BASE}/assistant/conversations/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async deleteAssistantConversation(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/assistant/conversations/${id}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async chatAssistant(
    message: string,
    conversationId?: string
  ): Promise<{ reply: string; citations: PolicyCitation[]; conversation_id: string; llm_provider: string; model: string; latency_ms?: number }> {
    const res = await fetch(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    return handleResponse(res);
  },

  // MCP Tools
  async getMCPTools(): Promise<{ server: string; protocol: string; tools: any[] }> {
    const res = await fetch(`${API_BASE}/mcp/tools`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async callMCPTool(name: string, args: Record<string, any>): Promise<any> {
    const res = await fetch(`${API_BASE}/mcp/tools/call`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ name, arguments: args }),
    });
    return handleResponse(res);
  },

  // User Management (Admin Only)
  async getUsers(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/auth/users`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async updateUserStatus(userId: string, isActive: boolean): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/users/${userId}/status`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({ is_active: isActive }),
    });
    return handleResponse(res);
  },

  async resetUserPassword(userId: string, newPassword: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/users/${userId}/reset-password`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ new_password: newPassword }),
    });
    return handleResponse(res);
  },

  // Health and System Diagnostics
  async getHealth(): Promise<{ status: string; service: string; environment: string; architecture_layers: number; version: string; telemetry: string }> {
    const res = await fetch(`${API_BASE}/health`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getReadiness(): Promise<{ status: string; database: string; model_engine: string; knowledge_rag: string }> {
    const res = await fetch(`${API_BASE}/ready`, { headers: getHeaders() });
    return handleResponse(res);
  },
};
