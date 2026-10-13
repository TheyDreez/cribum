import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, MoveHorizontal, Maximize2, RotateCcw } from 'lucide-react';
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
  const [viewMode, setViewMode] = useState<'custom' | 'fit-width' | 'fit-page'>('fit-width');
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewportSize, setViewportSize] = useState({ width: 800, height: 600 });
  const [imageSize, setImageSize] = useState({ width: 1, height: 1 });
  const [imageReady, setImageReady] = useState(false);

  const [isPanning, setIsPanning] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [scrollPos, setScrollPos] = useState({ left: 0, top: 0 });

  const activeEvidenceIds = selectedFinding?.evidence_ids || [];

  // Reset de dimensões ao alternar documento
  useEffect(() => {
    setImageReady(false);
    setImageSize({ width: 1, height: 1 });
  }, [documentId]);

  // Medição da área disponível com ResizeObserver
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setViewportSize({ width, height });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Fórmulas de escala
  const availableWidth = Math.max(100, viewportSize.width - 32);
  const availableHeight = Math.max(100, viewportSize.height - 32);

  const fitWidthScale = imageSize.width > 1 ? availableWidth / imageSize.width : 1.0;
  const fitHeightScale = imageSize.height > 1 ? availableHeight / imageSize.height : 1.0;
  const fitPageScale = Math.min(fitWidthScale, fitHeightScale);

  let effectiveScale = zoom;
  if (viewMode === 'fit-width') {
    effectiveScale = fitWidthScale;
  } else if (viewMode === 'fit-page') {
    effectiveScale = fitPageScale;
  }
  effectiveScale = Math.max(0.1, Math.min(4.0, effectiveScale));

  const renderedWidth = imageReady ? Math.max(50, Math.round(imageSize.width * effectiveScale)) : 'auto';
  const renderedHeight = imageReady ? Math.max(50, Math.round(imageSize.height * effectiveScale)) : 'auto';

  // Controles de visualização
  const handleFitWidth = () => {
    setViewMode('fit-width');
  };

  const handleFitPage = () => {
    setViewMode('fit-page');
  };

  const handleResetZoom = () => {
    setViewMode('custom');
    setZoom(1.0);
  };

  const handleZoomIn = () => {
    setViewMode('custom');
    setZoom(Math.min(3.0, Number((effectiveScale + 0.2).toFixed(2))));
  };

  const handleZoomOut = () => {
    setViewMode('custom');
    setZoom(Math.max(0.3, Number((effectiveScale - 0.2).toFixed(2))));
  };

  // Suporte a pan com Pointer Events e captura de ponteiro
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0 || !containerRef.current) return;
    setIsPanning(true);
    setStartPos({ x: e.clientX, y: e.clientY });
    setScrollPos({
      left: containerRef.current.scrollLeft,
      top: containerRef.current.scrollTop,
    });
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isPanning || !containerRef.current) return;
    const dx = e.clientX - startPos.x;
    const dy = e.clientY - startPos.y;
    containerRef.current.scrollLeft = scrollPos.left - dx;
    containerRef.current.scrollTop = scrollPos.top - dy;
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isPanning) {
      setIsPanning(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        // Ignora erro se ponteiro já foi liberado
      }
    }
  };

  return (
    <div className="flex-1 min-w-0 flex flex-col bg-slate-100 overflow-hidden relative h-full">
      {/* Top Toolbar */}
      <div className="h-11 px-4 border-b border-slate-200 bg-white flex items-center justify-between z-10 shrink-0 shadow-2xs">
        <div className="flex-1 min-w-0 flex items-center gap-2 text-xs text-slate-700 mr-4">
          <span className="shrink-0 font-semibold text-slate-800">Visualizador Pericial:</span>
          {selectedFinding ? (
            <span
              className="px-2.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-xs truncate font-medium max-w-[500px]"
              title={selectedFinding.title}
            >
              Alerta Ativo: {selectedFinding.title}
            </span>
          ) : (
            <span className="text-slate-400 text-xs">Nenhum alerta selecionado</span>
          )}
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Ajustar à Largura */}
          <button
            type="button"
            onClick={handleFitWidth}
            className={`px-2.5 py-1 rounded text-xs flex items-center gap-1 transition ${
              viewMode === 'fit-width'
                ? 'bg-slate-800 text-white font-medium shadow-2xs'
                : 'text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
            title="Ajustar documento à largura disponível"
          >
            <MoveHorizontal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[11px]">Ajustar à largura</span>
          </button>

          {/* Ajustar à Página */}
          <button
            type="button"
            onClick={handleFitPage}
            className={`px-2.5 py-1 rounded text-xs flex items-center gap-1 transition ${
              viewMode === 'fit-page'
                ? 'bg-slate-800 text-white font-medium shadow-2xs'
                : 'text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
            title="Ajustar documento à página inteira"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[11px]">Ajustar à página</span>
          </button>

          <div className="h-4 w-[1px] bg-slate-200 mx-1" />

          {/* Zoom Out */}
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 transition"
            title="Reduzir zoom (-20%)"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>

          <span
            onClick={handleResetZoom}
            className="text-xs font-mono text-slate-700 w-12 text-center cursor-pointer hover:text-blue-600 font-semibold transition"
            title="Clique para redefinir para 100%"
          >
            {Math.round(effectiveScale * 100)}%
          </span>

          {/* Zoom In */}
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 transition"
            title="Aumentar zoom (+20%)"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          {/* Reset 100% */}
          <button
            type="button"
            onClick={handleResetZoom}
            className="p-1 rounded hover:bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200 transition"
            title="Redefinir visualização original (100%)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area com suporte a Pan e Rolagem fluida com todas as bordas acessíveis */}
      <div
        ref={containerRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        className={`flex-1 overflow-auto bg-slate-200/50 p-4 select-none ${
          isPanning ? 'cursor-grabbing' : effectiveScale > 1.0 ? 'cursor-grab' : 'cursor-default'
        }`}
      >
        <div className="w-max h-max m-auto">
          <div
            style={{
              width: renderedWidth,
              height: renderedHeight,
            }}
            className="relative shadow-md border border-slate-300 rounded bg-white overflow-hidden shrink-0"
          >
            {/* Imagem Original da Guia com dimensões naturais capturadas no onLoad */}
            <img
              key={documentId}
              src={`/api/documents/${encodeURIComponent(documentId)}/image`}
              alt="Guia Médica Original"
              className="block w-full h-full object-contain pointer-events-none"
              crossOrigin="anonymous"
              draggable={false}
              onLoad={(event) => {
                const img = event.currentTarget;
                setImageSize({
                  width: img.naturalWidth || 800,
                  height: img.naturalHeight || 1100,
                });
                setImageReady(true);
              }}
            />

            {/* Camada SVG com coordenadas baseadas exclusivamente nas dimensões naturais da imagem */}
            <svg
              viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
              preserveAspectRatio="none"
              className="absolute inset-0 w-full h-full pointer-events-none"
            >
              {imageReady &&
                evidences.map((evidence) => {
                  const box = evidence.bbox;
                  if (
                    !box ||
                    evidence.localization_status === 'UNLOCALIZED' ||
                    evidence.localization_status === 'INVALID_GEOMETRY'
                  ) {
                    return null;
                  }

                  const highlighted = activeEvidenceIds.includes(evidence.id);

                  const x = box.x_min * imageSize.width;
                  const y = box.y_min * imageSize.height;
                  const width = (box.x_max - box.x_min) * imageSize.width;
                  const height = (box.y_max - box.y_min) * imageSize.height;

                  const labelWidth = Math.min(190, imageSize.width);
                  const labelHeight = 22;
                  const labelX = Math.max(0, Math.min(x, imageSize.width - labelWidth));
                  const labelY = Math.max(0, Math.min(y - labelHeight - 4, imageSize.height - labelHeight));

                  return (
                    <g key={evidence.id} data-evidence-id={evidence.id}>
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={height}
                        fill={highlighted ? 'rgba(217,119,6,0.12)' : 'rgba(37,99,235,0.04)'}
                        stroke={highlighted ? '#b45309' : '#2563eb'}
                        strokeWidth={highlighted ? 2 : 1}
                        vectorEffect="non-scaling-stroke"
                        strokeDasharray={highlighted ? undefined : '4 3'}
                      />

                      {highlighted && (
                        <g transform={`translate(${labelX}, ${labelY})`}>
                          <rect
                            width={labelWidth}
                            height={labelHeight}
                            rx={3}
                            fill="#ffffff"
                            stroke="#b45309"
                            vectorEffect="non-scaling-stroke"
                          />
                          <text
                            x={6}
                            y={15}
                            fontSize={11}
                            fill="#78350f"
                            fontFamily="sans-serif"
                          >
                            Evidência selecionada
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
    </div>
  );
};

export default DocumentViewer;
