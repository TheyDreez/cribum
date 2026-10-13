import React, { useState, useEffect } from 'react';
import { Network, AlertOctagon, Building, User, FileText, Activity } from 'lucide-react';
import { GraphResponse, NetworkAnomaly } from '../types';

export const NetworkGraphView: React.FC = () => {
  const [data, setData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAnomalyRule, setSelectedAnomalyRule] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/graph')
      .then((r) => r.json())
      .then((json: GraphResponse) => {
        setData(json);
        setLoading(false);
        if (json.anomalies && json.anomalies.length > 0) {
          setSelectedAnomalyRule(json.anomalies[0].rule_id);
        }
      })
      .catch((err) => {
        console.error('Falha ao buscar dados do grafo:', err);
        setLoading(false);
      });
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
    data.anomalies.find((a) => a.rule_id === selectedAnomalyRule) || data.anomalies[0];

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
    <div className="flex-1 flex overflow-hidden bg-graphite-950">
      {/* Visualização de Resumo da Rede */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Network className="w-5 h-5 text-auditTeal-400" />
              Grafo Relacional Multi-Entidade (NetworkX)
            </h2>
            <p className="text-xs text-slate-400">
              Análise cruzada de conexões entre Pacientes, Médicos, Clínicas e Procedimentos.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-300 bg-graphite-900 px-4 py-2 rounded-lg border border-graphite-800">
            <div>
              <span className="text-slate-500 block text-[10px]">TOTAL DE GUIAS</span>
              <span className="text-white font-bold">{data.total_claims}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">NÓS MAPEADOS</span>
              <span className="text-white font-bold">{data.nodes.length}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">CONEXÕES</span>
              <span className="text-white font-bold">{data.links.length}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">ANOMALIAS</span>
              <span className="text-auditRose-500 font-bold">{data.anomalies.length}</span>
            </div>
          </div>
        </div>

        {/* Grade de Entidades Dinâmicas */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-graphite-900 rounded-xl border border-graphite-800 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-auditTeal-500/10 text-auditTeal-400">
              <User className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block font-mono">Profissionais</span>
              <span className="text-base font-bold text-white">{profCount} Médicos</span>
            </div>
          </div>

          <div className="p-4 bg-graphite-900 rounded-xl border border-graphite-800 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block font-mono">Clínicas/Hospitais</span>
              <span className="text-base font-bold text-white">{clinicCount} Unidades</span>
            </div>
          </div>

          <div className="p-4 bg-graphite-900 rounded-xl border border-graphite-800 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block font-mono">Procedimentos</span>
              <span className="text-base font-bold text-white">{procCount} Tipos</span>
            </div>
          </div>

          <div className="p-4 bg-graphite-900 rounded-xl border border-graphite-800 flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block font-mono">Pacientes</span>
              <span className="text-base font-bold text-white">{patientCount} Indivíduos</span>
            </div>
          </div>
        </div>

        {/* Representação Dinâmica do Subgrafo da Anomalia Selecionada */}
        <div className="bg-graphite-900/60 p-6 rounded-xl border border-graphite-800 min-h-[380px] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Topologia do Cluster Selecionado ({activeAnomaly?.rule_id || 'Nenhuma anomalia'})
            </span>
            {activeAnomaly && (
              <span className="text-xs font-mono text-auditRose-500 flex items-center gap-1.5 bg-auditRose-500/10 px-2.5 py-1 rounded border border-auditRose-500/20">
                <AlertOctagon className="w-3.5 h-3.5" />
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
                    className="text-center p-4 bg-graphite-950 rounded-lg border border-auditRose-500/40 shadow-lg shadow-auditRose-500/5 min-w-[180px]"
                  >
                    <span className="text-[11px] font-mono text-auditRose-400 font-bold block mb-1">
                      {prof.label}
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      Grau de Conexão: {prof.degree}
                    </span>
                    <span className="text-[10px] text-slate-500 mt-1 block">
                      {activeAnomaly.related_document_ids.length} guias na data analisada
                    </span>
                  </div>
                ))}

                {/* Nós de Clínicas Envolvidas */}
                {clinicsInvolved.map((clinic) => (
                  <div
                    key={clinic.id}
                    className="text-center p-4 bg-graphite-950 rounded-lg border border-graphite-700 min-w-[180px]"
                  >
                    <span className="text-[11px] font-mono text-auditTeal-400 font-bold block mb-1">
                      {clinic.label}
                    </span>
                    <span className="text-xs text-slate-300 block">
                      {clinic.cidade ? `Município: ${clinic.cidade}` : 'Local não informado'}
                    </span>
                    <span className="text-[10px] text-slate-500 mt-1 block font-mono">
                      {clinic.id}
                    </span>
                  </div>
                ))}
              </div>

              {/* Relações Extraídas */}
              <div className="mt-4 p-3 bg-graphite-950/80 rounded-lg border border-graphite-800 text-xs">
                <span className="text-slate-400 font-mono text-[11px] block mb-1">
                  Parecer Descritivo do Investigador:
                </span>
                <p className="text-slate-300 leading-relaxed font-sans">
                  {activeAnomaly.explanation}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
              Nenhuma anomalia ativa selecionada.
            </div>
          )}

          <div className="text-[11px] text-slate-500 font-mono flex items-center justify-between border-t border-graphite-800/80 pt-3">
            <span>Motor: NetworkX MultiGraph Anomaly Detection</span>
            <span>Entidades e evidências mapeadas diretamente das guias sintéticas</span>
          </div>
        </div>
      </div>

      {/* Painel Lateral de Anomalias de Rede */}
      <div className="w-96 border-l border-graphite-800 bg-graphite-900/80 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono mb-3 flex items-center gap-2">
          <AlertOctagon className="w-4 h-4 text-auditRose-500" />
          Anomalias Detectadas ({data.anomalies.length})
        </h3>

        {data.anomalies.length === 0 ? (
          <p className="text-xs text-slate-500 italic">Nenhuma anomalia de rede detectada.</p>
        ) : (
          <div className="space-y-3">
            {data.anomalies.map((anom) => (
              <div
                key={anom.rule_id}
                onClick={() => setSelectedAnomalyRule(anom.rule_id)}
                className={`p-3.5 rounded-lg border transition cursor-pointer ${
                  selectedAnomalyRule === anom.rule_id
                    ? 'bg-auditRose-500/10 border-auditRose-500/50'
                    : 'bg-graphite-950 border-graphite-800 hover:border-graphite-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-white">{anom.title}</span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-auditRose-500/20 text-auditRose-400">
                    {anom.severity}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-3">
                  {anom.explanation}
                </p>

                <div className="p-2 bg-graphite-900 rounded border border-graphite-800 mb-2">
                  <span className="text-[10px] text-slate-400 block font-mono mb-1">
                    Guias Relacionadas no Esquema ({anom.related_document_ids.length}):
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {anom.related_document_ids.map((id) => (
                      <span
                        key={id}
                        className="text-[10px] font-mono bg-graphite-950 px-1.5 py-0.5 rounded border border-graphite-800 text-slate-300"
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="text-[10px] text-slate-500 italic">
                  Limitação: {anom.limitations}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
