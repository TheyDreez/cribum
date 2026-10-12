# ARQUITETURA DO SISTEMA — CRIBUM / AUDITRX

**Versão:** 1.0.0 (MVP)  
**Equipe:** Inédito Viável (Sorocaba/SP & colaboradores remotos)  
**Hackathon:** AMD Developer Hackathon: ACT III  
**Trilha:** Health and Wellbeing  

---

## 1. Visão Geral

O **CRIBUM** (nome de trabalho *AuditRx*) é um ambiente de conferência e auditoria pericial documental para guias e prescrições médicas.
A proposta arquitetural fundamenta-se em três princípios:
1. **Incerteza Explícita:** Nunca ocultar ambiguidades de leitura; apresentar hipóteses concorrentes e o nível de confiança heurístico.
2. **Evidência Ancorada:** Vincular cada alerta documental à região física da imagem (bounding box normalizado 0..1).
3. **Decisão Humana Obrigatória (*Human-in-the-Loop*):** O sistema não executa diagnósticos ou rejeições autônomas; funciona estritamente como suporte ao auditor.

```
[ Imagem Médica (Upload) ]
           │
           ▼
[ Pipeline de Normalização & Armazenamento Seguro ]
    ├── Validação MIME real, descompressão segura (anti-bomb)
    └── Hash criptográfico SHA-256 (Cadeia de custódia)
           │
           ▼
[ Camada de Provedores de Inferência ]
    ├── Modo REAL: vLLM (Qwen2-VL) em GPU AMD ROCm (falha explícita se indisponível)
    └── Modo DEMO: Fixtures determinísticas gabaritadas (aviso visual permanente)
           │
           ▼
[ Contratos Tipados (Pydantic V2) ]
    ├── ExtractedFields (Hipóteses 1..3, incerteza: CERTAIN | AMBIGUOUS | INDETERMINATE)
    └── Evidences (Bounding boxes normalizados [x_min, y_min, x_max, y_max])
           │
           ▼
[ Motor de Regras Determinísticas (RulesEngine) ]
    ├── Inconsistências Documentais (CRM ausente, unidade ausente)
    ├── Duplicidade de Guia (Hash SHA-256)
    └── Risco de Troca LASA (Base ISMP Brasil)
           │
           ▼
[ Motor de Análise Relacional (GraphEngine - NetworkX) ]
    └── Detecção de anomalias em rede (ex: faturamento em clínicas distantes no mesmo dia)
           │
           ▼
[ Interface de Auditoria React + SQLite Persistente ]
    └── Registro formal da Decisão Humana fundamentada e Audit Events
```

---

## 2. Componentes

### 2.1 Backend (FastAPI + SQLAlchemy + SQLite)
* **API REST:** Endpoints para upload seguro, disparo de execuções (`runs`), consulta de evidências, submissão de parecer do auditor e topologia do grafo.
* **Persistência Relacional:** SQLite local para o MVP, permitindo persistência de histórico e decisões humanas mesmo após reinicialização do servidor.
* **Isolamento de Inferência:** O backend comunica-se via HTTP com o endpoint vLLM; não importa dependências pesadas de PyTorch/ROCm no mesmo runtime.

### 2.2 Frontend (React + TypeScript + Tailwind CSS)
* **Visualizador Pericial:** Overlay SVG sobre a imagem renderizada destacando bounding boxes coloridas conforme a seleção do alerta.
* **Painel de Hipóteses:** Apresentação lado a lado das alternativas de leitura com indicadores de incerteza em âmbar.
* **Formulário de Decisão Humana:** Seleção de hipótese confirmada e justificativa textual obrigatória.
* **Navegador de Grafo:** Visualização da rede de 200 guias e inspeção de clusters suspeitos.
