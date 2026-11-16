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
    role: 'Workflow Orchestration: Initializes investigation context, assigns audit session ID, and dynamically routes triage path.',
  },
  {
    id: 'intake',
    label: 'Transaction Intake Agent',
    role: 'Ingestion & Normalization: Validates transaction schema, standardizes currency precision, and verifies counterparty identifiers.',
  },
  {
    id: 'data_quality',
    label: 'Data Quality Agent',
    role: 'Ledger Reconciliation & Integrity: Verifies double-entry ledger math, detects balance anomalies, and ensures data integrity.',
  },
  {
    id: 'fraud_detector',
    label: 'Fraud Detection Agent',
    role: 'Predictive Fraud Analytics: Evaluates machine learning fraud probabilities and triggers statutory rule screening.',
  },
  {
    id: 'market_credit_risk',
    label: 'Market & Credit Risk Agent',
    role: 'Exposure & Liquidity Analytics: Assesses counterparty exposure limits, portfolio concentration, and 95% Value-at-Risk.',
  },
  {
    id: 'risk_assessment',
    label: 'Risk Assessment Agent',
    role: 'Composite Risk Scoring: Synthesizes predictive probabilities, exposure metrics, and statutory penalties into a calibrated 0–100 risk score.',
  },
  {
    id: 'investigator',
    label: 'Investigation Agent',
    role: 'Forensic Pattern Analysis: Investigates rapid account liquidation, transaction velocity, and counterparty relationship graphs.',
  },
  {
    id: 'policy_compliance',
    label: 'Policy & Compliance Agent',
    role: 'Statutory & Regulatory Compliance: Cross-references regulatory frameworks (FATF Recommendation 16, AML-04, KYC) and binds citations.',
  },
  {
    id: 'explainability',
    label: 'Explainability Agent',
    role: 'Explainability & Decision Support: Translates model feature attributions and policy requirements into an objective compliance narrative.',
  },
  {
    id: 'audit_reporter',
    label: 'Audit & Reporting Agent',
    role: 'Audit & Governance Finalizer: Assembles the forensic dossier, redacts customer PII, and seals the tamper-evident SHA-256 audit record.',
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

