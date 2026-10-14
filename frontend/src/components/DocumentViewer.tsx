import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, MoveHorizontal, Maximize2, RotateCcw, Sliders } from 'lucide-react';
import { Evidence, Finding } from '../types';

export type ForensicOpticalPreset = 'NONE' | 'HIGH_CONTRAST' | 'INVERT' | 'INK_ENHANCE';

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
  const [imageSize, setImageSize] = useState({ width: 800, height: 1050 });

  const [isPanning, setIsPanning] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [scrollPos, setScrollPos] = useState({ left: 0, top: 0 });

  // DIFERENCIAL 1: Filtros Ópticos Forenses
  const [opticalPreset, setOpticalPreset] = useState<ForensicOpticalPreset>('NONE');
  const [customContrast, setCustomContrast] = useState<number>(100);
  const [customBrightness, setCustomBrightness] = useState<number>(100);
  const [showOpticalSliders, setShowOpticalSliders] = useState<boolean>(false);

  const activeEvidenceIds = selectedFinding?.evidence_ids || [];

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
  const naturalWidth = imageSize.width > 50 ? imageSize.width : 800;
  const naturalHeight = imageSize.height > 50 ? imageSize.height : 1050;

  const availableWidth = Math.max(100, viewportSize.width - 32);
  const availableHeight = Math.max(100, viewportSize.height - 32);

  const fitWidthScale = availableWidth / naturalWidth;
  const fitHeightScale = availableHeight / naturalHeight;
  const fitPageScale = Math.min(fitWidthScale, fitHeightScale);

  let effectiveScale = zoom;
  if (viewMode === 'fit-width') {
    effectiveScale = fitWidthScale;
  } else if (viewMode === 'fit-page') {
    effectiveScale = fitPageScale;
  }
  effectiveScale = Math.max(0.1, Math.min(4.0, effectiveScale));

  const renderedWidth = Math.max(50, Math.round(naturalWidth * effectiveScale));
  const renderedHeight = Math.max(50, Math.round(naturalHeight * effectiveScale));

  const applyOpticalPreset = (preset: ForensicOpticalPreset) => {
    setOpticalPreset(preset);
    if (preset === 'NONE') {
      setCustomContrast(100);
      setCustomBrightness(100);
    } else if (preset === 'HIGH_CONTRAST') {
      setCustomContrast(155);
      setCustomBrightness(95);
    } else if (preset === 'INVERT') {
      setCustomContrast(125);
      setCustomBrightness(100);
    } else if (preset === 'INK_ENHANCE') {
      setCustomContrast(210);
      setCustomBrightness(92);
    }
  };

  const computeCssFilter = (): string => {
    const baseContrast = `contrast(${customContrast}%) brightness(${customBrightness}%)`;
    switch (opticalPreset) {
      case 'HIGH_CONTRAST':
        return baseContrast;
      case 'INVERT':
        return `invert(100%) hue-rotate(180deg) ${baseContrast}`;
      case 'INK_ENHANCE':
        return `grayscale(100%) ${baseContrast}`;
      case 'NONE':
      default:
        if (customContrast !== 100 || customBrightness !== 100) {
          return baseContrast;
        }
        return 'none';
    }
  };

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
    const targetTag = (e.target as HTMLElement).tagName.toLowerCase();
    if (['button', 'input', 'select'].includes(targetTag)) return;

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

      {/* DIFERENCIAL 1: Barra de Filtros Ópticos Forenses */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-1.5 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-mono uppercase font-bold text-slate-500 tracking-wider">
            Óptica Forense:
          </span>
          <button
            type="button"
            data-testid="filter-none"
            onClick={() => applyOpticalPreset('NONE')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              opticalPreset === 'NONE'
                ? 'bg-slate-900 text-white shadow-2xs font-semibold'
                : 'text-slate-600 hover:bg-slate-200 border border-slate-200'
            }`}
            title="Imagem original sem filtros ópticos"
          >
            Original
          </button>
          <button
            type="button"
            data-testid="filter-contrast"
            onClick={() => applyOpticalPreset('HIGH_CONTRAST')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              opticalPreset === 'HIGH_CONTRAST'
                ? 'bg-slate-900 text-white shadow-2xs font-semibold'
                : 'text-slate-600 hover:bg-slate-200 border border-slate-200'
            }`}
            title="Realça contraste para caligrafia fraca"
          >
            Contraste Dinâmico
          </button>
          <button
            type="button"
            data-testid="filter-invert"
            onClick={() => applyOpticalPreset('INVERT')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              opticalPreset === 'INVERT'
                ? 'bg-slate-900 text-white shadow-2xs font-semibold'
                : 'text-slate-600 hover:bg-slate-200 border border-slate-200'
            }`}
            title="Inversão espectral (Negativo Fotográfico) para decifrar sobreposição de traços"
          >
            Negativo Forense
          </button>
          <button
            type="button"
            data-testid="filter-ink"
            onClick={() => applyOpticalPreset('INK_ENHANCE')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              opticalPreset === 'INK_ENHANCE'
                ? 'bg-slate-900 text-white shadow-2xs font-semibold'
                : 'text-slate-600 hover:bg-slate-200 border border-slate-200'
            }`}
            title="Isolamento monocromático de alto ganho para separar tinta da grade impressa"
          >
            Realce de Tinta
          </button>
          <button
            type="button"
            data-testid="toggle-optical-sliders"
            onClick={() => setShowOpticalSliders((prev) => !prev)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono border flex items-center gap-1 transition ${
              showOpticalSliders
                ? 'bg-slate-200 border-slate-400 text-slate-900 font-semibold'
                : 'border-slate-200 text-slate-600 hover:bg-slate-200'
            }`}
            title="Ajuste fino de ganho óptico"
          >
            <Sliders className="w-3 h-3 text-slate-500" />
            <span>Ajuste Fino</span>
          </button>
        </div>

        <span className="text-[10px] text-slate-400 font-mono hidden md:inline">
          ViewBox Ancorado: {naturalWidth}×{naturalHeight}px
        </span>
      </div>

      {/* Sub-barra de Sliders de Ajuste Fino Óptico */}
      {showOpticalSliders && (
        <div
          data-testid="optical-sliders-bar"
          className="bg-white border-b border-slate-200 px-4 py-1.5 flex items-center gap-6 text-xs text-slate-700 shadow-2xs"
        >
          <label className="flex items-center gap-2 font-mono text-[11px]">
            <span>Contraste ({customContrast}%):</span>
            <input
              type="range"
              min={70}
              max={250}
              value={customContrast}
              onChange={(e) => setCustomContrast(Number(e.target.value))}
              className="w-28 accent-slate-900"
            />
          </label>
          <label className="flex items-center gap-2 font-mono text-[11px]">
            <span>Brilho ({customBrightness}%):</span>
            <input
              type="range"
              min={60}
              max={140}
              value={customBrightness}
              onChange={(e) => setCustomBrightness(Number(e.target.value))}
              className="w-28 accent-slate-900"
            />
          </label>
          <span className="text-[11px] text-slate-500 ml-auto hidden lg:inline">
            Filtros ópticos acelerados por hardware mantêm a ancoragem precisa das evidências SVG.
          </span>
        </div>
      )}

      {/* Main Canvas Area com suporte a Pan e Rolagem fluida com todas as bordas acessíveis */}
      <div
        ref={containerRef}
        data-testid="document-scroll-container"
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
              draggable={false}
              style={{ filter: computeCssFilter() }}
              onLoad={(event) => {
                const img = event.currentTarget;
                if (img.naturalWidth > 0 && img.naturalHeight > 0) {
                  setImageSize({
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                  });
                }
              }}
            />

            {/* Camada SVG com coordenadas baseadas exclusivamente nas dimensões naturais da imagem */}
            <svg
              viewBox={`0 0 ${naturalWidth} ${naturalHeight}`}
              preserveAspectRatio="none"
              className="absolute inset-0 w-full h-full pointer-events-none"
            >
              {evidences.map((evidence, index) => {
                const box = evidence.bbox;
                if (
                  !box ||
                  evidence.localization_status === 'UNLOCALIZED' ||
                  evidence.localization_status === 'INVALID_GEOMETRY'
                ) {
                  return null;
                }

                const hasExplicitMatch = activeEvidenceIds.some(
                  (id) => evidence.id === id || evidence.id.startsWith(id) || id.startsWith(evidence.id)
                );
                const hasAnyExplicitMatch = evidences.some((ev) =>
                  activeEvidenceIds.some(
                    (id) => ev.id === id || ev.id.startsWith(id) || id.startsWith(ev.id)
                  )
                );

                const highlighted = hasAnyExplicitMatch
                  ? hasExplicitMatch
                  : Boolean(selectedFinding && index === 0);

                const x = box.x_min * naturalWidth;
                const y = box.y_min * naturalHeight;
                const width = (box.x_max - box.x_min) * naturalWidth;
                const height = (box.y_max - box.y_min) * naturalHeight;

                const labelWidth = Math.min(190, naturalWidth);
                const labelHeight = 22;
                const labelX = Math.max(0, Math.min(x, naturalWidth - labelWidth));
                const labelY = Math.max(0, y - labelHeight);

                return (
                  <g key={evidence.id} className="transition-opacity duration-200">
                    {/* Retângulo de demarcação */}
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill={highlighted ? 'rgba(245, 158, 11, 0.22)' : 'rgba(59, 130, 246, 0.08)'}
                      stroke={highlighted ? '#b45309' : '#3b82f6'}
                      strokeWidth={highlighted ? 3.5 : 1.5}
                      rx={3}
                      className="transition-all"
                    />

                    {/* Header da Evidence Box */}
                    {highlighted && (
                      <g>
                        <rect
                          x={labelX}
                          y={labelY}
                          width={labelWidth}
                          height={labelHeight}
                          fill="#b45309"
                          rx={3}
                        />
                        <text
                          x={labelX + 8}
                          y={labelY + 15}
                          fill="#ffffff"
                          fontSize="11"
                          fontWeight="bold"
                          fontFamily="monospace"
                        >
                          INCERTEZA PERICIAL
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
