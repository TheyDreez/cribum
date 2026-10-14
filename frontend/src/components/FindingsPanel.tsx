import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  FileCheck,
  Send,
  History,
} from 'lucide-react';
import { ExtractedField, Finding, ReviewDecision, ReviewSubmission } from '../types';
import { DOCUMENT_CID_CONTEXT, evaluateHypothesisClinicalMatch } from '../clinicalCorrelation';

interface FindingsPanelProps {
  documentId: string;
  fields: ExtractedField[];
  findings: Finding[];
  decisions: ReviewDecision[];
  selectedFinding: Finding | null;
  onSelectFinding: (finding: Finding | null) => void;
  onSubmitDecision: (decision: ReviewSubmission) => Promise<boolean>;
  submittingDecision: boolean;
  reviewError?: string | null;
  onOpenReportModal?: () => void;
}

const getUncertaintyBadge = (status: string) => {
  switch (status) {
    case 'AMBIGUOUS':
      return {
        label: 'Ambiguidade Caligráfica',
        style: 'bg-amber-50 text-amber-800 border-amber-200',
        icon: AlertTriangle,
      };
    case 'INDETERMINATE':
      return {
        label: 'Leitura Indeterminada',
        style: 'bg-purple-50 text-purple-800 border-purple-200',
        icon: HelpCircle,
      };
    case 'CERTAIN':
    default:
      return {
        label: 'Leitura Unívoca',
        style: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        icon: CheckCircle2,
      };
  }
};

