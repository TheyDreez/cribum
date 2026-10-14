import React, { useState, useEffect } from 'react';
import { Network, AlertOctagon, Building, User, FileText, Activity } from 'lucide-react';
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
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Network className="w-5 h-5 text-slate-700" />
              Grafo Relacional Multi-Entidade (NetworkX)
            </h2>
            <p className="text-xs text-slate-500">
              Análise cruzada de conexões entre Pacientes, Médicos, Clínicas e Procedimentos.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-700 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-2xs">
            <div>
              <span className="text-slate-400 block text-[10px]">TOTAL DE GUIAS</span>
              <span className="text-slate-900 font-bold">{data.total_claims}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">NÓS MAPEADOS</span>
              <span className="text-slate-900 font-bold">{data.nodes.length}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">CONEXÕES</span>
              <span className="text-slate-900 font-bold">{data.links.length}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">ANOMALIAS</span>
              <span className="text-rose-600 font-bold">{data.anomalies.length}</span>
            </div>
          </div>
        </div>

        {/* Aviso de Limites Probatórios e Interpretação Pericial */}
        <div className="mb-6 p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2.5">
          <AlertOctagon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold block text-amber-950 mb-0.5">
              Limites Probatórios do Grafo de Relações:
            </span>
            <span>
              Mesmo dia e distância geográfica constituem indício documental de faturamento que exige conferência humana; não comprovam simultaneidade física (podem decorrer de telemedicina legítima ou escala de plantão).
            </span>
          </div>
        </div>

        {/* Grade de Entidades Dinâmicas */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-white rounded-xl border border-slate-200 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-lg bg-slate-100 text-slate-700">
              <User className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-500 block">Profissionais</span>
              <span className="text-base font-bold text-slate-900">{profCount} Médicos</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-lg bg-blue-50 text-blue-700">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-500 block">Clínicas/Hospitais</span>
              <span className="text-base font-bold text-slate-900">{clinicCount} Unidades</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-lg bg-purple-50 text-purple-700">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-500 block">Procedimentos</span>
              <span className="text-base font-bold text-slate-900">{procCount} Tipos</span>
            </div>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 flex items-center gap-3 shadow-2xs">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-700">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-500 block">Pacientes</span>
              <span className="text-base font-bold text-slate-900">{patientCount} Indivíduos</span>
            </div>
          </div>
        </div>

        {/* Representação Dinâmica do Subgrafo da Anomalia Selecionada */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 min-h-[380px] flex flex-col justify-between shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
              Topologia do Cluster Selecionado ({activeAnomaly?.rule_id || 'Nenhuma anomalia'})
            </span>
            {activeAnomaly && (
              <span className="text-xs font-mono text-rose-700 flex items-center gap-1.5 bg-rose-50 px-2.5 py-1 rounded border border-rose-200 font-semibold">
                <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
                {activeAnomaly.severity} — {activeAnomaly.title}
              </span>
            )}
          </div>

          {activeAnomaly ? (
            <div className="py-6">
              <div className="flex items-center justify-around flex-wrap gap-4 py-4">
                {/* Nós de Profissionais Envolvidos */}
                {profsInvolved.map((prof) => (
                  <div
                    key={prof.id}
                    className="text-center p-4 bg-rose-50/50 rounded-lg border border-rose-200 min-w-[180px] shadow-2xs"
                  >
                    <span className="text-[11px] font-mono text-rose-800 font-bold block mb-1">
                      {prof.label}
                    </span>
                    <span className="text-[10px] text-slate-500 block font-mono">
                      Grau de Conexão: {prof.degree}
                    </span>
                    <span className="text-[10px] text-slate-600 mt-1 block">
                      {activeAnomaly.related_document_ids.length} guias na data analisada
                    </span>
                  </div>
                ))}

                {/* Nós de Clínicas Envolvidas */}
                {clinicsInvolved.map((clinic) => (
                  <div
                    key={clinic.id}
                    className="text-center p-4 bg-slate-50 rounded-lg border border-slate-200 min-w-[180px] shadow-2xs"
                  >
                    <span className="text-[11px] font-mono text-slate-800 font-bold block mb-1">
                      {clinic.label}
                    </span>
                    <span className="text-xs text-slate-600 block">
                      {clinic.cidade ? `Município: ${clinic.cidade}` : 'Local não informado'}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-1 block font-mono">
                      {clinic.id}
                    </span>
                  </div>
                ))}
              </div>

              {/* Relações Extraídas */}
              <div className="mt-4 p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                <span className="text-slate-600 font-semibold text-[11px] block mb-1">
                  Parecer Descritivo do Investigador:
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
            <span>Motor: NetworkX MultiGraph Anomaly Detection</span>
            <span>Entidades e evidências mapeadas diretamente das guias sintéticas</span>
          </div>
        </div>
      </div>

      {/* Painel Lateral de Anomalias de Rede */}
      <div className="w-96 border-l border-slate-200 bg-white p-4 overflow-y-auto shadow-xs">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-1.5">
          <AlertOctagon className="w-4 h-4 text-rose-600" />
          Anomalias Detectadas ({data.anomalies.length})
        </h3>

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
                  className={`p-3.5 rounded-lg border transition cursor-pointer shadow-2xs ${
                    isSelected
                      ? 'bg-rose-50/50 border-rose-300 ring-1 ring-rose-200'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-900">{anom.title}</span>
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
                      {anom.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-3 font-sans">
                    {anom.explanation}
                  </p>

                  <div className="p-2 bg-slate-50 rounded border border-slate-200 mb-2">
                    <span className="text-[10px] text-slate-500 block font-semibold mb-1">
                      Guias Relacionadas no Esquema ({anom.related_document_ids.length}):
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {anom.related_document_ids.map((id) => (
                        <span
                          key={id}
                          className="text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700"
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
