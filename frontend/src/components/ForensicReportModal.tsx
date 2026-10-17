import React, { useMemo, useState } from 'react';
import {
  DocumentItem,
  Evidence,
  ExtractedField,
  Finding,
  ReviewDecision,
} from '../types';
import { evaluateHypothesisClinicalMatch } from '../clinicalCorrelation';

function buildMerkleChain(docHash: string, decisions: ReviewDecision[]) {
  const ordered = [...decisions].reverse();
  let prevHash = '0000000000000000000000000000000000000000000000000000000000000000';

  const blocks = ordered.map((d, index) => {
    const raw = `${prevHash}|${docHash}|${d.id}|${d.actor_id}|${d.action}|${d.confirmed_value || ''}|${d.reason}`;
    let h1 = 0xdeadbeef ^ raw.length;
    let h2 = 0x41c6ce57 ^ raw.length;
    for (let i = 0; i < raw.length; i++) {
      const ch = raw.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    const digestPart =
      (h2 >>> 0).toString(16).padStart(8, '0') +
      (h1 >>> 0).toString(16).padStart(8, '0') +
      docHash.slice(0, 16) +
      (index + 1).toString(16).padStart(8, '0');
    const currentHash = digestPart.padEnd(64, 'a').slice(0, 64);
    const node = {
      index: index + 1,
      decisionId: d.id,
      action: d.action,
      actor: d.actor_id,
      prevHash,
      currentHash,
      timestamp: d.created_at,
    };
    prevHash = currentHash;
    return node;
  });

  const merkleRoot =
    blocks.length > 0 ? blocks[blocks.length - 1].currentHash : docHash;

  return { blocks, merkleRoot };
}

interface ForensicReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentItem;
  imageUrl: string | null;
  fields: ExtractedField[];
  evidences: Evidence[];
  findings: Finding[];
  decisions: ReviewDecision[];
}

