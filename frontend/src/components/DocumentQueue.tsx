import React, { useState } from 'react';
import { FileUp, AlertTriangle, CheckCircle, Clock, Search } from 'lucide-react';
import { DocumentItem } from '../types';

interface DocumentQueueProps {
  documents: DocumentItem[];
  selectedDocId: string | null;
  onSelectDoc: (id: string) => void;
  onUpload: (file: File) => void;
  uploading: boolean;
}

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
    const matchesSearch = doc.filename_original.toLowerCase().includes(search.toLowerCase()) || doc.id.includes(search);
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
    <aside className="w-80 border-r border-graphite-800 bg-graphite-900/70 flex flex-col h-[calc(100vh-65px)]">
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
            placeholder="Buscar por caso ou ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-graphite-950 border border-graphite-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-auditTeal-500 font-mono"
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
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-slate-200 truncate max-w-[170px]" title={doc.filename_original}>
                    {doc.filename_original}
                  </span>
                  {doc.findings_count > 0 ? (
                    <span className="flex items-center gap-1 text-[11px] font-mono font-medium px-1.5 py-0.5 rounded bg-auditRose-500/15 text-auditRose-500 border border-auditRose-500/20">
                      <AlertTriangle className="w-3 h-3" />
                      {doc.findings_count} {doc.findings_count === 1 ? 'alerta' : 'alertas'}
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[11px] font-mono px-1.5 py-0.5 rounded bg-auditTeal-500/10 text-auditTeal-400 border border-auditTeal-500/20">
                      <CheckCircle className="w-3 h-3" />
                      Limpo
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>ID: {doc.id.slice(0, 8)}...</span>
                  <span className={`capitalize ${doc.review_status === 'APPROVED' ? 'text-auditTeal-400' : doc.review_status === 'REJECTED' ? 'text-auditRose-500' : 'text-slate-400'}`}>
                    {doc.review_status === 'PENDING' ? 'Pendente' : doc.review_status === 'APPROVED' ? 'Aprovado' : 'Rejeitado'}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
};
