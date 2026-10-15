import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import {
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sliders,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
} from 'lucide-react';
import { api } from '../../services/api';
import { ModelEvaluation } from '../../types';
import { PageHeader } from '../../components/common/PageHeader';
import { MetricCard } from '../../components/common/MetricCard';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const ModelIntelligence: React.FC = () => {
  const [evaluation, setEvaluation] = useState<ModelEvaluation | null>(null);
  const [modelRegistry, setModelRegistry] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  useEffect(() => {
    loadModelData();
  }, []);

  const loadModelData = async () => {
    try {
      setLoading(true);
      const [evalData, regData] = await Promise.all([
        api.getModelEvaluation(),
        api.getModelRegistry(),
      ]);
      setEvaluation(evalData);
      setModelRegistry(regData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !evaluation) {
    return (
      <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
        <PageHeader
          title="Detection Performance"
          subtitle="Fraud detection quality, discrimination scores, confusion matrix, and feature impact"
          breadcrumbs={['FinGuard', 'Intelligence', 'Detection Performance']}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
          <LoadingSkeleton lines={2} />
        </div>
      </div>
    );
  }

  const cm = evaluation.confusion_matrix;
  const totalTest =
    (cm.true_negatives || 0) +
    (cm.false_positives || 0) +
    (cm.false_negatives || 0) +
    (cm.true_positives || 0);

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Detection Performance"
        subtitle="Fraud detection quality, discrimination scores, confusion matrix, and feature impact"
        breadcrumbs={['FinGuard', 'Intelligence', 'Detection Performance']}
        badge="Active Engine: v1.2"
        actions={
          <button
            onClick={loadModelData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        }
      />

      {/* Model Provenance Banner */}
      <div className="rounded-xl bg-[#0f172a] border border-slate-800 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-sm font-bold text-white">{evaluation.model_version}</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
              Active Production Inference
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">{evaluation.algorithm}</p>
          <div className="text-[11px] text-slate-400 mt-1">
            Evaluated on held-out test sample ({evaluation.test_sample_count.toLocaleString()} transactions,{' '}
            {evaluation.test_fraud_count} confirmed frauds) • Last evaluated: {new Date(evaluation.trained_at).toLocaleDateString()}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-300 flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <div>
              <div className="font-semibold text-emerald-200">Data Leakage Guard: Active</div>
              <div className="text-[10px] text-emerald-400">
                Checks that prevent the model from using future information it would not know at prediction time
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Business-Friendly Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Fraud Detection Quality"
          value={evaluation.pr_auc.toFixed(4)}
          explanation="Precision-Recall Score: Evaluates how well the model catches true frauds without creating unnecessary false alarms"
          variant="info"
        />

        <MetricCard
          label="Model Discrimination Score"
          value={evaluation.roc_auc.toFixed(4)}
          explanation="ROC-AUC Score: Measures the model's ability to rank fraudulent transactions above legitimate ones across thresholds"
          variant="success"
        />

        <MetricCard
          label="Balanced Accuracy (F1-Score)"
          value={evaluation.f1_score.toFixed(4)}
          explanation="Harmonic mean of precision and recall at the configured decision threshold"
          variant="warning"
        />

        <MetricCard
          label="Decision Review Threshold"
          value={`${(evaluation.threshold * 100).toFixed(0)}%`}
          explanation="Transactions with calibrated risk score at or above this threshold trigger mandatory human review"
          variant="default"
        />
      </div>

      {/* Confusion Matrix & Feature Importance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Card */}
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span>Decision Breakdown (Confusion Matrix)</span>
              <span className="text-[10px] text-slate-500 font-mono">
                Total Test Set: {totalTest.toLocaleString()}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Evaluates model predictions against confirmed historical outcomes on independent test data
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            {/* True Negatives */}
            <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40">
              <div className="text-slate-400 text-[11px] font-sans">Correctly Approved (True Negatives)</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">
                {cm.true_negatives.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">Legitimate transactions cleared</div>
            </div>

            {/* False Positives */}
            <div className="p-3.5 rounded-lg bg-amber-950/20 border border-amber-900/40">
              <div className="text-slate-400 text-[11px] font-sans">False Alarms (False Positives)</div>
              <div className="text-xl font-bold text-amber-400 mt-1">
                {cm.false_positives.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">Legitimate flagged for review</div>
            </div>

            {/* False Negatives */}
            <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/40">
              <div className="text-slate-400 text-[11px] font-sans">Missed Frauds (False Negatives)</div>
              <div className="text-xl font-bold text-rose-400 mt-1">
                {cm.false_negatives.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">Frauds not detected</div>
            </div>

            {/* True Positives */}
            <div className="p-3.5 rounded-lg bg-sky-950/20 border border-sky-900/40">
              <div className="text-slate-400 text-[11px] font-sans">Detected Frauds (True Positives)</div>
              <div className="text-xl font-bold text-sky-400 mt-1">
                {cm.true_positives.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">Correctly intercepted frauds</div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex justify-between items-center text-xs">
            <span className="text-slate-400">Precision at Threshold:</span>
            <span className="font-mono text-white font-bold">{(evaluation.precision * 100).toFixed(2)}%</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">Recall at Threshold:</span>
            <span className="font-mono text-white font-bold">{(evaluation.recall * 100).toFixed(2)}%</span>
          </div>
        </div>

        {/* Feature Importance Bar Chart */}
        <div className="rounded-xl bg-[#11192e] border border-slate-800/80 p-5 space-y-4 shadow-sm">
          <div>
            <h3 className="text-sm font-semibold text-white">Top Predictive Signals</h3>
            <p className="text-xs text-slate-400">
              Features contributing most significantly to model risk discrimination
            </p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={evaluation.feature_importance.slice(0, 7)}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 70, bottom: 5 }}
              >
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis
                  dataKey="feature"
                  type="category"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  width={100}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="importance" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Expandable Technical Details Area */}
      <div className="rounded-xl bg-[#11192e] border border-slate-800/80 overflow-hidden shadow-sm">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/40 transition cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-sky-400" />
            <span className="text-xs font-semibold text-slate-200">
              Technical Details & Model Specifications (Developers & Administrators)
            </span>
          </div>
          {showTechnicalDetails ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </button>

        {showTechnicalDetails && (
          <div className="p-4 pt-0 border-t border-slate-800 space-y-3 text-xs font-mono">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-500 text-[10px]">Algorithm Architecture</span>
                <div className="text-slate-200 font-bold mt-0.5">{evaluation.algorithm}</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-500 text-[10px]">Artifact File</span>
                <div className="text-slate-200 font-bold mt-0.5">finguard_rf_model.joblib</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-slate-500 text-[10px]">Explainability Engine</span>
                <div className="text-slate-200 font-bold mt-0.5">TreeSHAP Fast Exact Attribution</div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed font-sans pt-1">
              The model produces calibrated probabilities across PaySim financial typologies. Target leakage
              audits verify zero post-outcome information contamination. Decision thresholds are tuned to
              maintain precision above 80% while maximizing fraud detection coverage.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
