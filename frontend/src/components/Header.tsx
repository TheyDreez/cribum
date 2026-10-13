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
    <header className="border-b border-graphite-800 bg-graphite-900 sticky top-0 z-30">
      {/* Top Banner se for Modo DEMO */}
      {isDemo && (
        <div className="bg-auditAmber-500/15 border-b border-auditAmber-500/30 px-4 py-1.5 text-xs text-auditAmber-400 flex items-center justify-between font-mono">
          <span>⚠️ {config.demo_banner_message || 'MODO DEMO ATIVO: Resultados de fixtures sintéticas documentadas.'}</span>
          <span className="text-[11px] opacity-80">AMD ACT III · Health & Wellbeing Track</span>
        </div>
      )}

      <div className="w-full px-6 py-3 flex items-center justify-between">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-auditTeal-500 to-auditTeal-600 flex items-center justify-center text-graphite-950 font-bold shadow-lg shadow-auditTeal-500/10">
            <Shield className="w-5 h-5 text-graphite-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg tracking-tight text-white">
                {config?.app_name || 'CRIBUM'}
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-graphite-800 border border-graphite-700 text-slate-400 font-mono">
                v{config?.version || '1.0.0'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Auditor Pericial de Guias & Prescrições Médicas · Inédito Viável
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-graphite-950 p-1 rounded-lg border border-graphite-800">
          <button
            onClick={() => onTabChange('auditoria')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'auditoria'
                ? 'bg-auditTeal-500 text-graphite-950 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Auditoria Individual
          </button>
          <button
            onClick={() => onTabChange('rede')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'rede'
                ? 'bg-auditTeal-500 text-graphite-950 shadow-sm'
                : 'text-slate-400 hover:text-white'
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
            className="flex items-center gap-1.5 px-3 py-1.5 bg-graphite-800 hover:bg-graphite-700 text-xs font-medium rounded-lg text-slate-200 border border-graphite-700 transition"
            title="Carregar os 20 casos sintéticos gabaritados na fila"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingSeed ? 'animate-spin' : ''}`} />
            Carregar 20 Casos Sintéticos
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-graphite-950 rounded-lg border border-graphite-800 font-mono text-xs">
            <Cpu className="w-3.5 h-3.5 text-auditTeal-400" />
            <span className="text-slate-300">
              {config?.execution_mode === 'REAL' ? 'AMD ROCm (vLLM)' : 'Fixture Demo Engine'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
