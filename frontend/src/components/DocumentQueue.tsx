import React, { useState } from 'react';
import { FileUp, AlertTriangle, CheckCircle, Clock, Search, XCircle } from 'lucide-react';
import { DocumentItem } from '../types';

interface DocumentQueueProps {
  documents: DocumentItem[];
  selectedDocId: string | null;
  onSelectDoc: (id: string) => void;
  onUpload: (file: File) => void;
  uploading: boolean;
}

export const getFriendlyCaseName = (filename: string): string => {
  const map: Record<string, string> = {
    'caso_01_losartana_lorazepam.jpg': 'Caso 01: Losartana vs Lorazepam (LASA)',
    'caso_02_fluoxetina_flunarizina.jpg': 'Caso 02: Fluoxetina vs Flunarizina (LASA)',
    'caso_03_digoxina_dipirona.jpg': 'Caso 03: Digoxina vs Dipirona (LASA)',
    'caso_04_citalopram_escitalopram.jpg': 'Caso 04: Citalopram vs Escitalopram (LASA)',
    'caso_05_tramadol_trazodona.jpg': 'Caso 05: Tramadol vs Trazodona (LASA)',
    'caso_06_sem_crm.jpg': 'Caso 06: Ausência de CRM do Prescritor',
    'caso_07_sem_unidade.jpg': 'Caso 07: Ausência de Unidade Posológica',
    'caso_08_crm_incompleto.jpg': 'Caso 08: CRM Incompleto / Formato Inválido',
    'caso_09_cid_incompativel.jpg': 'Caso 09: CID Incompatível com Prescrição',
    'caso_10_posologia_contraditoria.jpg': 'Caso 10: Posologia Contraditória',
    'caso_11_duplicidade_declarada.jpg': 'Caso 11: Guia Duplicada (Lote A)',
    'caso_12_duplicidade_declarada.jpg': 'Caso 12: Guia Duplicada (Lote B)',
    'caso_13_duplicidade_declarada.jpg': 'Caso 13: Guia Duplicada (Lote C)',
    'caso_14_duplicidade_declarada.jpg': 'Caso 14: Guia Duplicada (Lote D)',
    'caso_15_duplicidade_declarada.jpg': 'Caso 15: Guia Duplicada (Lote E)',
    'caso_16_controle_limpo.jpg': 'Caso 16: Controle Regular 01',
    'caso_17_controle_limpo.jpg': 'Caso 17: Controle Regular 02',
    'caso_18_controle_limpo.jpg': 'Caso 18: Controle Regular 03',
    'caso_19_controle_limpo.jpg': 'Caso 19: Controle Regular 04',
    'caso_20_controle_limpo.jpg': 'Caso 20: Controle Regular 05',
  };
  return map[filename.toLowerCase()] || filename;
};

const getReviewStatusInfo = (status: string) => {
  switch (status) {
    case 'APPROVED':
      return { label: 'Aprovado', style: 'text-auditTeal-400 font-medium' };
    case 'REJECTED':
      return { label: 'Rejeitado', style: 'text-auditRose-500 font-medium' };
    case 'IN_REVIEW':
      return { label: 'Em Revisão', style: 'text-amber-400 font-medium' };
    case 'ESCALATED':
      return { label: 'Forense', style: 'text-purple-400 font-medium' };
    case 'CLARIFICATION_REQUESTED':
      return { label: 'Esclarecimento', style: 'text-blue-400 font-medium' };
    case 'PENDING':
    default:
      return { label: 'Pendente', style: 'text-slate-400' };
  }
};

