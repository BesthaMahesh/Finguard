export interface AgentNodeState {
  id: string;
  label: string;
  role: string;
  status: 'waiting' | 'running' | 'completed' | 'skipped' | 'failed';
  duration_ms: number | null;
  summary: Record<string, any>;
  output: Record<string, any>;
  tokens: string;
  error?: string | null;
}

export interface WorkflowVerdict {
  risk_score: number;
  risk_tier: string;
  decision: string;
  narrative: string;
  case_id?: string | null;
}

export interface WorkflowRunState {
  runId: string | null;
  transactionId: number | null;
  agents: AgentNodeState[];
  overallStatus: 'idle' | 'running' | 'completed' | 'failed';
  verdict: WorkflowVerdict | null;
  liveNarrative: string;
  duration_ms: number | null;
  error: string | null;
}

export const DEFAULT_AGENTS: Array<{ id: string; label: string; role: string }> = [
  {
    id: 'supervisor_plan',
    label: 'Supervisor Agent',
    role: 'Orchestrator: Evaluates intent, assigns correlation ID, and dynamically routes workflow.',
  },
  {
    id: 'intake',
    label: 'Transaction Intake Agent',
    role: 'Validator: Validates payload schema, formats decimals, and unpacks account numbers.',
  },
  {
    id: 'data_quality',
    label: 'Data Quality Agent',
    role: 'LeakageGuard: Checks balance signs and ensures zero target label leakage.',
  },
  {
    id: 'fraud_detector',
    label: 'Fraud Detection Agent',
    role: 'ML Classifier: Runs Random Forest inference and evaluates deterministic fraud rules.',
  },
  {
    id: 'market_credit_risk',
    label: 'Market & Credit Risk Agent',
    role: 'Risk Quant: Evaluates portfolio volatility, exposure ratio, and parametric 95% VaR.',
  },
  {
    id: 'risk_assessment',
    label: 'Risk Assessment Agent',
    role: 'Score Synthesizer: Blends ML probabilities and rule penalties into a 0-100 composite risk score.',
  },
  {
    id: 'investigator',
    label: 'Investigation Agent',
    role: 'Forensic Analyst: Examines rapid balance liquidation deltas and counterparty relationship graphs.',
  },
  {
    id: 'policy_compliance',
    label: 'Policy & Compliance Agent',
    role: 'Regulatory RAG: Queries vector store to pull statutory citations (FATF Rec 16, AML-04).',
  },
  {
    id: 'explainability',
    label: 'Explainability Agent',
    role: 'Narrative Generator: Synthesizes TreeSHAP feature attributions and policies into an objective report via Groq LLM.',
  },
  {
    id: 'audit_reporter',
    label: 'Audit & Reporting Agent',
    role: 'Ledger Sealer: Packages the forensic docket, masks PII, and seals a SHA-256 chained audit record.',
  },
];

export function createInitialWorkflowState(): WorkflowRunState {
  return {
    runId: null,
    transactionId: null,
    agents: DEFAULT_AGENTS.map((a) => ({
      ...a,
      status: 'waiting',
      duration_ms: null,
      summary: {},
      output: {},
      tokens: '',
      error: null,
    })),
    overallStatus: 'idle',
    verdict: null,
    liveNarrative: '',
    duration_ms: null,
    error: null,
  };
}

export function applyEvent(
  state: WorkflowRunState,
  event: { event: string; data: any }
): WorkflowRunState {
  const { event: eventName, data } = event;

  switch (eventName) {
    case 'run_start': {
      const incomingAgents = data.agents || DEFAULT_AGENTS;
      return {
        ...state,
        runId: data.run_id || state.runId,
        transactionId: data.transaction_id || state.transactionId,
        overallStatus: 'running',
        verdict: null,
        liveNarrative: '',
        duration_ms: null,
        error: null,
        agents: incomingAgents.map((a: any) => ({
          id: a.id,
          label: a.label,
          role: a.role,
          status: 'waiting',
          duration_ms: null,
          summary: {},
          output: {},
          tokens: '',
          error: null,
        })),
      };
    }

    case 'agent_start': {
      return {
        ...state,
        agents: state.agents.map((agent) =>
          agent.id === data.agent
            ? { ...agent, status: 'running' }
            : agent
        ),
      };
    }

    case 'agent_token': {
      const token = data.text || '';
      return {
        ...state,
        liveNarrative: state.liveNarrative + token,
        agents: state.agents.map((agent) =>
          agent.id === data.agent
            ? { ...agent, tokens: agent.tokens + token }
            : agent
        ),
      };
    }

    case 'agent_end': {
      const isSkipped = data.status === 'SKIPPED';
      return {
        ...state,
        agents: state.agents.map((agent) => {
          if (agent.id === data.agent) {
            return {
              ...agent,
              status: isSkipped ? 'skipped' : 'completed',
              duration_ms: data.duration_ms ?? 0,
              summary: data.summary || {},
              output: data.output || {},
            };
          }
          return agent;
        }),
      };
    }

    case 'agent_error': {
      return {
        ...state,
        agents: state.agents.map((agent) =>
          agent.id === data.agent
            ? {
                ...agent,
                status: 'failed',
                error: data.error || 'Agent encountered runtime error',
              }
            : agent
        ),
      };
    }

    case 'run_end': {
      const result = data.result || {};
      return {
        ...state,
        overallStatus: 'completed',
        duration_ms: data.duration_ms ?? state.duration_ms,
        verdict: {
          risk_score: result.risk_score ?? 0,
          risk_tier: result.risk_tier ?? 'LOW',
          decision: result.decision ?? 'APPROVED',
          narrative: result.narrative ?? state.liveNarrative,
          case_id: result.case_id || null,
        },
      };
    }

    case 'run_error': {
      return {
        ...state,
        overallStatus: 'failed',
        error: data.error || 'Workflow execution error',
      };
    }

    default:
      return state;
  }
}

export function replayEvents(events: Array<{ event: string; data: any }>): WorkflowRunState {
  let current = createInitialWorkflowState();
  for (const ev of events) {
    current = applyEvent(current, ev);
  }
  return current;
}

