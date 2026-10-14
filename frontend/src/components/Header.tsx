import React from 'react';
import { Cpu, Network, RefreshCw, FileText } from 'lucide-react';
import { AppConfig, DocumentItem } from '../types';

interface HeaderProps {
  config: AppConfig | null;
  activeTab: 'auditoria' | 'rede';
  onTabChange: (tab: 'auditoria' | 'rede') => void;
  onSeedDemo: () => void;
  loadingSeed: boolean;
  documents?: DocumentItem[];
}

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
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs print:hidden select-none">
      {/* Top Banner discreto para Modo DEMO */}
      {isDemo && (
        <div
          data-testid="demo-banner"
          className="bg-amber-50 border-b border-amber-200/80 px-4 py-1 text-xs text-amber-900 flex items-center justify-between"
        >
          <span className="font-medium">
            ⚠️ {config?.demo_banner_message?.includes('MODO DEMO ATIVO') ? config.demo_banner_message : `MODO DEMO ATIVO: ${config?.demo_banner_message || 'Resultados de fixtures sintéticas documentadas.'}`}
          </span>
          <span className="text-[11px] text-amber-800 font-mono uppercase tracking-wider hidden sm:inline">
            Governança: Human-in-the-Loop Obrigatório
          </span>
        </div>
      )}

      <div className="w-full px-5 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#0f172a] flex items-center justify-center text-white shadow-xs font-mono font-bold text-sm tracking-tighter text-emerald-400">
            CR
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base tracking-wider uppercase text-slate-900">
                {config?.app_name || 'CRIBUM'}
              </h1>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-mono">
                v{config?.version || '1.0.0'}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Medical Forensics &amp; Integrity Suite · Inédito Viável
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            type="button"
            data-testid="tab-audit"
            onClick={() => onTabChange('auditoria')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'auditoria'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Auditoria Individual
          </button>
          <button
            type="button"
            data-testid="tab-graph"
            onClick={() => onTabChange('rede')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'rede'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            Rede de Guias (Grafo)
          </button>
        </div>

        {/* Mini-Painel Pericial em Tempo Real (Bloomberg Health Style) */}
        {totalDocs > 0 && (
          <div className="hidden xl:flex items-center divide-x divide-slate-200 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1 text-xs">
            <div className="pr-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">Lote:</span>
              <span className="font-mono font-bold text-slate-900" data-testid="metric-total-docs">
                {totalDocs} docs
              </span>
            </div>
            <div className="px-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">Alertas / LASA:</span>
              <span
                className="font-mono font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded border border-red-200"
                data-testid="metric-critical-alerts"
              >
                {criticalOrAmbiguousDocs} casos
              </span>
            </div>
            <div className="pl-3 flex items-center gap-1.5">
              <span className="text-slate-400 uppercase text-[10px] font-mono">HITL Progress:</span>
              <span
                className="font-mono font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200"
                data-testid="metric-hitl-progress"
              >
                {hitlProgress}% ({reviewedDocs}/{totalDocs})
              </span>
            </div>
          </div>
        )}

        {/* Hardware & Actions */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            data-testid="seed-demo-btn"
            onClick={onSeedDemo}
            disabled={loadingSeed}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-lg border border-slate-300 transition shadow-2xs disabled:opacity-50"
            title="Carregar os 20 casos sintéticos gabaritados na fila"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingSeed ? 'animate-spin text-slate-400' : 'text-slate-500'}`} />
            Carregar 20 Casos Sintéticos
          </button>

          <div
            data-testid="execution-mode-badge"
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg border border-slate-200 font-mono text-xs text-slate-700 font-semibold"
          >
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <span>
              {config?.execution_mode === 'REAL' ? 'AMD ROCm (vLLM)' : 'Fixture Demo Engine'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
