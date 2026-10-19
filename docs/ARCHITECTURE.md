# ARQUITETURA DO SISTEMA — CRIBUM

**Versão:** 1.0.0 (MVP)  
**Categoria:** Saúde e Tecnologias Assistivas & Auditoria Clínica  
**Arquitetura:** Sistema Multiagente de Visão Computacional, Farmacovigilância LASA, Grafos Relacionais e Cadeia de Custódia Merkle (RFC 6962)

---

## 1. Visão Geral

O **CRIBUM** é uma plataforma clínica e assistiva (mobile e web) de conferência de receitas médicas, segurança de medicação (**LASA** — *Look-Alike, Sound-Alike*) e auditoria pericial documental em saúde (SUS / ANS).

A proposta arquitetural fundamenta-se em quatro princípios:
1. **Incerteza Explícita:** Nunca ocultar ambiguidades caligráficas; apresentar hipóteses concorrentes de leitura (`top-3`) e o grau de incerteza explícito (`CERTAIN`, `AMBIGUOUS`, `INDETERMINATE`).
2. **Evidência Ancorada:** Vincular cada alerta clínico ou documental à região física exata da imagem (coordenadas de *bounding box* normalizadas `0..1`).
3. **Decisão Humana Obrigatória (*Human-in-the-Loop*):** Em casos de ambiguidade caligráfica ou risco LASA crítico, o sistema bloqueia aprovações automáticas e exige validação humana fundamentada.
4. **Privacidade e Imutabilidade (*Privacy-First & LGPD*):** Processamento local sem vazamento de dados sensíveis de pacientes para nuvens públicas de terceiros, aliado à cadeia de custódia criptográfica em Árvore de Merkle (**RFC 6962**).

```text
[ Imagem da Receita / Guia Médica (Câmera Mobile ou Upload Web) ]
           │
           ▼
[ Pipeline de Normalização & Armazenamento Seguro ]
    ├── Validação MIME real, descompressão segura (anti-bomb)
    └── Hash criptográfico SHA-256 (Cadeia de custódia inicial)
           │
           ▼
[ 1. Agente Leitor (backend/agents/leitor.py) ]
    ├── Modo REAL: vLLM (Qwen2-VL) via OpenAI-compatible JSON Schema (sem fallback silencioso)
    ├── Modo DEMO: Fixtures determinísticas gabaritadas (aviso visual transparente)
    └── Extração de Hipóteses 1..3 + Bounding Boxes normalizadas [x_min, y_min, x_max, y_max]
           │
           ▼
[ 2. Agente Farmacêutico (backend/agents/farmaceutico.py) ]
    ├── Motor Farmacológico LASA (distância fonética/visual sobre base ANVISA / ISMP Brasil)
    ├── Correlação Diagnóstica (CID-10 × indicação farmacológica) e cálculo de CCRI (0..100)
    └── Regras Documentais (CRM ausente, unidade ausente, posologia contraditória, duplicidade SHA-256)
           │
           ▼
[ 3. Agente Investigador (backend/agents/investigador.py & graph_engine.py) ]
    └── Motor de Grafos Relacionais (NetworkX) para detecção de anomalias e conluios na rede
           │
           ▼
[ 4. Agente Relator (backend/agents/relator.py) ]
    ├── Cadeia de Custódia Criptográfica em Árvore de Merkle (RFC 6962: prev_chain_hash -> chain_hash)
    └── Emissão do Dossiê Pericial TISS/ANS e persistência isolada por execução (run_id)
```

---

## 2. Componentes e Isolamento Técnico

### 2.1 Backend Multiagente (FastAPI + SQLAlchemy + SQLite)
* **Orquestração de 4 Agentes Autônomos (`backend/agents/`):**
  1. `leitor.py`: Agente de Visão Multimodal (`Qwen2-VL`) com extração estruturada de múltiplas hipóteses e coordenadas espaciais.
  2. `farmaceutico.py`: Agente Farmacológico LASA e de conformidade clínica/regulatória (ANVISA/ISMP, CID-10 e TUSS/ANS).
  3. `investigador.py`: Agente de Grafos Relacionais (`NetworkX`) para detecção de padrões atípicos, faturamentos geograficamente incompatíveis no mesmo dia e conluios.
  4. `relator.py`: Agente de Auditoria Privacy-First (LGPD), cálculo de risco composto (CCRI) e selagem criptográfica em Árvore de Merkle (RFC 6962).
* **Isolamento Estrito por Execução (`run_id`):**
  * Cada execução pericial gera evidências com escopo próprio (`ev-{original_id}-{run_id[:8]}`), impedindo colisão ou sobrescrita de *bounding boxes* entre diferentes análises.
  * Auto-migração segura na inicialização (`_apply_migrations` via `PRAGMA table_info`) garantindo compatibilidade contínua do banco relacional.
* **Vínculo Estrito no Parecer Humano (HITL):**
  * O endpoint `POST /api/documents/{doc_id}/decisions` valida estritamente o trio `(run_id, field_id, confirmed_value)`, rejeitando com `HTTP 400 INVALID_HYPOTHESIS` qualquer tentativa de confirmar valores fora das hipóteses auditadas.
* **Política Zero Fallback Silencioso:**
  * No modo `REAL`, caso o servidor de inferência local/remoto (`vLLM`) esteja indisponível, o backend falha explicitamente com `HTTP 503 INFERENCE_UNAVAILABLE`, garantindo integridade probatória.

### 2.2 Frontend Responsivo & Estação Pericial (React 18 + TypeScript + Tailwind CSS)
* **Design Clínico de Alto Contraste:** Paleta neutra e semafórica acessível (âmbar `#D97706` para incerteza caligráfica e carmim `#BE123C` para risco LASA crítico).
* **Visualizador Pericial com Filtros Ópticos:** Overlay SVG interativo com controles de zoom/ajuste, além de filtros ópticos forenses em tempo real (*Contraste Dinâmico*, *Negativo Forense / Negatoscópio* e *Realce de Tinta*).
* **Hierarquia Probatória em 4 Níveis:**
  1. *Alertas de Inconsistência e Segurança LASA* (`CRITICAL`, `HIGH`, `MEDIUM`) com atalho direto para a evidência visual;
  2. *Hipóteses de Leitura do VLM* agrupadas por campo e nível de incerteza;
  3. *Parecer do Auditor Humano (HITL)* com justificativa obrigatória;
  4. *Dossiê Criptográfico & Histórico Retrátil* com verificação da cadeia Merkle RFC 6962.
* **Navegador de Grafo Relacional:** Visualização da topologia de 200 guias (`claims_200.json`) e inspeção de subgrafos suspeitos.

