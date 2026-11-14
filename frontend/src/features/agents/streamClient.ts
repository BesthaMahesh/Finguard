import { getApiBase } from '../../services/api';

export interface SSEAgentEvent {
  event: string;
  data: any;
  ts?: string;
}

export type SSEEventHandler = (eventName: string, data: any) => void;

export async function streamAgentWorkflow(
  payload: {
    transaction_id?: number | null;
    step?: number;
    type?: string;
    amount?: number;
    name_orig?: string;
    old_balance_org?: number;
    new_balance_orig?: number;
    name_dest?: string;
    old_balance_dest?: number;
    new_balance_dest?: number;
  },
  onEvent: SSEEventHandler,
  signal?: AbortSignal
): Promise<void> {
  const base = getApiBase();
  const url = `${base}/agents/analyze/stream`;
  const token = localStorage.getItem('finguard_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let errorDetail = `Stream request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  if (!response.body) {
    throw new Error('ReadableStream not supported by response');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      if (!part.trim()) continue;
      const lines = part.split('\n');
      let currentEvent = 'message';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.replace('event:', '').trim();
        } else if (line.startsWith('data:')) {
          currentData += line.replace('data:', '').trim();
        }
      }

      if (currentData) {
        try {
          const parsed = JSON.parse(currentData);
          onEvent(currentEvent, parsed);
        } catch (e) {
          console.warn('Failed to parse SSE JSON payload:', currentData, e);
        }
      }
    }
  }

  if (buffer.trim()) {
    const lines = buffer.split('\n');
    let currentEvent = 'message';
    let currentData = '';
    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.replace('event:', '').trim();
      } else if (line.startsWith('data:')) {
        currentData += line.replace('data:', '').trim();
      }
    }
    if (currentData) {
      try {
        const parsed = JSON.parse(currentData);
        onEvent(currentEvent, parsed);
      } catch {
        // ignore
      }
    }
  }
}

