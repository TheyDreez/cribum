import React from 'react';
import { Shield, Cpu, Network, RefreshCw, FileText } from 'lucide-react';
import { AppConfig } from '../types';

interface HeaderProps {
  config: AppConfig | null;
  activeTab: 'auditoria' | 'rede';
  onTabChange: (tab: 'auditoria' | 'rede') => void;
  onSeedDemo: () => void;
  loadingSeed: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  config,
  activeTab,
  onTabChange,
  onSeedDemo,
  loadingSeed,
}) => {
  const isDemo = config?.execution_mode === 'DEMO';

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      {/* Top Banner discreto para Modo DEMO */}
      {isDemo && (
        <div className="bg-amber-50 border-b border-amber-200/80 px-4 py-1 text-xs text-amber-900 flex items-center justify-between">
          <span className="font-medium">
            ⚠️ {config?.demo_banner_message?.includes('MODO DEMO ATIVO') ? config.demo_banner_message : `MODO DEMO ATIVO: ${config?.demo_banner_message || 'Resultados de fixtures sintéticas documentadas.'}`}
          </span>
          <span className="text-[11px] text-amber-800">Ambiente de Demonstração e Validação</span>
        </div>
      )}

      <div className="w-full px-6 py-2.5 flex items-center justify-between">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-xs">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base tracking-tight text-slate-900">
                {config?.app_name || 'CRIBUM'}
              </h1>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-mono">
                v{config?.version || '1.0.0'}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Auditor Pericial de Guias & Prescrições Médicas · Inédito Viável
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
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

        {/* Hardware & Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onSeedDemo}
            disabled={loadingSeed}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium rounded-lg border border-slate-300 transition shadow-xs disabled:opacity-50"
            title="Carregar os 20 casos sintéticos gabaritados na fila"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingSeed ? 'animate-spin text-slate-400' : 'text-slate-500'}`} />
            Carregar 20 Casos Sintéticos
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg border border-slate-200 font-mono text-xs text-slate-700">
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
