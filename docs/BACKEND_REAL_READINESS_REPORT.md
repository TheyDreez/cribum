# CRIBUM — Relatório de Prontidão do Backend Real e Fechamento do Fluxo

**Data:** 13 de Outubro de 2026  
**Branch:** `audit/p0-verification`  
**Documento:** `docs/BACKEND_REAL_READINESS_REPORT.md`  
**Responsável:** Antigravity / Time Inédito Viável  

---

## 1. Resumo Executivo

Nesta etapa, consolidamos o fechamento técnico do **CRIBUM** (sistema pericial de auditoria de guias e prescrições médicas) com foco em confiabilidade probatória, isolamento de dados por execução, testes automatizados de ponta a ponta e transparência total sobre a infraestrutura de hardware.

Nenhum resultado foi inventado. O status de cada subsistema foi verificado empiricamente por suítes de testes automatizados executados na íntegra.

---

## 2. Persistência e Isolamento de Dados

### 2.1. Auto-migração de Esquema para Bancos Legados
- Implementada na inicialização do SQLAlchemy a rotina `_apply_migrations(engine)` em `backend/db/database.py`.
- Verifica via `PRAGMA table_info` a presença da coluna `run_id` nas tabelas `evidences`, `extracted_fields` e `audit_decisions`.
- Caso o banco seja legado (criado antes da inclusão de `run_id`), as colunas são adicionadas via `ALTER TABLE ... ADD COLUMN run_id VARCHAR(36) NULL` sem perda de dados ou necessidade de recriação do arquivo `.db`.
- A aplicação opera de forma idêntica tanto em bancos recém-inicializados quanto em bancos já populados.

### 2.2. Isolamento Estrito por Execução (`run_id`)
- **Evidências Scoped:** Cada evidência gravada recebe um identificador determinístico atrelado ao ID da execução (`ev-{original_id}-{run_id[:8]}`), impedindo que duas execuções do mesmo documento compartilhem ou sobrescrevam bounding boxes.
- **Campos Extraídos e Falha com Falha Limpa:** Se uma execução falha (`FAILED`), os resultados de execuções anteriores não são marcados como novos. O `run_id` ativo da falha tem status `FAILED` e mensagem de erro registrada.
- **Cópias de Documentos:** Duas imagens idênticas enviadas em documentos diferentes geram registros completamente independentes em `documents`, `runs`, `extracted_fields` e `evidences`.

### 2.3. Vínculo Estrito no Parecer Humano (HITL)
- A confirmação pericial (`POST /api/documents/{doc_id}/decisions`) agora exige:
  1. `run_id`: execução pericial à qual a decisão se refere.
  2. `field_id`: identificador do campo específico sendo auditado.
  3. `confirmed_value`: valor que obrigatoriamente deve constar na lista de hipóteses geradas pelo VLM para aquele campo e para aquela execução.
- Tentativas de confirmar valores arbitrários ou hipóteses pertencentes a outros campos são rejeitadas com erro HTTP 400 (`INVALID_HYPOTHESIS`).

---

## 3. Integração com Servidor de Inferência AMD ROCm

### 3.1. Auditoria do Ambiente Local
- **Hardware Local:** Estação de trabalho Windows x86_64, sem driver ROCm ou GPU AMD compatível instalada.
- **Endpoint vLLM:** Não foi fornecida URL ou token de acesso a container ROCm remoto em nuvem.
- **Status Registrado:** **NÃO EXECUTADA EM HARDWARE REAL AMD** (declarada com total transparência no relatório e na telemetria).
- **Remoção de Falsa Telemetria:** A string estática `"AMD ROCm GPU"` foi completamente eliminada da resposta do provider. A telemetria agora informa `"vLLM/ROCm Remote Server"` apenas quando há conexão real confirmada, ou `"Fixture Demo Engine"` no modo de demonstração.

### 3.2. Adaptador e Suíte de Testes de Protocolo (`test_amd_protocol.py`)
- Foi desenvolvido o adaptador `RealROCmProvider` aderente ao protocolo OpenAI-compatible de visão multimodal do vLLM (`/v1/chat/completions` com payload de imagem codificada em base64 e JSON Schema estruturado via `response_format`).
- Implementada suíte de testes com servidor fake em `backend/tests/test_amd_protocol.py` cobrindo:
  1. Extração estruturada válida e parsing de hipóteses/bounding boxes.
  2. Tratamento defensivo de resposta vazia ou JSON truncado (gera campos indeterminados que forçam revisão humana).
  3. Falha explícita quando o endpoint remoto está indisponível (retorna HTTP 503 `INFERENCE_UNAVAILABLE`).
  4. Garantia de que nenhuma requisição em modo REAL sofre fallback silencioso para o modo DEMO.

---

## 4. Testes de Navegador (Playwright E2E)

Foi desenvolvida e executada a suíte automatizada de testes end-to-end em `frontend/tests/e2e.spec.ts`, executando contra o navegador Chromium headless real.

**Resultado da Execução: 12 passed (8.1s)**