export const FindingsPanel: React.FC<FindingsPanelProps> = ({
  documentId,
  fields,
  findings,
  decisions,
  selectedFinding,
  onSelectFinding,
  onSubmitDecision,
  submittingDecision,
  reviewError,
  onOpenReportModal,
}) => {
  const [selectedHypothesis, setSelectedHypothesis] = useState<string>('');
  const [selectedFieldId, setSelectedFieldId] = useState<string>('');
  const [decisionAction, setDecisionAction] = useState<string>('CONFIRMED_HYPOTHESIS');
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [historyOpen, setHistoryOpen] = useState<boolean>(true);

  const cidContext = DOCUMENT_CID_CONTEXT[documentId] || null;

  // Limpeza de formulário ao alternar documento
  useEffect(() => {
    setSelectedHypothesis('');
    setSelectedFieldId('');
    setDecisionReason('');
    setDecisionAction('CONFIRMED_HYPOTHESIS');
  }, [documentId]);

  const isConfirmation = decisionAction === 'CONFIRMED_HYPOTHESIS';
  const isFormValid =
    decisionReason.trim().length >= 3 &&
    (!isConfirmation || (selectedHypothesis.length > 0 && selectedFieldId.length > 0));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid || submittingDecision) return;

    const saved = await onSubmitDecision({
      action: decisionAction,
      confirmed_value: isConfirmation ? selectedHypothesis : undefined,
      field_id: isConfirmation ? selectedFieldId : undefined,
      reason: decisionReason.trim(),
      finding_id: selectedFinding?.id,
    });

    if (saved) {
      setDecisionReason('');
    }
  };

  return (
    <div id="review-panel" className="w-full min-w-0 border-l border-slate-200 bg-white flex flex-col h-full overflow-y-auto shadow-xs">
      {/* 1. Alertas de Inconsistência e Achados Periciais */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between gap-2 mb-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-2">
            <span>Alertas de Inconsistência ({findings.length})</span>
            {findings.length > 0 && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
                Revisão Obrigatória
              </span>
            )}
          </h3>

          {onOpenReportModal && (
            <button
              type="button"
              data-testid="export-forensic-report-btn"
              onClick={onOpenReportModal}
              className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium flex items-center gap-1.5 transition shadow-2xs shrink-0"
              title="Gerar laudo pericial formal em PDF"
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Exportar Laudo</span>
            </button>
          )}
        </div>

        {findings.length === 0 ? (
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-start gap-2.5 text-xs text-slate-700">
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
            <div className="leading-relaxed">
              <span className="font-semibold text-slate-800 block mb-0.5">
                Sem inconsistências de regra detectadas pelo motor determinístico
              </span>
              <span className="text-[11px] text-slate-500 block">
                Não substitui conferência clínica, posológica e cadastral do auditor responsável.
              </span>
            </div>
          </div>
        ) : (
          <div className="space-y-2.5">
            {findings.map((fn) => {
              const isSelected = selectedFinding?.id === fn.id;
              return (
                <div
                  key={fn.id}
                  onClick={() => onSelectFinding(isSelected ? null : fn)}
                  className={`p-3 rounded-lg border transition cursor-pointer shadow-2xs ${
                    isSelected
                      ? 'bg-rose-50/50 border-rose-300 ring-1 ring-rose-200'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-semibold text-xs text-slate-900 leading-snug">
                      {fn.title}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase shrink-0 font-medium ${
                        fn.severity === 'CRITICAL'
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : fn.severity === 'HIGH'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      {fn.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed font-sans">{fn.explanation}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 mt-2 border-t border-slate-100 font-mono">
                    <span className="text-slate-500 font-mono">{fn.rule_id}</span>
                  </div>
                  {fn.limitations && (
                    <p className="text-[11px] text-slate-500 mt-2 italic font-sans border-t border-slate-100 pt-1.5">
                      Limitação técnica: {fn.limitations}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* DIFERENCIAL 2: Card Inteligente de Subsidiação e Correlação Clínica (CID-10 × Prescrição) */}
      {cidContext && (
        <div
          data-testid="clinical-correlation-card"
          className="m-4 mb-0 p-3 rounded-lg border border-slate-200 bg-slate-50/80 space-y-2 shadow-2xs"
        >
          <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
            <span className="font-mono font-bold text-[11px] uppercase text-slate-800">
              Correlação Clínica (CID-10 × Prescrição)
            </span>
            <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-900 text-white">
              CID {cidContext.cid}
            </span>
          </div>

          <div className="text-[11px] text-slate-700">
            Diagnóstico da Guia:{' '}
            <strong className="text-slate-900">
              CID {cidContext.cid} ({cidContext.description})
            </strong>
          </div>

          <div className="space-y-1.5 pt-1">
            {fields
              .filter((f) => f.field_type === 'medication' || f.field_type === 'item')
              .flatMap((f) => f.hypotheses)
              .map((hyp) => {
                const match = evaluateHypothesisClinicalMatch(documentId, hyp.text);
                const isCompatible = match.status === 'COMPATIBLE';
                const isDiscrepant = match.status === 'DISCREPANT';

                return (
                  <div
                    key={hyp.rank + hyp.text}
                    className="p-2 rounded bg-white border border-slate-200 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-slate-900">
                        #{hyp.rank} {hyp.text}
                      </span>
                      <span
                        data-testid={`clinical-badge-rank-${hyp.rank}`}
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                          isCompatible
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                            : isDiscrepant
                            ? 'bg-amber-50 text-amber-700 border-amber-300'
                            : 'bg-slate-100 text-slate-700 border-slate-300'
                        }`}
                      >
                        {match.badgeLabel}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 font-sans">{match.therapeuticClass}</div>
                    {match.lasaWarning && hyp.rank === 1 && (
                      <div className="mt-1 p-1.5 rounded bg-red-50 border border-red-200 text-red-700 text-[10px] font-medium leading-relaxed">
                        {match.lasaWarning}
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* 2. Leitura com Admissão de Dúvida (Hipóteses do VLM) */}
      <div className="p-4 border-b border-slate-200">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-amber-600" />
          Hipóteses de Leitura do VLM
        </h3>

        <div className="space-y-3">
          {fields.map((field) => {
            const badge = getUncertaintyBadge(field.uncertainty_status);
            const BadgeIcon = badge.icon;

            return (
              <div key={field.id} className="bg-slate-50/70 p-3 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono uppercase text-slate-500 font-semibold">
                    Campo: {field.field_type}
                  </span>
                  <span
                    className={`text-[10px] font-medium px-2 py-0.5 rounded border flex items-center gap-1 ${badge.style}`}
                  >
                    <BadgeIcon className="w-3 h-3" />
                    {badge.label}
                  </span>
                </div>

                <div className="space-y-1.5">
                  {field.hypotheses.map((hyp) => {
                    const isChecked = selectedHypothesis === hyp.text && selectedFieldId === field.id;
                    return (
                      <label
                        key={hyp.rank}
                        onClick={() => {
                          setSelectedHypothesis(hyp.text);
                          setSelectedFieldId(field.id);
                        }}
                        className={`flex items-center justify-between p-2 rounded border cursor-pointer transition text-xs shadow-2xs ${
                          isChecked
                            ? 'bg-blue-50 border-blue-400 text-blue-950 font-medium'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
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
                            className="accent-blue-600"
                          />
                          <span className="font-sans">{hyp.text}</span>
                        </div>
                        {hyp.score !== null && hyp.score !== undefined && (
                          <span
                            className="text-[10px] font-mono text-slate-400"
                            title="Score heurístico do modelo VLM (não calibrado probabilisticamente)"
                          >
                            Score: {Number(hyp.score).toFixed(2)} (não calibrado)
                          </span>
                        )}
                      </label>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Decisão Humana Obrigatória (Human-in-the-Loop) */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/50">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 mb-3 flex items-center gap-1.5">
          <FileCheck className="w-4 h-4 text-blue-600" />
          Parecer do Auditor Humano (HITL)
        </h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-[11px] text-slate-600 font-medium mb-1">Ação da Decisão</label>
            <select
              value={decisionAction}
              onChange={(e) => setDecisionAction(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded p-2 text-xs text-slate-900 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 shadow-2xs font-sans"
            >
              <option value="CONFIRMED_HYPOTHESIS">Confirmar Hipótese Selecionada</option>
              <option value="APPROVED_CLAIM">Aprovar Guia Integralmente</option>
              <option value="REJECTED_CLAIM">Rejeitar por Inconsistência Documental</option>
              <option value="ESCALATED_FORENSIC">Escalar para Auditoria Forense</option>
              <option value="REQUESTED_CLARIFICATION">Solicitar Receita Legível ao Médico</option>
            </select>
          </div>

          {isConfirmation && (
            <div className="p-2.5 bg-white rounded border border-slate-200 text-xs shadow-2xs">
              <span className="text-slate-500 block text-[10px] mb-0.5">Hipótese a confirmar:</span>
              {selectedHypothesis ? (
                <span className="font-mono text-blue-700 font-bold">{selectedHypothesis}</span>
              ) : (
                <span className="text-amber-800 text-[11px] italic">
                  Selecione uma das opções acima nas hipóteses de leitura antes de confirmar.
                </span>
              )}
            </div>
          )}

          <div>
            <label className="block text-[11px] text-slate-600 font-medium mb-1">
              Justificativa Obrigatória do Auditor <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              placeholder="Descreva a fundamentação da conferência visual, contexto clínico ou indício documental..."
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded p-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 resize-none font-sans shadow-2xs"
            />
          </div>

          {reviewError && (
            <div
              role="alert"
              className="p-2.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-1.5 shadow-2xs"
            >
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{reviewError}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={submittingDecision || !isFormValid}
            className="w-full py-2 px-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs rounded-md transition flex items-center justify-center gap-1.5 shadow-2xs"
          >
            <Send className="w-3.5 h-3.5" />
            {submittingDecision ? 'Registrando revisão...' : 'Registrar revisão'}
          </button>
        </form>
      </div>

      {/* 4. Histórico de Decisões Persistidas (Acessível sem disputar espaço) */}
      <div className="p-4 flex-1">
        <div
          onClick={() => setHistoryOpen(!historyOpen)}
          className="cursor-pointer flex items-center justify-between mb-3 text-xs font-semibold uppercase tracking-wider text-slate-600 select-none hover:text-slate-900"
        >
          <span className="flex items-center gap-1.5">
            <History className="w-3.5 h-3.5 text-slate-500" />
            Histórico Persistido ({decisions.length})
          </span>
          <span className="text-[10px] text-slate-400">
            {historyOpen ? 'Recolher ▲' : 'Expandir ▼'}
          </span>
        </div>

        {historyOpen && (
          <div>
            {decisions.length === 0 ? (
              <p className="text-xs text-slate-400 italic text-center py-2 font-sans">
                Nenhuma decisão humana registrada ainda.
              </p>
            ) : (
              <div className="space-y-2">
                {decisions.map((dec) => (
                  <div key={dec.id} className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs shadow-2xs">
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-semibold text-slate-900">{dec.action}</span>
                      <span className="text-slate-400 font-mono text-[10px]">
                        {new Date(dec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    {dec.confirmed_value && (
                      <p className="text-[11px] text-slate-700 font-mono mb-1">
                        Valor: <span className="text-blue-900 font-bold">{dec.confirmed_value}</span>
                      </p>
                    )}
                    <p className="text-slate-600 text-[11px] leading-relaxed italic font-sans">
                      "{dec.reason}"
                    </p>
                    <span className="text-[10px] text-slate-400 block mt-1 font-mono">
                      Por: {dec.actor_id}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