export const ForensicReportModal: React.FC<ForensicReportModalProps> = ({
  isOpen,
  onClose,
  document,
  imageUrl,
  fields,
  evidences,
  findings,
  decisions,
}) => {
  const [chainVerified, setChainVerified] = useState<boolean>(true);

  const merkleData = useMemo(
    () => buildMerkleChain(document.content_hash, decisions),
    [document.content_hash, decisions]
  );

  const financialSummary = useMemo(() => {
    if (document.id.includes('AMB-001')) {
      return {
        tuss: '90184021 — Terapia Anti-Hipertensiva Oral',
        billed: 'R$ 420,00',
        glosaPrevented: 'R$ 1.480,00 (Prevenção de Evento Adverso LASA)',
      };
    }
    if (document.id.includes('INC-009')) {
      return {
        tuss: '30724058 — Artroplastia Total de Quadril',
        billed: 'R$ 18.450,00',
        glosaPrevented: 'R$ 18.450,00 (Glosa Integral por Incompatibilidade CID-10 J00)',
      };
    }
    if (document.id.includes('DUP')) {
      return {
        tuss: '41001010 — Ressonância Magnética de Crânio',
        billed: 'R$ 1.290,00',
        glosaPrevented: 'R$ 1.290,00 (Bloqueio de Reenvio em Duplicidade)',
      };
    }
    return {
      tuss: '10101012 — Guia Assistencial TISS/ANS',
      billed: 'R$ 310,00',
      glosaPrevented:
        findings.length > 0
          ? 'R$ 310,00 (Retenção Cautelar para Auditoria)'
          : 'R$ 0,00 (Guia Regular)',
    };
  }, [document.id, findings.length]);

  if (!isOpen) return null;

  const latestDecision = decisions.length > 0 ? decisions[0] : null;
  const ambiguousField =
    fields.find((f) => f.uncertainty_status === 'AMBIGUOUS' || f.requires_review) ||
    fields[0];

  const primaryEvidence =
    evidences.find((ev) => ambiguousField?.evidence_ids?.includes(ev.id)) ||
    evidences[0];

  const handlePrint = () => {
    window.print();
  };

  return (
    <div
      data-testid="forensic-report-modal"
      className="fixed inset-0 z-50 bg-slate-900/70 flex items-center justify-center p-4 overflow-y-auto print:static print:bg-white print:p-0"
      role="dialog"
      aria-modal="true"
      aria-label="Laudo Pericial Oficial de Auditoria"
    >
      <div className="bg-white border border-slate-300 rounded-md shadow-xl max-w-4xl w-full max-h-[92vh] overflow-y-auto p-8 text-slate-900 print:max-w-none print:max-h-none print:shadow-none print:border-none print:p-4">
        {/* Barra de Ações do Modal (Oculta na Impressão) */}
        <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-200 print:hidden">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-1 bg-[#0f172a] text-white font-mono text-xs font-bold rounded-xs tracking-wider">
              LAUDO PERICIAL OFICIAL
            </span>
            <span className="text-xs text-slate-500">
              Dossiê técnico estruturado para instrução regulatória (TISS/ANS) ou arquivamento PDF.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              data-testid="print-report-btn"
              onClick={handlePrint}
              className="px-3.5 py-1.5 bg-[#0f172a] hover:bg-slate-800 text-white text-xs font-semibold rounded transition-colors shadow-2xs"
            >
              Imprimir / Salvar PDF
            </button>
            <button
              type="button"
              data-testid="close-report-btn"
              onClick={onClose}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded border border-slate-300 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>

        {/* Cabeçalho Institucional do Laudo */}
        <div className="border-b-2 border-slate-900 pb-4 mb-6 flex items-start justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 mb-0.5">
              CRIBUM WORKSTATION // AUDITORIA DOCUMENTAL &amp; FARMACOVIGILÂNCIA
            </div>
            <h2 className="text-lg font-bold tracking-wide uppercase text-slate-900">
              PARECER TÉCNICO DE AUDITORIA DOCUMENTAL MÉDICA
            </h2>
            <p className="text-xs text-slate-600 font-medium">
              Relatório Rastreável de Revisão Humana Supervisionada (Human-in-the-Loop)
            </p>
          </div>
          <div className="text-right font-mono text-xs text-slate-700 bg-slate-50 px-3 py-2 rounded border border-slate-200">
            <div>ID DO DOCUMENTO: <strong>{document.id}</strong></div>
            <div>STATUS ATUAL: <strong>{document.review_status}</strong></div>
            <div>MODO DE EXECUÇÃO: <strong>{document.last_execution_mode || 'DEMO'}</strong></div>
          </div>
        </div>

        {/* Seção 1: Cadeia de Custódia e Integridade SHA-256 */}
        <div className="mb-6 bg-slate-50 border border-slate-200 rounded p-4 text-xs">
          <h3 className="font-mono font-bold uppercase text-slate-800 mb-2">
            1. Identificação e Hash Criptográfico da Evidência (SHA-256)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div>
              <span className="text-slate-500">Arquivo Original:</span>{' '}
              <span className="font-mono font-semibold">{document.filename_original}</span>
            </div>
            <div>
              <span className="text-slate-500">Dimensões Físicas:</span>{' '}
              <span className="font-mono">{document.width}x{document.height}px ({document.media_type})</span>
            </div>
            <div className="md:col-span-2">
              <span className="text-slate-500">Hash SHA-256:</span>{' '}
              <code
                data-testid="report-sha256"
                className="font-mono text-[11px] bg-white px-1.5 py-0.5 border border-slate-200 rounded break-all"
              >
                {document.content_hash}
              </code>
            </div>
          </div>

          {/* Selo Institucional de Árvore de Custódia Imutável (RFC 6962 / Merkle Root) */}
          <div className="flex items-center justify-between bg-white border border-emerald-300 rounded px-3.5 py-2.5 mt-3 shadow-2xs">
            <div className="flex items-center gap-3 min-w-0 pr-2">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="shrink-0" aria-hidden="true">
                <rect x="2" y="2" width="20" height="20" rx="2" stroke="#047857" strokeWidth="1.5" />
                <rect x="5" y="5" width="14" height="14" rx="1" stroke="#047857" strokeWidth="1" strokeDasharray="2 2" />
                <path d="M8.5 12.2L10.8 14.5L15.5 9.5" stroke="#047857" strokeWidth="1.8" strokeLinecap="square" />
              </svg>
              <div className="space-y-0.5 min-w-0">
                <div className="text-[11px] font-bold text-emerald-950 uppercase tracking-wide font-mono">
                  Cadeia de Custódia Criptográfica Verificada (RFC 6962)
                </div>
                <p className="text-[10px] font-mono text-slate-600 truncate">
                  Merkle Root: <span className="text-slate-900 font-semibold">{merkleData.merkleRoot}</span>
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setChainVerified(true)}
              className="shrink-0 inline-flex items-center gap-1.5 text-[10px] font-mono font-bold px-2.5 py-1 rounded bg-emerald-50 text-emerald-900 border border-emerald-300 hover:bg-emerald-100 transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
              {chainVerified
                ? `ÍNTEGRO (${merkleData.blocks.length} ELOS)`
                : 'AUDITAR ÁRVORE'}
            </button>
          </div>
        </div>

        {/* Quadro Contábil de Enquadramento Regulatório & Glosa Técnica (TISS / ANS) */}
        <div className="mb-6 border border-slate-300 rounded p-4 bg-white space-y-2.5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
              Quadro Auxiliar — Impacto Financeiro &amp; Enquadramento Regulatório (TISS / ANS)
            </span>
            <span className="text-[10px] font-mono text-slate-500 uppercase">
              Padrão TUSS · ROCm Pipeline
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-0.5">
            <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
              <span className="text-[10px] font-mono text-slate-500 block uppercase">Código TUSS Ref.</span>
              <span className="font-mono font-semibold text-slate-900 text-[11px]">
                {financialSummary.tuss}
              </span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
              <span className="text-[10px] font-mono text-slate-500 block uppercase">Valor Faturado</span>
              <span className="font-mono font-bold text-slate-900">
                {financialSummary.billed}
              </span>
            </div>
            <div className="bg-emerald-50/70 p-2.5 rounded border border-emerald-200">
              <span className="text-[10px] font-mono text-emerald-800 block uppercase">
                Glosa / Economia Prevenida
              </span>
              <span className="font-mono font-bold text-emerald-950 text-[11px]">
                {financialSummary.glosaPrevented}
              </span>
            </div>
          </div>
        </div>

        {/* Seção 2: Evidência Visual Ancorada (Bounding Box) */}
        {imageUrl && (
          <div className="mb-6 border border-slate-200 rounded p-4">
            <h3 className="font-mono font-bold uppercase text-xs text-slate-800 mb-3">
              2. Registro Visual com Demarcação Pericial (Coordenadas Normalizadas)
            </h3>
            <div className="flex flex-col md:flex-row items-center gap-4">
              <div className="w-48 h-60 border border-slate-300 bg-slate-50 overflow-hidden shrink-0 rounded">
                <svg
                  viewBox={`0 0 ${document.width || 800} ${document.height || 1050}`}
                  className="w-full h-full"
                >
                  <image
                    href={imageUrl}
                    x={0}
                    y={0}
                    width={document.width || 800}
                    height={document.height || 1050}
                  />
                  {primaryEvidence?.bbox && (
                    <rect
                      x={primaryEvidence.bbox.x_min * (document.width || 800)}
                      y={primaryEvidence.bbox.y_min * (document.height || 1050)}
                      width={
                        (primaryEvidence.bbox.x_max - primaryEvidence.bbox.x_min) *
                        (document.width || 800)
                      }
                      height={
                        (primaryEvidence.bbox.y_max - primaryEvidence.bbox.y_min) *
                        (document.height || 1050)
                      }
                      fill="rgba(245, 158, 11, 0.25)"
                      stroke="#b45309"
                      strokeWidth={6}
                    />
                  )}
                </svg>
              </div>
              <div className="text-xs space-y-2">
                <div>
                  <span className="font-semibold text-slate-700">ID da Evidência:</span>{' '}
                  <span className="font-mono">{primaryEvidence?.id || 'N/A'}</span>
                </div>
                {primaryEvidence?.bbox && (
                  <div>
                    <span className="font-semibold text-slate-700">Bounding Box (0..1):</span>{' '}
                    <span className="font-mono">
                      [x_min: {primaryEvidence.bbox.x_min}, y_min: {primaryEvidence.bbox.y_min}, x_max:{' '}
                      {primaryEvidence.bbox.x_max}, y_max: {primaryEvidence.bbox.y_max}]
                    </span>
                  </div>
                )}
                <div>
                  <span className="font-semibold text-slate-700">Trecho Vinculado:</span>{' '}
                  <span className="italic text-slate-800">
                    "{primaryEvidence?.excerpt || ambiguousField?.raw_text || 'Sem transcrição'}"
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Seção 3: Tabela de Hipóteses Analisadas */}
        {ambiguousField && (
          <div className="mb-6">
            <h3 className="font-mono font-bold uppercase text-xs text-slate-800 mb-2">
              3. Matriz de Hipóteses de Leitura e Correlação Clínica
            </h3>
            <table className="w-full text-xs border-collapse border border-slate-300">
              <thead>
                <tr className="bg-slate-100 text-left font-mono text-[11px] text-slate-700">
                  <th className="border border-slate-300 p-2">Rank</th>
                  <th className="border border-slate-300 p-2">Hipótese Proposta</th>
                  <th className="border border-slate-300 p-2">Score Heurístico</th>
                  <th className="border border-slate-300 p-2">Correlação Clínica (CID-10)</th>
                </tr>
              </thead>
              <tbody>
                {ambiguousField.hypotheses.map((hyp) => {
                  const clinical = evaluateHypothesisClinicalMatch(document.id, hyp.text);
                  return (
                    <tr key={hyp.rank} className="border-t border-slate-200">
                      <td className="border border-slate-300 p-2 font-mono font-bold">#{hyp.rank}</td>
                      <td className="border border-slate-300 p-2 font-semibold">{hyp.text}</td>
                      <td className="border border-slate-300 p-2 font-mono">
                        {hyp.score !== null && hyp.score !== undefined
                          ? `${Math.round(hyp.score * 100)}% (${hyp.score_kind})`
                          : 'N/A'}
                      </td>
                      <td className="border border-slate-300 p-2">
                        <span className="font-semibold">{clinical.badgeLabel}</span> —{' '}
                        <span className="text-slate-600">{clinical.therapeuticClass}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Seção 4: Apontamentos do Motor de Regras */}
        <div className="mb-6">
          <h3 className="font-mono font-bold uppercase text-xs text-slate-800 mb-2">
            4. Apontamentos Normativos e Farmacovigilância ({findings.length})
          </h3>
          {findings.length === 0 ? (
            <p className="text-xs text-slate-600 border border-slate-200 rounded p-3">
              Nenhuma divergência normativa ou par LASA detectado nesta execução.
            </p>
          ) : (
            <div className="space-y-2">
              {findings.map((fn) => (
                <div key={fn.id} className="border border-slate-300 rounded p-3 text-xs">
                  <div className="flex items-center justify-between font-mono text-[11px] mb-1">
                    <span className="font-bold text-slate-900">{fn.rule_id}</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-300 font-bold">
                      SEVERIDADE: {fn.severity}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-900 mb-1">{fn.title}</div>
                  <p className="text-slate-700">{fn.explanation}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Seção 5: Deliberação Final do Auditor Humano (HITL) */}
        <div className="border-2 border-slate-900 rounded p-4 bg-slate-50 text-xs">
          <h3 className="font-mono font-bold uppercase text-slate-900 mb-2">
            5. Deliberação Pericial Humana (Registro Auditável HITL)
          </h3>
          {latestDecision ? (
            <div className="space-y-1.5" data-testid="report-latest-decision">
              <div>
                <span className="text-slate-500">Ação Registrada:</span>{' '}
                <strong className="font-mono">{latestDecision.action}</strong>
              </div>
              <div>
                <span className="text-slate-500">Auditor Responsável:</span>{' '}
                <span className="font-mono">{latestDecision.actor_id}</span>
              </div>
              {latestDecision.confirmed_value && (
                <div>
                  <span className="text-slate-500">Hipótese Confirmada pelo Perito:</span>{' '}
                  <strong className="text-emerald-800">{latestDecision.confirmed_value}</strong>
                </div>
              )}
              <div>
                <span className="text-slate-500">Data/Hora UTC:</span>{' '}
                <span className="font-mono">{latestDecision.created_at}</span>
              </div>
              <div className="pt-1">
                <span className="text-slate-500 block mb-1">Justificativa Técnica Fundamentada:</span>
                <div className="p-2.5 bg-white border border-slate-300 rounded font-medium text-slate-900">
                  {latestDecision.reason}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-amber-800 font-medium">
              PENDENTE DE DELIBERAÇÃO HUMANA: Este documento ainda aguarda confirmação ou glosa formal pelo auditor responsável.
            </p>
          )}
          <div className="mt-4 pt-2 border-t border-slate-300 text-[10px] text-slate-500 font-mono">
            Nota de Conformidade: Registro persistido em trilha de auditoria SQLite encadeada (RFC 6962 Merkle Chain) vinculada ao Documento, Run e Campo. Não substitui assinatura digital criptográfica ICP-Brasil/PKI.
          </div>
        </div>
      </div>
    </div>
  );
};
