import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  FileCheck,
  Send,
  History,
  Crosshair,
} from 'lucide-react';
import { ExtractedField, Finding, ReviewDecision } from '../types';

interface FindingsPanelProps {
  documentId: string;
  fields: ExtractedField[];
  findings: Finding[];
  decisions: ReviewDecision[];
  selectedFinding: Finding | null;
  onSelectFinding: (finding: Finding | null) => void;
  onSubmitDecision: (decision: {
    action: string;
    confirmed_value?: string;
    field_id?: string;
    reason: string;
    finding_id?: string;
  }) => void;
  submittingDecision: boolean;
}

export const FindingsPanel: React.FC<FindingsPanelProps> = ({
  documentId,
  fields,
  findings,
  decisions,
  selectedFinding,
  onSelectFinding,
  onSubmitDecision,
  submittingDecision,
}) => {
  const [selectedHypothesis, setSelectedHypothesis] = useState<string>('');
  const [selectedFieldId, setSelectedFieldId] = useState<string>('');
  const [decisionAction, setDecisionAction] = useState<string>('CONFIRMED_HYPOTHESIS');
  const [decisionReason, setDecisionReason] = useState<string>('');

  // Limpeza de formulário ao alternar documento
  useEffect(() => {
    setSelectedHypothesis('');
    setSelectedFieldId('');
    setDecisionReason('');
    setDecisionAction('CONFIRMED_HYPOTHESIS');
  }, [documentId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!decisionReason.trim()) return;

    onSubmitDecision({
      action: decisionAction,
      confirmed_value: selectedHypothesis || undefined,
      field_id: selectedFieldId || undefined,
      reason: decisionReason,
      finding_id: selectedFinding?.id,
    });
    setDecisionReason('');
  };

  return (
    <div className="w-[430px] border-l border-graphite-800 bg-graphite-900/90 flex flex-col h-[calc(100vh-65px)] overflow-y-auto">
      {/* 1. Alertas e Achados Periciais */}
      <div className="p-4 border-b border-graphite-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between mb-3 font-mono">
          <span>Alertas de Inconsistência ({findings.length})</span>
          {findings.length > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded bg-auditRose-500/15 text-auditRose-500 border border-auditRose-500/20">
              Revisão Obrigatória
            </span>
          )}
        </h3>

        {findings.length === 0 ? (
          <div className="p-3 bg-graphite-950 rounded-lg border border-graphite-800 flex items-center gap-2 text-xs text-auditTeal-400">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Nenhuma inconsistência ou colisão LASA detectada neste documento.</span>
          </div>
        ) : (
          <div className="space-y-2.5">
            {findings.map((fn) => {
              const isSelected = selectedFinding?.id === fn.id;
              return (
                <div
                  key={fn.id}
                  onClick={() => onSelectFinding(isSelected ? null : fn)}
                  className={`p-3 rounded-lg border transition cursor-pointer ${
                    isSelected
                      ? 'bg-auditRose-500/10 border-auditRose-500/40 shadow-sm'
                      : 'bg-graphite-950 border-graphite-800 hover:border-graphite-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-semibold text-xs text-white leading-snug">
                      {fn.title}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded uppercase shrink-0 font-medium ${
                        fn.severity === 'CRITICAL'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : fn.severity === 'HIGH'
                          ? 'bg-auditRose-500/20 text-auditRose-400 border border-auditRose-500/30'
                          : 'bg-auditAmber-500/20 text-auditAmber-400 border border-auditAmber-500/30'
                      }`}
                    >
                      {fn.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed mb-2">
                    {fn.explanation}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-graphite-800/80">
                    <span className="font-mono text-[10px] opacity-75">{fn.rule_id}</span>
                    <button className="flex items-center gap-1 text-auditTeal-400 hover:underline">
                      <Crosshair className="w-3 h-3" />
                      <span>{isSelected ? 'Ocultar BBox' : 'Ver Evidência'}</span>
                    </button>
                  </div>

                  {fn.limitations && (
                    <p className="mt-2 text-[10px] text-slate-500 italic bg-graphite-900/60 p-1.5 rounded">
                      Limitação: {fn.limitations}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. Leitura com Admissão de Dúvida (Hipóteses) */}
      <div className="p-4 border-b border-graphite-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3 font-mono flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-auditAmber-400" />
          Hipóteses de Leitura do VLM
        </h3>

        <div className="space-y-3">
          {fields.map((field) => (
            <div key={field.id} className="bg-graphite-950 p-3 rounded-lg border border-graphite-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-mono uppercase text-slate-400">
                  Campo: {field.field_type}
                </span>
                {field.uncertainty_status === 'AMBIGUOUS' ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-auditAmber-500/15 text-auditAmber-400 border border-auditAmber-500/30 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Ambiguidade Detectada
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-auditTeal-500/15 text-auditTeal-400">
                    Certeza Visual
                  </span>
                )}
              </div>

              <div className="space-y-1.5">
                {field.hypotheses.map((hyp) => {
                  const isChecked = selectedHypothesis === hyp.text;
                  return (
                    <label
                      key={hyp.rank}
                      className={`flex items-center justify-between p-2 rounded border cursor-pointer transition text-xs ${
                        isChecked
                          ? 'bg-auditTeal-500/15 border-auditTeal-500/40 text-white font-medium'
                          : 'bg-graphite-900/70 border-graphite-800 text-slate-300 hover:border-graphite-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          name={`hyp-${field.id}`}
                          value={hyp.text}
                          checked={isChecked}
                          onChange={() => {
                            setSelectedHypothesis(hyp.text);
                            setSelectedFieldId(field.id);
                          }}
                          className="accent-auditTeal-500"
                        />
                        <span>{hyp.text}</span>
                      </div>
                      {hyp.score !== null && hyp.score !== undefined && (
                        <span className="text-[11px] font-mono text-slate-400">
                          {Math.round(hyp.score * 100)}%
                        </span>
                      )}
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Decisão Humana Obrigatória (Human-in-the-Loop) */}
      <div className="p-4 border-b border-graphite-800 bg-graphite-950/40">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3 font-mono flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-auditTeal-400" />
          Parecer do Auditor Humano (HITL)
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Ação da Decisão</label>
            <select
              value={decisionAction}
              onChange={(e) => setDecisionAction(e.target.value)}
              className="w-full bg-graphite-950 border border-graphite-800 rounded p-2 text-xs text-white focus:outline-none focus:border-auditTeal-500"
            >
              <option value="CONFIRMED_HYPOTHESIS">Confirmar Hipótese Selecionada</option>
              <option value="APPROVED_CLAIM">Aprovar Guia Integralmente</option>
              <option value="REJECTED_CLAIM">Rejeitar por Inconsistência Documental</option>
              <option value="ESCALATED_FORENSIC">Escalar para Auditoria Forense</option>
              <option value="REQUESTED_CLARIFICATION">Solicitar Receita Legível ao Médico</option>
            </select>
          </div>

          {selectedHypothesis && (
            <div className="p-2 bg-graphite-950 rounded border border-graphite-800 text-xs">
              <span className="text-slate-400 block text-[10px]">Valor Confirmado:</span>
              <span className="font-mono text-auditTeal-400 font-semibold">{selectedHypothesis}</span>
            </div>
          )}

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">
              Justificativa Obrigatória do Auditor <span className="text-red-400">*</span>
            </label>
            <textarea
              required
              rows={3}
              placeholder="Descreva a fundamentação da conferência visual, contexto clínico ou indício..."
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              className="w-full bg-graphite-950 border border-graphite-800 rounded p-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-auditTeal-500 resize-none font-sans"
            />
          </div>

          <button
            type="submit"
            disabled={submittingDecision || !decisionReason.trim()}
            className="w-full py-2 px-3 bg-auditTeal-500 hover:bg-auditTeal-400 disabled:opacity-50 text-graphite-950 font-bold text-xs rounded-md transition flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Send className="w-3.5 h-3.5" />
            {submittingDecision ? 'Registrando Decisão...' : 'Registrar Decisão no Prontuário'}
          </button>
        </form>
      </div>

      {/* 4. Histórico de Decisões Persistidas */}
      <div className="p-4 flex-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 font-mono flex items-center gap-2">
          <History className="w-3.5 h-3.5" />
          Histórico Persistido ({decisions.length})
        </h3>

        {decisions.length === 0 ? (
          <p className="text-xs text-slate-600 italic text-center py-2">
            Nenhuma decisão humana registrada ainda.
          </p>
        ) : (
          <div className="space-y-2">
            {decisions.map((dec) => (
              <div key={dec.id} className="p-2.5 rounded bg-graphite-950 border border-graphite-800 text-xs">
                <div className="flex items-center justify-between text-[11px] mb-1">
                  <span className="font-mono text-auditTeal-400 font-medium">{dec.action}</span>
                  <span className="text-slate-500 font-mono text-[10px]">
                    {new Date(dec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                {dec.confirmed_value && (
                  <p className="text-[11px] text-slate-300 font-mono mb-1">
                    Valor: <span className="text-white font-semibold">{dec.confirmed_value}</span>
                  </p>
                )}
                <p className="text-slate-400 text-[11px] leading-relaxed italic">
                  "{dec.reason}"
                </p>
                <span className="text-[10px] text-slate-600 block mt-1 font-mono">
                  Por: {dec.actor_id}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
