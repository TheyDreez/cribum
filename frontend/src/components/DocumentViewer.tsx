import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, MoveHorizontal, MoveVertical, RotateCcw } from 'lucide-react';
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
  onSelectEvidence,
}) => {
  const [zoom, setZoom] = useState(1.0);
  const [viewMode, setViewMode] = useState<'custom' | 'fit-width' | 'fit-height'>('custom');
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [scrollPos, setScrollPos] = useState({ left: 0, top: 0 });

  const activeEvidenceIds = selectedFinding?.evidence_ids || [];

  // Controles de visualização
  const handleFitWidth = () => {
    setViewMode('fit-width');
    setZoom(1.0);
  };

  const handleFitHeight = () => {
    setViewMode('fit-height');
    setZoom(1.0);
  };

  const handleResetZoom = () => {
    setViewMode('custom');
    setZoom(1.0);
  };

  const handleZoomIn = () => {
    setViewMode('custom');
    setZoom((z) => Math.min(3.0, Number((z + 0.2).toFixed(1))));
  };

  const handleZoomOut = () => {
    setViewMode('custom');
    setZoom((z) => Math.max(0.4, Number((z - 0.2).toFixed(1))));
  };

  // Suporte a pan/arraste quando ampliado
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    setIsPanning(true);
    setStartPos({ x: e.clientX, y: e.clientY });
    setScrollPos({
      left: containerRef.current.scrollLeft,
      top: containerRef.current.scrollTop,
    });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isPanning || !containerRef.current) return;
    const dx = e.clientX - startPos.x;
    const dy = e.clientY - startPos.y;
    containerRef.current.scrollLeft = scrollPos.left - dx;
    containerRef.current.scrollTop = scrollPos.top - dy;
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  return (
    <div className="flex-1 min-w-0 flex flex-col bg-graphite-950 overflow-hidden relative">
      {/* Top Toolbar */}
      <div className="h-10 px-4 border-b border-graphite-800 bg-graphite-900/80 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2 text-xs text-slate-300 font-mono truncate mr-2">
          <span className="shrink-0 font-medium">Visualizador Pericial:</span>
          {selectedFinding ? (
            <span className="px-2 py-0.5 rounded bg-auditRose-500/15 text-auditRose-500 border border-auditRose-500/20 text-[11px] truncate">
              Alerta Ativo: {selectedFinding.title}
            </span>
          ) : (
            <span className="text-slate-500 text-[11px]">Nenhum alerta selecionado</span>
          )}
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-1">
          {/* Ajustar à Largura */}
          <button
            onClick={handleFitWidth}
            className={`px-2 py-1 rounded text-xs font-mono flex items-center gap-1 transition ${
              viewMode === 'fit-width'
                ? 'bg-auditTeal-500/20 text-auditTeal-400 border border-auditTeal-500/30'
                : 'text-slate-400 hover:text-white hover:bg-graphite-800'
            }`}
            title="Ajustar documento à largura disponível"
          >
            <MoveHorizontal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[11px]">Largura</span>
          </button>

          {/* Ajustar à Altura */}
          <button
            onClick={handleFitHeight}
            className={`px-2 py-1 rounded text-xs font-mono flex items-center gap-1 transition ${
              viewMode === 'fit-height'
                ? 'bg-auditTeal-500/20 text-auditTeal-400 border border-auditTeal-500/30'
                : 'text-slate-400 hover:text-white hover:bg-graphite-800'
            }`}
            title="Ajustar documento à altura disponível"
          >
            <MoveVertical className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[11px]">Altura</span>
          </button>

          <div className="h-4 w-[1px] bg-graphite-800 mx-1" />

          {/* Zoom Out */}
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Reduzir zoom (-20%)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>

          <span
            onClick={handleResetZoom}
            className="text-[11px] font-mono text-slate-300 w-12 text-center cursor-pointer hover:text-auditTeal-400 transition"
            title="Clique para redefinir para 100%"
          >
            {Math.round(zoom * 100)}%
          </span>

          {/* Zoom In */}
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Aumentar zoom (+20%)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          {/* 100% Reset */}
          <button
            onClick={handleResetZoom}
            className="p-1 rounded hover:bg-graphite-800 text-slate-400 hover:text-white transition"
            title="Redefinir visualização original (100%)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area com suporte a Pan e Rolagem fluida */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`flex-1 overflow-auto p-6 flex items-center justify-center bg-graphite-950/90 select-none ${
          isPanning ? 'cursor-grabbing' : zoom > 1.0 ? 'cursor-grab' : 'cursor-default'
        }`}
      >
        <div
          className={`relative shadow-2xl transition-transform duration-100 ease-out origin-center border border-graphite-800 rounded-sm overflow-hidden ${
            viewMode === 'fit-width'
              ? 'w-full max-w-[950px]'
              : viewMode === 'fit-height'
              ? 'max-h-[calc(100vh-140px)] w-auto'
              : 'w-auto'
          }`}
          style={{
            transform: viewMode === 'custom' && zoom !== 1.0 ? `scale(${zoom})` : undefined,
          }}
        >
          {/* Imagem Original da Guia */}
          <img
            src={`/api/documents/${documentId}/image`}
            alt="Guia Médica Original"
            className={`block pointer-events-none ${
              viewMode === 'fit-width'
                ? 'w-full h-auto'
                : viewMode === 'fit-height'
                ? 'max-h-[calc(100vh-150px)] w-auto'
                : 'max-w-[760px] h-auto'
            }`}
            crossOrigin="anonymous"
          />

          {/* Camada SVG de Bounding Boxes */}
          <svg className="absolute inset-0 w-full h-full pointer-events-auto">
            {evidences.map((ev) => {
              if (!ev.bbox || ev.localization_status === 'UNLOCALIZED' || ev.localization_status === 'INVALID_GEOMETRY') {
                return null;
              }

              const isHighlighted = activeEvidenceIds.some(
                (id) => ev.id === id || ev.id.startsWith(id) || id.startsWith(ev.id)
              );

              const left = `${ev.bbox.x_min * 100}%`;
              const top = `${ev.bbox.y_min * 100}%`;
              const width = `${(ev.bbox.x_max - ev.bbox.x_min) * 100}%`;
              const height = `${(ev.bbox.y_max - ev.bbox.y_min) * 100}%`;

              return (
                <g
                  key={ev.id}
                  className="transition-all duration-200"
                  onClick={() => onSelectEvidence && onSelectEvidence(ev.id)}
                >
                  {/* Retângulo de destaque */}
                  <rect
                    x={left}
                    y={top}
                    width={width}
                    height={height}
                    fill={isHighlighted ? 'rgba(244, 63, 94, 0.25)' : 'rgba(20, 184, 166, 0.08)'}
                    stroke={isHighlighted ? '#f43f5e' : '#14b8a6'}
                    strokeWidth={isHighlighted ? '2.5' : '1.5'}
                    strokeDasharray={isHighlighted ? 'none' : '4 2'}
                    className="cursor-pointer transition-all"
                  />

                  {/* Tag explicativa da localização pericial */}
                  {isHighlighted && (
                    <g transform={`translate(${parseFloat(left) * 7.6 || 0}, ${Math.max(0, (parseFloat(top) * 7.6 || 0) - 20)})`}>
                      <rect
                        x={0}
                        y={0}
                        width="150"
                        height="18"
                        rx="3"
                        fill="#0f172a"
                        stroke="#f43f5e"
                        strokeWidth="1"
                      />
                      <text
                        x="5"
                        y="12"
                        fill="#fda4af"
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        {ev.localization_status}
                      </text>
                    </g>
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
