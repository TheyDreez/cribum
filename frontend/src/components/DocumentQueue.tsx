import React, { useState } from 'react';
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
      return { label: 'Aprovado', style: 'text-emerald-700 font-semibold' };
    case 'REJECTED':
      return { label: 'Rejeitado', style: 'text-rose-700 font-semibold' };
    case 'IN_REVIEW':
      return {
        label: 'Em Revisão',
        style:
          'text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 font-medium text-[10px]',
      };
    case 'ESCALATED':
      return { label: 'Forense', style: 'text-purple-700 font-semibold' };
    case 'CLARIFICATION_REQUESTED':
      return { label: 'Esclarecimento', style: 'text-blue-700 font-semibold' };
    case 'PENDING':
    default:
      return { label: 'Pendente', style: 'text-slate-500' };
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
    <aside
      id="document-queue"
      className="w-full min-w-0 border-r border-slate-200 bg-white flex flex-col h-full shadow-2xs select-none"
    >
      {/* Cabeçalho Técnico da Fila */}
      <div className="p-3.5 border-b border-slate-200 bg-slate-50/80">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200/80 text-slate-700">
              Q-01
            </span>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Fila de Auditoria ({documents.length})
            </h2>
          </div>

          <label className="cursor-pointer flex items-center gap-1.5 px-2.5 py-1 bg-[#0f172a] hover:bg-slate-800 text-white font-medium text-xs rounded transition shadow-2xs">
            <span className="font-mono text-[11px] leading-none">+</span>
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

        {/* Busca rápida */}
        <div className="relative mb-2">
          <span className="font-mono text-[10px] text-slate-400 absolute left-2.5 top-2">
            /
          </span>
          <input
            type="text"
            placeholder="Buscar por caso, nome ou ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded pl-6 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-400 font-sans shadow-2xs"
          />
        </div>

        {/* Filtros de Triagem */}
        <div className="flex items-center gap-1 text-[11px]">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2.5 py-0.5 rounded transition ${
              filter === 'ALL'
                ? 'bg-slate-900 text-white font-medium shadow-2xs'
                : 'text-slate-600 hover:bg-slate-200/60'
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter('PENDING')}
            className={`px-2.5 py-0.5 rounded transition ${
              filter === 'PENDING'
                ? 'bg-slate-900 text-white font-medium shadow-2xs'
                : 'text-slate-600 hover:bg-slate-200/60'
            }`}
          >
            Pendentes
          </button>
          <button
            onClick={() => setFilter('FINDINGS')}
            className={`px-2.5 py-0.5 rounded transition ${
              filter === 'FINDINGS'
                ? 'bg-slate-900 text-white font-medium shadow-2xs'
                : 'text-slate-600 hover:bg-slate-200/60'
            }`}
          >
            Com Alertas
          </button>
        </div>
      </div>

      {/* Lista de Documentos */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 bg-white">
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
                className={`w-full text-left p-3 transition flex flex-col gap-1.5 border-l-[3px] ${
                  isSelected
                    ? 'bg-slate-50 border-slate-900 text-slate-900 shadow-2xs'
                    : 'hover:bg-slate-50/70 border-transparent text-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <span
                      className={`text-xs block truncate ${
                        isSelected ? 'font-bold text-slate-950' : 'font-medium text-slate-900'
                      }`}
                      title={friendlyName}
                    >
                      {friendlyName}
                    </span>
                    {friendlyName !== doc.filename_original && (
                      <span className="font-mono text-[10px] text-slate-400 block truncate mt-0.5">
                        {doc.filename_original}
                      </span>
                    )}
                  </div>

                  {isFailed ? (
                    <span
                      className="flex items-center gap-1.5 text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 shrink-0"
                      title={doc.last_execution_error || 'Falha de processamento nesta execução.'}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-red-600 shrink-0" />
                      Falha
                    </span>
                  ) : doc.findings_count > 0 ? (
                    <span className="flex items-center gap-1.5 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600 shrink-0" />
                      {doc.findings_count} {doc.findings_count === 1 ? 'alerta' : 'alertas'}
                    </span>
                  ) : (
                    <span
                      className="flex items-center gap-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 shrink-0"
                      title="Sem inconsistências de regra detectadas pelo motor determinístico"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0" />
                      Sem inconsistências
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] pt-0.5">
                  <span className="text-slate-400 font-mono text-[10px]">
                    ID: {doc.id.slice(0, 8)}...
                  </span>
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