export const DocumentQueue: React.FC<DocumentQueueProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  uploading,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'FINDINGS'>('ALL');
  const [search, setSearch] = useState('');

  const filteredDocs = documents.filter((doc) => {
    const friendlyName = getFriendlyCaseName(doc.filename_original);
    const query = search.toLowerCase();
    const matchesSearch =
      friendlyName.toLowerCase().includes(query) ||
      doc.filename_original.toLowerCase().includes(query) ||
      doc.id.toLowerCase().includes(query);

    if (!matchesSearch) return false;
    if (filter === 'PENDING') return doc.review_status === 'PENDING';
    if (filter === 'FINDINGS') return doc.findings_count > 0;
    return true;
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <aside className="w-80 min-w-[280px] max-w-[340px] shrink-0 border-r border-graphite-800 bg-graphite-900/70 flex flex-col h-[calc(100vh-65px)]">
      {/* Header da Fila */}
      <div className="p-4 border-b border-graphite-800">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-auditTeal-400" />
            Fila de Auditoria ({documents.length})
          </h2>

          <label className="cursor-pointer flex items-center gap-1.5 px-2.5 py-1 bg-auditTeal-500 hover:bg-auditTeal-400 text-graphite-950 font-semibold text-xs rounded-md transition shadow-sm">
            <FileUp className="w-3.5 h-3.5" />
            <span>{uploading ? 'Enviando...' : 'Upload'}</span>
            <input
              type="file"
              accept="image/png,image/jpeg"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>

        {/* Busca */}
        <div className="relative mb-2">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Buscar por caso, nome ou ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-graphite-950 border border-graphite-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-auditTeal-500 font-sans"
          />
        </div>

        {/* Filtros rápidos */}
        <div className="flex items-center gap-1 text-[11px]">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2 py-0.5 rounded ${filter === 'ALL' ? 'bg-graphite-800 text-white font-medium' : 'text-slate-400'}`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter('PENDING')}
            className={`px-2 py-0.5 rounded ${filter === 'PENDING' ? 'bg-graphite-800 text-white font-medium' : 'text-slate-400'}`}
          >
            Pendentes
          </button>
          <button
            onClick={() => setFilter('FINDINGS')}
            className={`px-2 py-0.5 rounded ${filter === 'FINDINGS' ? 'bg-graphite-800 text-white font-medium' : 'text-slate-400'}`}
          >
            Com Alertas
          </button>
        </div>
      </div>

      {/* Lista de Documentos */}
      <div className="flex-1 overflow-y-auto divide-y divide-graphite-800/50">
        {filteredDocs.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            Nenhum documento encontrado. Carregue os 20 casos sintéticos no topo.
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const isSelected = doc.id === selectedDocId;
            const friendlyName = getFriendlyCaseName(doc.filename_original);
            const isFailed = doc.last_execution_status === 'FAILED';

            return (
              <button
                key={doc.id}
                onClick={() => onSelectDoc(doc.id)}
                className={`w-full text-left p-3.5 transition flex flex-col gap-1.5 ${
                  isSelected
                    ? 'bg-graphite-800/90 border-l-2 border-auditTeal-400'
                    : 'hover:bg-graphite-850 border-l-2 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <span
                      className="font-medium text-xs text-slate-200 block truncate"
                      title={friendlyName}
                    >
                      {friendlyName}
                    </span>
                    {friendlyName !== doc.filename_original && (
                      <span className="font-mono text-[10px] text-slate-500 block truncate">
                        {doc.filename_original}
                      </span>
                    )}
                  </div>

                  {isFailed ? (
                    <span
                      className="flex items-center gap-1 text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/30 shrink-0"
                      title={doc.last_execution_error || 'Falha de processamento nesta execução.'}
                    >
                      <XCircle className="w-3 h-3" />
                      Falha
                    </span>
                  ) : doc.findings_count > 0 ? (
                    <span className="flex items-center gap-1 text-[11px] font-mono font-medium px-1.5 py-0.5 rounded bg-auditRose-500/15 text-auditRose-500 border border-auditRose-500/20 shrink-0">
                      <AlertTriangle className="w-3 h-3" />
                      {doc.findings_count} {doc.findings_count === 1 ? 'alerta' : 'alertas'}
                    </span>
                  ) : (
                    <span
                      className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-auditTeal-500/10 text-auditTeal-400 border border-auditTeal-500/20 shrink-0"
                      title="Sem inconsistências de regra detectadas pelo motor determinístico"
                    >
                      <CheckCircle className="w-3 h-3" />
                      Sem inconsistências
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono pt-0.5">
                  <span className="text-slate-500">ID: {doc.id.slice(0, 8)}...</span>
                  {(() => {
                    const info = getReviewStatusInfo(doc.review_status);
                    return <span className={info.style}>{info.label}</span>;
                  })()}
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
};
