import React, { useState, useEffect } from 'react';
import { GraphResponse, NetworkAnomaly } from '../types';

export const NetworkGraphView: React.FC = () => {
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | null>(null);

  useEffect(() => {
    async function loadGraph() {
      try {
        let response: Response;
        try {
          response = await fetch('/api/graph');
        } catch {
          await new Promise((res) => setTimeout(res, 80));
          response = await fetch('/api/graph');
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const json: GraphResponse = await response.json();
        setData(json);
        if (json.anomalies && json.anomalies.length > 0) {
          setSelectedAnomalyId(json.anomalies[0].id || json.anomalies[0].rule_id);
        }
      } catch (err) {
        console.error('Falha ao buscar dados do grafo:', err);
      } finally {
        setLoading(false);
      }
    }
    void loadGraph();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500 font-mono text-xs">
        Carregando topologia do grafo multi-entidade...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
        Nenhum dado de rede disponível.
      </div>
    );
  }

  // Contagens dinâmicas derivadas diretamente dos nós retornados pela API
  const profCount = data.nodes.filter((n) => n.type === 'profissional').length;
  const clinicCount = data.nodes.filter((n) => n.type === 'clinica').length;
  const procCount = data.nodes.filter((n) => n.type === 'procedimento').length;
  const patientCount = data.nodes.filter((n) => n.type === 'paciente').length;

  // Anomalia ativa selecionada
  const activeAnomaly: NetworkAnomaly | undefined =
    data.anomalies.find((a) => (a.id || a.rule_id) === selectedAnomalyId) || data.anomalies[0];

  // Entidades correlacionadas dinamicamente às guias da anomalia selecionada
  const relatedDocIds = new Set(activeAnomaly?.related_document_ids || []);
  const anomalyLinks = data.links.filter((l) => l.document_id && relatedDocIds.has(l.document_id));
  const relatedNodeIds = new Set<string>();
  anomalyLinks.forEach((l) => {
    relatedNodeIds.add(l.source);
    relatedNodeIds.add(l.target);
  });

  const anomalyNodes = data.nodes.filter((n) => relatedNodeIds.has(n.id) || relatedDocIds.has(n.id));
  const profsInvolved = anomalyNodes.filter((n) => n.type === 'profissional');
  const clinicsInvolved = anomalyNodes.filter((n) => n.type === 'clinica');

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-100">
      {/* Visualização de Resumo da Rede */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-900 text-white tracking-wider">
                NET-01
              </span>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Grafo Relacional Multi-Entidade (NetworkX)
              </h2>
            </div>
            <p className="text-xs text-slate-500">
              Análise cruzada de topologia bipartida entre Beneficiários, Corpo Clínico, Rede Credenciada e Procedimentos TUSS.
            </p>
          </div>

          <div className="flex items-center divide-x divide-slate-200 text-xs font-mono text-slate-700 bg-white rounded-md border border-slate-200 shadow-2xs">
            <div className="px-3.5 py-2">
              <span className="text-slate-400 block text-[9px] font-bold tracking-wider">TOTAL DE GUIAS</span>
              <span className="text-slate-900 font-bold text-sm">{data.total_claims}</span>
            </div>
            <div className="px-3.5 py-2">
              <span className="text-slate-400 block text-[9px] font-bold tracking-wider">NÓS MAPEADOS</span>
              <span className="text-slate-900 font-bold text-sm">{data.nodes.length}</span>
            </div>
            <div className="px-3.5 py-2">
              <span className="text-slate-400 block text-[9px] font-bold tracking-wider">ARESTAS</span>
              <span className="text-slate-900 font-bold text-sm">{data.links.length}</span>
            </div>
            <div className="px-3.5 py-2 bg-rose-50/40">
              <span className="text-rose-600/80 block text-[9px] font-bold tracking-wider">ANOMALIAS</span>
              <span className="text-rose-700 font-bold text-sm">{data.anomalies.length}</span>
            </div>
          </div>
        </div>

        {/* Aviso de Limites Probatórios e Interpretação Pericial */}
        <div className="mb-5 p-3.5 bg-amber-50/80 border border-amber-200/90 rounded-md text-xs text-amber-950 flex items-start gap-3">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-200/70 text-amber-950 border border-amber-300 shrink-0 mt-0.5">
            NOTA METODOLÓGICA
          </span>
          <div className="leading-relaxed">
            <span className="font-semibold block text-amber-950 mb-0.5">
              Limites Probatórios do Grafo de Relações:
            </span>
            <span className="text-amber-900/90">
              Mesmo dia e distância geográfica constituem indício documental de faturamento que exige conferência humana; não comprovam simultaneidade física (podem decorrer de telemedicina legítima ou escala de plantão).
            </span>
          </div>
        </div>

        {/* Grade de Entidades Dinâmicas — Telemetria Institucional (Sem caixas de ícones clichês) */}
        <div className="grid grid-cols-4 gap-3.5 mb-5">
          <div className="p-3.5 bg-white rounded-md border border-slate-200 border-l-4 border-l-slate-800 shadow-2xs flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                ENT-01 // CORPO CLÍNICO
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-600">Profissionais</span>
              <span className="text-base font-bold font-mono text-slate-900">{profCount} Médicos</span>
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-md border border-slate-200 border-l-4 border-l-blue-700 shadow-2xs flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                ENT-02 // CREDENCIADOS
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-600">Clínicas/Hospitais</span>
              <span className="text-base font-bold font-mono text-slate-900">{clinicCount} Unidades</span>
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-md border border-slate-200 border-l-4 border-l-emerald-700 shadow-2xs flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                ENT-03 // TABELA TUSS
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-600">Procedimentos</span>
              <span className="text-base font-bold font-mono text-slate-900">{procCount} Tipos</span>
            </div>
          </div>

          <div className="p-3.5 bg-white rounded-md border border-slate-200 border-l-4 border-l-amber-600 shadow-2xs flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                ENT-04 // CARTEIRA ANS
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-slate-600">Pacientes</span>
              <span className="text-base font-bold font-mono text-slate-900">{patientCount} Indivíduos</span>
            </div>
          </div>
        </div>

        {/* Representação Dinâmica do Subgrafo da Anomalia Selecionada */}
        <div className="bg-white p-6 rounded-md border border-slate-200 min-h-[380px] flex flex-col justify-between shadow-2xs">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                SUBGRAFO::{activeAnomaly?.rule_id || 'NONE'}
              </span>
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Topologia do Cluster Selecionado
              </span>
            </div>
            {activeAnomaly && (
              <span className="text-[11px] font-mono text-rose-800 flex items-center gap-2 bg-rose-50 px-2.5 py-1 rounded border border-rose-200 font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600 shrink-0" />
                {activeAnomaly.severity} — {activeAnomaly.title}
              </span>
            )}
          </div>

          {activeAnomaly ? (
            <div className="py-4">
              {/* Topologia visual conectada com arestas explícitas para monitores largos */}
              <div className="my-4 px-5 py-8 bg-slate-50/80 rounded-md border border-slate-200 flex flex-col lg:flex-row items-center justify-center gap-0">
                {/* Nó Central / Origem: Médico */}
                <div className="w-64 p-4 rounded-md bg-white border-2 border-rose-400 text-left shadow-xs z-10">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-rose-700 font-bold">
                      NODE::ORIGIN // PRESCRITOR
                    </span>
                    <span className="w-2 h-2 rounded-full bg-rose-600" />
                  </div>
                  <div className="text-sm font-bold text-slate-900 font-mono">
                    {((activeAnomaly as any).crm || profsInvolved[0]?.label || 'CRM PROF-DEMO-007').replace(/^CRM\s+CRM\s+/i, 'CRM ')}
                  </div>
                  <div className="text-[11px] font-mono text-rose-800 mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between">
                    <span>Volume Diário:</span>
                    <span className="font-bold">{activeAnomaly.related_document_ids?.length || 6} guias / 24h</span>
                  </div>
                </div>

                {/* Aresta Conectora 1 */}
                <div className="hidden lg:flex flex-col items-center w-36 -mx-1">
                  <span className="text-[10px] font-mono font-bold text-rose-800 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 mb-1">
                    Mesma Data
                  </span>
                  <div className="w-full border-t-2 border-dashed border-rose-400" />
                  <span className="text-[10px] font-mono text-slate-500 mt-1">
                    Faturação Simultânea
                  </span>
                </div>

                {/* Nó Destino 1: Clínica Sorocaba */}
                <div className="w-64 p-4 rounded-md bg-white border border-slate-300 text-left shadow-xs z-10">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
                      NODE::UNIT_A // CREDENCIADO
                    </span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  </div>
                  <div className="text-sm font-bold text-slate-900 font-mono truncate">
                    {clinicsInvolved[0]?.label || 'Clínica CLINICA-DEMO-001'}
                  </div>
                  <div className="text-[11px] font-mono text-slate-600 mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between">
                    <span>Jurisdição:</span>
                    <span className="font-semibold text-slate-900">{clinicsInvolved[0]?.cidade || 'Sorocaba'}</span>
                  </div>
                </div>

                {/* Aresta Conectora 2 (Conflito Geográfico) */}
                <div className="hidden lg:flex flex-col items-center w-40 -mx-1">
                  <span className="text-[10px] font-mono font-bold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-300 mb-1">
                    Conflito Geográfico
                  </span>
                  <div className="w-full border-t-2 border-dashed border-amber-500" />
                  <span className="text-[10px] font-mono text-slate-500 mt-1">
                    Municípios Distintos
                  </span>
                </div>

                {/* Nó Destino 2: Clínica Santos */}
                <div className="w-64 p-4 rounded-md bg-white border border-slate-300 text-left shadow-xs z-10">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
                      NODE::UNIT_B // CREDENCIADO
                    </span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  </div>
                  <div className="text-sm font-bold text-slate-900 font-mono truncate">
                    {clinicsInvolved[1]?.label || 'Clínica CLINICA-DEMO-005'}
                  </div>
                  <div className="text-[11px] font-mono text-slate-600 mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between">
                    <span>Jurisdição:</span>
                    <span className="font-semibold text-slate-900">{clinicsInvolved[1]?.cidade || 'Santos'}</span>
                  </div>
                </div>
              </div>

              {/* Relações Extraídas */}
              <div className="mt-4 p-3.5 bg-slate-50 rounded-md border border-slate-200 text-xs">
                <span className="text-slate-700 font-mono uppercase tracking-wider font-bold text-[10px] block mb-1">
                  PARECER TÉCNICO DO MOTOR DE GRAFOS (AGENTE INVESTIGADOR):
                </span>
                <p className="text-slate-700 leading-relaxed font-sans">
                  {activeAnomaly.explanation}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
              Nenhuma anomalia ativa selecionada.
            </div>
          )}

          <div className="text-[11px] text-slate-500 font-mono flex items-center justify-between border-t border-slate-100 pt-3">
            <span>ENGINE: NetworkX MultiGraph // Subgraph Isomorphism</span>
            <span>Evidências ancoradas em lote sintético auditável</span>
          </div>
        </div>
      </div>

      {/* Painel Lateral de Anomalias de Rede */}
      <div className="w-96 border-l border-slate-200 bg-white p-4 overflow-y-auto shadow-xs">
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-rose-950 text-rose-100">
              ANOM
            </span>
            Anomalias Detectadas
          </h3>
          <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
            {data.anomalies.length} casos
          </span>
        </div>

        {data.anomalies.length === 0 ? (
          <p className="text-xs text-slate-400 italic">Nenhuma anomalia de rede detectada.</p>
        ) : (
          <div className="space-y-3">
            {data.anomalies.map((anom) => {
              const anomKey = anom.id || anom.rule_id;
              const isSelected = (activeAnomaly?.id === anom.id) || selectedAnomalyId === anomKey;
              return (
                <div
                  key={anomKey}
                  onClick={() => setSelectedAnomalyId(anomKey)}
                  className={`p-3.5 rounded-md border transition cursor-pointer shadow-2xs ${
                    isSelected
                      ? 'bg-rose-50/40 border-rose-300 ring-1 ring-rose-200'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-900">{anom.title}</span>
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">
                      {anom.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-3 font-sans">
                    {anom.explanation}
                  </p>

                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200 mb-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block font-bold mb-1.5">
                      Guias Relacionadas ({anom.related_document_ids.length}):
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {anom.related_document_ids.map((id) => (
                        <span
                          key={id}
                          className="text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800 font-medium"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  </div>

                  <p className="text-[10px] text-slate-400 italic">
                    Limitação: {anom.limitations}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
