import React from 'react';
import { AppConfig, DocumentItem } from '../types';

interface HeaderProps {
  config: AppConfig | null;
  activeTab: 'auditoria' | 'rede';
  onTabChange: (tab: 'auditoria' | 'rede') => void;
  onSeedDemo: () => void;
  loadingSeed: boolean;
  documents?: DocumentItem[];
}

/**
 * Emblema arquitetural exclusivo do CRIBUM (do latim Cribrum = Crivo / Matriz de Inspeção Óptica).
 * Substitui ícones genéricos por uma retícula pericial de precisão 3x3 com ponto focal calibrado.
 */
const CribumArchitecturalEmblem: React.FC = () => (
  <div className="w-9 h-9 rounded-md bg-[#0f172a] border border-slate-700 flex items-center justify-center shadow-2xs shrink-0 relative overflow-hidden">
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Grade interna do crivo analítico */}
      <path
        d="M5 9H19M5 15H19M9 5V19M15 5V19"
        stroke="#334155"
        strokeWidth="1.2"
      />
      {/* Moldura de demarcação óptica */}
      <rect
        x="6.5"
        y="6.5"
        width="11"
        height="11"
        rx="1"
        stroke="#94A3B8"
        strokeWidth="1.25"
      />
      {/* Cantoneiras de ancoragem pericial (Bounding Box Reticle) */}
      <path
        d="M3.5 7.5V3.5H7.5M16.5 3.5H20.5V7.5M20.5 16.5V20.5H16.5M7.5 20.5H3.5V16.5"
        stroke="#38BDF8"
        strokeWidth="1.5"
        strokeLinecap="square"
      />
      {/* Nó central de decisão humana verificada */}
      <circle cx="12" cy="12" r="2.2" fill="#10B981" />
    </svg>
  </div>
);

export const Header: React.FC<HeaderProps> = ({
  config,
  activeTab,
  onTabChange,
  onSeedDemo,
  loadingSeed,
  documents = [],
}) => {
  const isDemo = config?.execution_mode === 'DEMO';
  const totalDocs = documents.length;
  const criticalOrAmbiguousDocs = documents.filter((d) => d.findings_count > 0).length;
  const reviewedDocs = documents.filter((d) => d.review_status !== 'PENDING').length;
  const hitlProgress = totalDocs > 0 ? Math.round((reviewedDocs / totalDocs) * 100) : 0;

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-2xs print:hidden select-none">
      {/* Faixa Técnica de Governança Operacional (Sem emojis genéricos) */}
      {isDemo && (
        <div
          data-testid="demo-banner"
          className="bg-amber-50/90 border-b border-amber-200/80 px-5 py-1 text-[11px] text-amber-950 flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase px-1.5 py-0.2 bg-amber-200/70 text-amber-950 rounded border border-amber-300">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
              SYS::DEMO
            </span>
            <span className="font-medium">
              {config?.demo_banner_message?.includes('MODO DEMO ATIVO')
                ? config.demo_banner_message
                : `MODO DEMO ATIVO: ${
                    config?.demo_banner_message ||
                    'Resultados de fixtures sintéticas documentadas.'
                  }`}
            </span>
          </div>
          <span className="text-[10px] text-amber-900 font-mono uppercase tracking-wider hidden sm:inline">
            Protocolo: Human-in-the-Loop Obrigatório · RFC 6962
          </span>
        </div>
      )}

      <div className="w-full px-5 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Identidade Institucional */}
        <div className="flex items-center gap-3">
          <CribumArchitecturalEmblem />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-sm tracking-[0.08em] uppercase text-slate-900">
                {config?.app_name || 'CRIBUM'}
              </h1>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-mono font-medium">
                v{config?.version || '1.0.0'}
              </span>
              <span className="hidden md:inline-block text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                // TISS · ANS · ISMP-BR
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium tracking-tight">
              Medical Forensics &amp; Clinical Integrity Suite · Inédito Viável
            </p>
          </div>
        </div>

        {/* Seletores de Módulo Operacional (Com geometria vetorial exclusiva) */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-md border border-slate-200">
          <button
            type="button"
            data-testid="tab-audit"
            onClick={() => onTabChange('auditoria')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-all ${
              activeTab === 'auditoria'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold border border-slate-200/80'
                : 'text-slate-600 hover:text-slate-900 font-medium'
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <rect x="2.5" y="1.5" width="11" height="13" rx="1" stroke="currentColor" strokeWidth="1.4" />
              <path d="M5 5.5H11M5 8H11M5 10.5H8.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="square" />
            </svg>
            Auditoria Individual
          </button>
          <button
            type="button"
            data-testid="tab-graph"
            onClick={() => onTabChange('rede')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-all ${
              activeTab === 'rede'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold border border-slate-200/80'
                : 'text-slate-600 hover:text-slate-900 font-medium'
            }`}
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="3.5" cy="8" r="2" stroke="currentColor" strokeWidth="1.4" />
              <circle cx="12.5" cy="3.5" r="2" stroke="currentColor" strokeWidth="1.4" />
              <circle cx="12.5" cy="12.5" r="2" stroke="currentColor" strokeWidth="1.4" />
              <path d="M5.3 7.1L10.7 4.4M5.3 8.9L10.7 11.6" stroke="currentColor" strokeWidth="1.3" />
            </svg>
            Rede de Guias (Grafo)
          </button>
        </div>

        {/* Telemetria Operacional de Lote (Estilo Terminal Financeiro/Atuarial) */}
        {totalDocs > 0 && (
          <div className="hidden xl:flex items-center divide-x divide-slate-200 bg-slate-50 border border-slate-200 rounded-md px-3 py-1 text-xs">
            <div className="pr-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">Lote:</span>
              <span className="font-mono font-bold text-slate-900" data-testid="metric-total-docs">
                {totalDocs} docs
              </span>
            </div>
            <div className="px-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">Alertas / LASA:</span>
              <span
                className="font-mono font-bold text-red-700 bg-red-50 px-1.5 py-0.5 rounded border border-red-200"
                data-testid="metric-critical-alerts"
              >
                {criticalOrAmbiguousDocs} casos
              </span>
            </div>
            <div className="pl-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">HITL Progress:</span>
              <span
                className="font-mono font-bold text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200"
                data-testid="metric-hitl-progress"
              >
                {hitlProgress}% ({reviewedDocs}/{totalDocs})
              </span>
            </div>
          </div>
        )}

        {/* Controles de Catálogo & Status de Silício */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            data-testid="seed-demo-btn"
            onClick={onSeedDemo}
            disabled={loadingSeed}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-md border border-slate-300 transition shadow-2xs disabled:opacity-50"
            title="Carregar os 20 casos sintéticos gabaritados na fila"
          >
            <span
              className={`w-2 h-2 rounded-xs border border-slate-500 ${
                loadingSeed ? 'animate-spin bg-slate-400' : 'bg-slate-700'
              }`}
            />
            Carregar 20 Casos Sintéticos
          </button>

          <div
            data-testid="execution-mode-badge"
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-md border border-slate-200 font-mono text-xs text-slate-800 font-semibold"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                config?.execution_mode === 'REAL' ? 'bg-red-600' : 'bg-emerald-600'
              }`}
            />
            <span>
              {config?.execution_mode === 'REAL' ? 'AMD ROCm (vLLM)' : 'Fixture Demo Engine'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
