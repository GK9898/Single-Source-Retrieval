'use client';

import React from 'react';
import { BarChart3, CheckCircle2 } from 'lucide-react';
import { EvaluateMetrics } from '../types';

interface EvaluationPanelProps {
  metrics?: EvaluateMetrics;
}

export const EvaluationPanel: React.FC<EvaluationPanelProps> = ({ metrics }) => {
  if (!metrics) return null;

  const items = [
    { label: 'Faithfulness', value: metrics.faithfulness, desc: 'Factual accuracy against retrieved context' },
    { label: 'Answer Relevance', value: metrics.answer_relevance, desc: 'Query alignment of synthesized answer' },
    { label: 'Context Recall', value: metrics.context_recall, desc: 'Coverage of required ground truth data' },
    { label: 'Context Precision', value: metrics.context_precision, desc: 'Signal-to-noise ratio in FAISS chunks' },
  ];

  return (
    <div className="w-full bg-slate-900/60 border border-slate-700/60 rounded-lg p-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <BarChart3 className="w-3.5 h-3.5 text-emerald-400" /> RAGAS Quality Audit
        </span>
        <span className="text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-700/40 px-2 py-0.5 rounded">
          Overall: {(metrics.overall_score * 100).toFixed(0)}%
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map((m, i) => (
          <div key={i} className="bg-slate-800/60 p-2 rounded border border-slate-700/40">
            <div className="flex justify-between text-[11px] font-medium text-slate-300">
              <span>{m.label}</span>
              <span className="text-emerald-400 font-bold">{(m.value * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-700/60 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full transition-all duration-500"
                style={{ width: `${m.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
