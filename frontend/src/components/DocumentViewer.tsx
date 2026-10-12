import React, { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { Evidence, Finding } from '../types';

interface DocumentViewerProps {
  documentId: string;
  evidences: Evidence[];
  selectedFinding: Finding | null;
  onSelectEvidence?: (evidenceId: string) => void;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  evidences,
  selectedFinding,
}) => {
  const [zoom, setZoom] = useState(1.0);

  const activeEvidenceIds = selectedFinding?.evidence_ids || [];

  return (
    <div className="flex-1 flex flex-col bg-graphite-950 overflow-hidden relative">
      {/* Top Toolbar */}
      <div className="h-10 px-4 border-b border-graphite-800 bg-graphite-900/80 flex items-center justify-between z-10">
        <div className="flex items-center gap-2 text-xs text-slate-300 font-mono">
          <span>Visualizador de Evidências Periciais</span>
          {selectedFinding && (
            <span className="px-2 py-0.5 rounded bg-auditRose-500/15 text-auditRose-500 border border-auditRose-500/20 text-[11px]">
              Alerta Ativo: {selectedFinding.title}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.15))}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Reduzir zoom"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-[11px] font-mono text-slate-400 w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.15))}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Aumentar zoom"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(1.0)}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Ajustar à tela"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 overflow-auto p-6 flex items-center justify-center bg-graphite-950/90">
        <div
          className="relative shadow-2xl transition-transform duration-100 ease-out origin-center border border-graphite-800 rounded-sm overflow-hidden"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Imagem Original da Guia */}
          <img
            src={`/api/documents/${documentId}/image`}
            alt="Guia Médica Original"
            className="max-w-[700px] h-auto block select-none pointer-events-none"
            crossOrigin="anonymous"
          />

          {/* Camada SVG de Bounding Boxes */}
          <svg className="absolute inset-0 w-full h-full pointer-events-auto">
            {evidences.map((ev) => {
              if (!ev.bbox || ev.localization_status === 'UNLOCALIZED') return null;

              const isHighlighted = activeEvidenceIds.includes(ev.id);

              const left = `${ev.bbox.x_min * 100}%`;
              const top = `${ev.bbox.y_min * 100}%`;
              const width = `${(ev.bbox.x_max - ev.bbox.x_min) * 100}%`;
              const height = `${(ev.bbox.y_max - ev.bbox.y_min) * 100}%`;

              return (
                <g key={ev.id} className="transition-all duration-200">
                  {/* Retângulo de destaque */}
                  <rect
                    x={left}
                    y={top}
                    width={width}
                    height={height}
                    fill={isHighlighted ? 'rgba(244, 63, 94, 0.22)' : 'rgba(20, 184, 166, 0.08)'}
                    stroke={isHighlighted ? '#f43f5e' : '#14b8a6'}
                    strokeWidth={isHighlighted ? '3' : '1.5'}
                    strokeDasharray={isHighlighted ? 'none' : '4 2'}
                    className="cursor-pointer transition-all"
                  />
                  {/* Tag indicadora */}
                  {isHighlighted && (
                    <text
                      x={left}
                      y={`calc(${top} - 6px)`}
                      fill="#f43f5e"
                      fontSize="11"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      [EVIDÊNCIA AUDITADA]
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
};