| Nº | Cenário Testado | Status | Comportamento Verificado |
|---|---|:---:|---|
| **01** | Selecionar documento e acionar visualização | **PASS** | Carregamento da imagem via API, painel de hipóteses e console pericial ativos. |
| **02** | Clicar em evidência e verificar bounding box SVG | **PASS** | Bounding box SVG destacada com stroke pericial na área do campo. |
| **03** | Selecionar hipótese no radio button | **PASS** | Seleção via clique reflete imediatamente no formulário de parecer. |
| **04** | Trocar de documento e verificar limpeza | **PASS** | O formulário de parecer e hipótese confirmada é completamente resetado ao alternar guias. |
| **05** | Impedir confirmação sem hipótese válida | **PASS** | O botão "Registrar revisão" permanece desabilitado com aviso explicativo. |
| **06** | Confirmar hipótese e verificar persistência | **PASS** | Decisão gravada no SQLite, persistindo no histórico após reload da página. |
| **07** | Badges de status da fila documental | **PASS** | Distinção visual entre casos "Pendente" e casos "Em Revisão". |
| **08** | Proteção contra race condition de rede | **PASS** | Alternância rápida entre 3 documentos sem misturar imagens ou dados. |
| **09** | Coerência estrita entre imagem e achados | **PASS** | Campos e regras de anomalia exibidos pertencem estritamente ao documento selecionado. |
| **10** | Grafo multi-entidade e seleção de anomalias | **PASS** | Cards de anomalia do grafo exibem ocorrências e guias distintas. |
| **11** | Banner de modo DEMO explícito | **PASS** | Banner transparente "MODO DEMO ATIVO" e provedor "Fixture Demo Engine". |
| **12** | Falha REAL sem fallback silencioso | **PASS** | Chamada com `mode_override=REAL` sem servidor AMD retorna HTTP 503 com detalhes explícitos. |

---

## 5. Resumo das Suítes de Testes Automatizados

### Backend (Pytest)
```
collected 20 items
backend/tests/test_amd_protocol.py ....                                  [ 20%]
backend/tests/test_api.py ...............                                [ 95%]
backend/tests/test_leitor.py .                                           [100%]
======================= 20 passed, 2 warnings in 15.18s =======================
```

### Frontend (Typecheck & Build)
```
> tsc && vite build
✓ 1923 modules transformed.
dist/index.html                   0.79 kB
dist/assets/index-BrTo1DdO.css   19.18 kB
dist/assets/index-CeP8GYLs.js   197.06 kB
✓ built in 1.72s
```

### E2E Browser (Playwright)
```
Running 12 tests using 1 worker
  ok  1 Cenário 01: Selecionar documento na fila e acionar visualização pericial (121ms)
  ok  2 Cenário 02: Clicar em alerta/evidência e verificar destaque da bounding box SVG (102ms)
  ok  3 Cenário 03: Selecionar hipótese no radio button e refletir no formulário (100ms)
  ok  4 Cenário 04: Trocar de documento e verificar limpeza rigorosa do formulário HITL (132ms)
  ok  5 Cenário 05: Impedimento de confirmação quando nenhuma hipótese for selecionada (57ms)
  ok  6 Cenário 06: Submeter hipótese confirmada e verificar persistência no banco após reload (322ms)
  ok  7 Cenário 07: Verificar badges de status de revisão na fila documental (5ms)
  ok  8 Cenário 08: Race guard: alternância rápida entre documentos sem misturar imagens e dados (622ms)
  ok  9 Cenário 09: Coerência estrita entre imagem, achados e campos do mesmo documento (165ms)
  ok 10 Cenário 10: Seleção de anomalias no grafo exibe cards e guias distintas (199ms)
  ok 11 Cenário 11: Banner de modo DEMO e ausência de falsas alegações de hardware (6ms)
  ok 12 Cenário 12: Tentativa de inferência REAL sem endpoint falha explicitamente sem fallback (2.2s)
  12 passed (8.1s)
```

---

## 6. Histórico de Commits na Branch `audit/p0-verification`

| Hash | Mensagem do Commit | Escopo |
|---|---|---|
| `6ae18fc` | `docs: add P0 verification report with empirical findings and test results` | Relatório de auditoria empírica de falhas P0 |
| `9e52db8` | `fix(persistence): implement schema auto-migration, run-isolation on failure, and strict field-level HITL binding` | Fechamento de persistência, migrações e HITL |
| `f2764fb` | `test(amd): add vLLM OpenAI-compatible protocol smoke test suite and offline failure validation` | Adaptador AMD, testes de protocolo e failover |
| `a085fc9` | `fix(ui): improve readability, add document zoom/fit controls, and align descriptive audit states` | Ergonomia pericial mínima, zoom/fit e linguagem |
| `b0f9b25` | `test(e2e): add comprehensive Playwright browser test suite covering 12 operational workflows` | Suíte E2E Playwright cobrindo 12 cenários |

---

## 7. Instruções para Executar e Visualizar na Máquina Local

Ambos os serviços já estão configurados e podem ser iniciados pelos comandos:

### 1. Backend (FastAPI / Uvicorn)
```powershell
cd C:\Users\andre\.gemini\antigravity\scratch\cribum
.venv\Scripts\python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```
- Endpoint de saúde: `http://127.0.0.1:8000/health`
- Documentação interativa da API: `http://127.0.0.1:8000/docs`

### 2. Frontend (Vite)
```powershell
cd C:\Users\andre\.gemini\antigravity\scratch\cribum\frontend
npm run preview -- --host 127.0.0.1 --port 5173
```
- Interface Web Pericial: **`http://localhost:5173`** (ou `http://127.0.0.1:5173`)
- O backend e o frontend já estão rodando em background na porta 8000 e 5173 prontos para uso no navegador.
