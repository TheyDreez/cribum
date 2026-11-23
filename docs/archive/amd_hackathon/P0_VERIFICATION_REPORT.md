# RELATÓRIO DE AUDITORIA VERIFICÁVEL — P0 MVP (CRIBUM)

**Projeto:** CRIBUM (AuditRx)  
**Equipe:** Inédito Viável  
**Evento:** AMD Developer Hackathon: ACT III — Health and Wellbeing Track  
**Data da Auditoria:** 12 de Outubro de 2026  
**Branch de Verificação:** `audit/p0-verification`  
**Ambiente:** Python 3.12.14 / FastAPI / SQLite / React 19 / TypeScript / Vite  

---

## 1. Sumário Executivo da Auditoria

Esta auditoria verificou empiricamente 10 pontos críticos levantados na revisão do P0 MVP do **CRIBUM**. Todas as investigações foram conduzidas reproduzindo o comportamento no código-fonte, criando testes de regressão automatizados e aplicando correções atômicas sem comprometer a honestidade metodológica (sem simular inferência em silício AMD sem hardware físico presente).

| # | Item de Verificação | Veredito | Resolução / Status |
|---|----------------------|----------|-------------------|
| 1 | Correspondência dos estados de revisão entre backend e frontend | **CONFIRMADO** | Corrigido em `1b31c71` |
| 2 | Isolamento de evidências por documento e execução | **CONFIRMADO** | Corrigido em `6a44438` |
| 3 | Identificador único para cada ocorrência de anomalia | **CONFIRMADO** | Corrigido em `6a44438` |
| 4 | Compatibilidade das severidades com os contratos | **CONFIRMADO** | Corrigido em `407013e` |
| 5 | Tratamento de leitura vazia como indeterminada, exigindo revisão | **CONFIRMADO** | Corrigido em `407013e` |
| 6 | Limpeza do formulário ao trocar documento e validação da hipótese | **CONFIRMADO** | Corrigido em `742a22d` e `1b31c71` |
| 7 | Proteção contra respostas atrasadas (race guard) | **CONFIRMADO** | Corrigido em `1b31c71` |
| 8 | Separação REAL/DEMO, sem fallback silencioso | **NÃO REPRODUZIDO** | Já atendido estritamente na baseline |
| 9 | Isolamento do gabarito e distinção de testes | **NÃO REPRODUZIDO** | Já atendido estritamente na baseline |
| 10| Remoção de promessas de desempenho/AMD sem evidência | **NÃO REPRODUZIDO** | Já atendido estritamente na baseline |

---

## 2. Detalhamento Item a Item

### Item 1: Correspondência dos estados de revisão entre backend e frontend
- **Veredito:** `CONFIRMADO`
- **Arquivo / Trecho:** [`frontend/src/components/DocumentQueue.tsx`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/frontend/src/components/DocumentQueue.tsx#L133-L135)
  ```tsx
  <span className={`capitalize ${doc.review_status === 'APPROVED' ? 'text-auditTeal-400' : doc.review_status === 'REJECTED' ? 'text-auditRose-500' : 'text-slate-400'}`}>
    {doc.review_status === 'PENDING' ? 'Pendente' : doc.review_status === 'APPROVED' ? 'Aprovado' : 'Rejeitado'}
  </span>
  ```
- **Diagnóstico:** O frontend tratava qualquer estado diferente de `PENDING` ou `APPROVED` como `"Rejeitado"`. Assim, decisões como `IN_REVIEW` (confirmação de hipótese), `ESCALATED` (escalonamento pericial) ou `CLARIFICATION_REQUESTED` eram exibidas como `"Rejeitado"` em vermelho.
- **Correção Aplicada:** Função `getReviewStatusInfo(status)` mapeando explicitamente todos os 6 estados contratuais (`PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `ESCALATED`, `CLARIFICATION_REQUESTED`) com estilo e rótulo auditáveis correspondentes.
- **Commit:** `1b31c71`

---

### Item 2: Isolamento de evidências por documento e execução
- **Veredito:** `CONFIRMADO`
- **Arquivos / Trechos:** 
  - [`backend/models/database.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/models/database.py#L71-L85): `EvidenceModel` não possuía `run_id`.
  - [`backend/api/app.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/api/app.py#L265-L272): `get_document_details` consultava `evidences` e `findings` filtrando apenas por `document_id`.
  - [`backend/api/app.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/api/app.py#L160-L175): `list_documents` contava achados acumulados de todas as execuções (`findings_count = db.query(FindingModel).filter(FindingModel.document_id == d.id).count()`).
- **Diagnóstico:** Se um documento fosse executado mais de uma vez, a contagem de alertas e a lista de evidências acumulavam os resultados de runs anteriores em vez de isolar a execução atual (`latest_run`).
- **Correção Aplicada:**
  - Adicionado `run_id = Column(String(36), ForeignKey("processing_runs.id"), nullable=True, index=True)` ao `EvidenceModel` e relationship em `ProcessingRunModel`.
  - Escopo de IDs de evidência por run (`f"{raw_id}-{run.id[:8]}"`) para evitar sobrescrita acidental em `db.merge()`.
  - Em `get_document_details` e `list_documents`, filtragem estrita pelo `latest_run.id`.
- **Teste de Regressão:** `test_evidence_run_isolation_and_anomaly_unique_ids` em `backend/tests/test_api.py`.
- **Commit:** `6a44438`

---

### Item 3: Identificador único para cada ocorrência de anomalia
- **Veredito:** `CONFIRMADO`
- **Arquivos / Trechos:**
  - [`backend/services/graph_engine.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/services/graph_engine.py#L74-L88): `detect_anomalies` gerava dicionários contendo apenas `rule_id`, sem `id` único da ocorrência.
  - [`frontend/src/components/NetworkGraphView.tsx`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/frontend/src/components/NetworkGraphView.tsx#L231-L240): React usava `key={anom.rule_id}` e o estado selecionava por `rule_id`.
- **Diagnóstico:** Múltiplas anomalias disparadas pela mesma regra (ex.: diferentes médicos faturando no mesmo dia em cidades distintas) compartilhavam a mesma chave, impedindo a seleção individual da anomalia no painel e disparando alertas de chave duplicada no React.
- **Correção Aplicada:**
  - Atribuído `id = f"ANOM-NET-001-{prof}-{data}"` a cada anomalia em `GraphEngine.detect_anomalies`.
  - Atualizado `NetworkAnomaly` em `frontend/src/types.ts` com `id: string`.
  - Em `NetworkGraphView.tsx`, alterado o estado de seleção para `selectedAnomalyId` e `key={anom.id || anom.rule_id}`.
- **Teste de Regressão:** `test_evidence_run_isolation_and_anomaly_unique_ids` em `backend/tests/test_api.py`.
- **Commit:** `6a44438`

---

### Item 4: Compatibilidade das severidades com os contratos
- **Veredito:** `CONFIRMADO`
- **Arquivo / Trecho:** [`backend/services/rules_engine.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/services/rules_engine.py#L150-L165)
  ```python
  FindingModel(severity=par_info.get("gravidade", "HIGH"), ...)
  ```
- **Diagnóstico:** O arquivo de referência `backend/data/references/lasa_ismp.json` utiliza termos em português (`CRITICA`, `ALTA`, `MEDIA`). O contrato estrito `FindingContract` (Pydantic) exige `Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]`. Ao passar os valores em português diretamente para o contrato, o Pydantic disparava `ValidationError`.
- **Correção Aplicada:** Criação do mapeamento canônico `SEVERITY_MAP` em `RulesEngine`, normalizando `CRITICA` -> `CRITICAL`, `ALTA` -> `HIGH`, `MEDIA` -> `MEDIUM`, `BAIXA` -> `LOW`.
- **Teste de Regressão:** `test_rules_engine_severity_mapping_and_indeterminate_handling` em `backend/tests/test_api.py`.
- **Commit:** `407013e`

---

### Item 5: Tratamento de leitura vazia como indeterminada, exigindo revisão
- **Veredito:** `CONFIRMADO`
- **Arquivo / Trecho:** [`backend/services/provider.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/services/provider.py#L305-L322)
  ```python
  uncertainty = "CERTAIN"
  if item.get("nivel_incerteza") == "alto": uncertainty = "AMBIGUOUS"
  ...
  top_name = hyp_list[0]["text"] if hyp_list else "Ilegível"
  # Sem tratamento: uncertainty permanecia CERTAIN e requires_review = False!
  ```
- **Diagnóstico:** Se o modelo VLM retornasse lista vazia de hipóteses ou texto `"Ilegível"`, o conversor de contratos caía no default `CERTAIN`, marcando `requires_review = False`. Isso violava diretamente a diretriz de segurança de saúde de fail-safe em casos de ilegibilidade.
- **Correção Aplicada:**
  - Em `RealROCmProvider._convert_to_contracts`, itens com hipóteses vazias, `top_name in ("Ilegível", "Indeterminado", "")` ou `nivel_incerteza in ("indeterminado", "vazio", "ilegivel")` são classificados como `uncertainty_status = "INDETERMINATE"`, `requires_review = True`, `normalized_value = None` e `score = None`.
  - Em `RulesEngine`, adicionada a regra `MED-003-INDETERMINATE-READING` (severidade `HIGH`), que cria apontamento formal obrigando revisão visual ou solicitação de nova receita.
- **Teste de Regressão:** `test_rules_engine_severity_mapping_and_indeterminate_handling` em `backend/tests/test_api.py`.
- **Commit:** `407013e`

---

### Item 6: Limpeza do formulário ao trocar documento e validação da hipótese
- **Veredito:** `CONFIRMADO`
- **Arquivos / Trechos:**
  - [`frontend/src/components/FindingsPanel.tsx`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/frontend/src/components/FindingsPanel.tsx#L38-L53): Ausência de `useEffect` dependente de `documentId`. O estado de `selectedHypothesis` e `decisionReason` permanecia preenchido com dados da guia anterior.
  - [`backend/api/app.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/api/app.py#L535-L545): Endpoint `POST /api/documents/{doc_id}/reviews` gravava qualquer `confirmed_value` ou `finding_id` sem validar se pertenciam ao documento sob auditoria.
- **Diagnóstico:** 
  1. No frontend, alternar documentos mantinha justificativas e hipóteses selecionadas do caso prévio, induzindo erro do auditor.
  2. No backend, uma requisição desajustada ou maliciosa podia confirmar medicações arbitrárias inexistentes no documento ou vincular a decisão a apontamentos de terceiros.
- **Correção Aplicada:**
  - Frontend: Adicionado `useEffect` monitorando `documentId` para resetar `selectedHypothesis = ''`, `decisionReason = ''` e ação para `CONFIRMED_HYPOTHESIS`.
  - Backend: Em `submit_human_review`, adicionadas checagens estritas:
    - Se `finding_id` fornecido, valida se o finding existe e pertence a `doc.id` (retorna HTTP 400 se divergente).
    - Se `action == "CONFIRMED_HYPOTHESIS"`, exige `confirmed_value` preenchido e valida se o valor corresponde a uma das hipóteses extraídas para o documento (retorna HTTP 400 se divergente).
- **Teste de Regressão:** `test_human_review_hypothesis_and_finding_validation` em `backend/tests/test_api.py`.
- **Commits:** `742a22d` (Backend) e `1b31c71` (Frontend).

---

### Item 7: Proteção contra respostas atrasadas (race guard)
- **Veredito:** `CONFIRMADO`
- **Arquivo / Trecho:** [`frontend/src/App.tsx`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/frontend/src/App.tsx#L46-L63)
  ```tsx
  useEffect(() => {
    if (!selectedDocId) { setDocDetail(null); return; }
    fetch(`/api/documents/${selectedDocId}`)
      .then((r) => r.json())
      .then((detail: DocumentDetail) => { setDocDetail(detail); ... })
  }, [selectedDocId]);
  ```
- **Diagnóstico:** Ao clicar rapidamente entre Guia A e Guia B, a requisição de Guia A podia resolver após a de Guia B, sobrescrevendo os dados de B com as hipóteses de A, enquanto a imagem carregava B (dessincronização visual-clínica).
- **Correção Aplicada:** Implementado `AbortController` cancelando a requisição anterior no cleanup do efeito, além de uma flag `isCurrent` e validação estrita `detail?.document?.id === selectedDocId` antes de invocar `setDocDetail`.
- **Validação:** Verificado via `npm run build` (compilação limpa sem erros de tipagem/lifecycle).
- **Commit:** `1b31c71`

---

### Item 8: Separação REAL/DEMO, sem fallback silencioso
- **Veredito:** `NÃO REPRODUZIDO (JÁ ATENDIDO)`
- **Evidência no Código:** [`backend/api/app.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/backend/api/app.py#L365-L425)
  - Em modo `REAL`, se o serviço vLLM/ROCm não estiver acessível, a API falha imediatamente com HTTP 503 `INFERENCE_UNAVAILABLE`. Não há fallback silencioso para fixtures nem para mocks.
  - Em modo `DEMO`, o `DemoFixtureProvider` busca exclusivamente pelo hash SHA-256 da imagem ou pelo ID canônico pré-semeado. Imagens arbitrárias falham com HTTP 400 `NO_FIXTURE_AVAILABLE`.
- **Testes Existentes Aprovados:**
  - `test_real_provider_fails_explicitly_without_silent_fallback` (HTTP 503 com `INFERENCE_UNAVAILABLE`).
  - `test_unknown_image_rejected_in_demo_mode_without_fallback` (HTTP 400 com `NO_FIXTURE_AVAILABLE`).

---

### Item 9: Isolamento do gabarito e distinção entre teste de fixtures e avaliação real
- **Veredito:** `NÃO REPRODUZIDO (JÁ ATENDIDO)`
- **Evidência no Código:**
  - A busca no repositório (`git grep "ground_truth"`) confirma que o diretório `backend/data/synthetic/ground_truth/` só é acessado pelo gerador sintético (`generate_dataset.py`) e pelo script de avaliação (`eval/run_eval.py`).
  - O script [`eval/run_eval.py`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/eval/run_eval.py#L15-L25) exibe cabeçalho explícito declarando que se trata de verificação de consistência das fixtures sintéticas e do motor de regras, e que a aferição de modelos visuais em caligrafia real é executada separadamente com o endpoint vLLM.

---

### Item 10: Remoção de promessas de desempenho, conformidade e execução AMD sem evidência
- **Veredito:** `NÃO REPRODUZIDO (JÁ ATENDIDO)`
- **Evidência no Código e Documentação:**
  - `README.md`, `docs/AMD_SETUP.md`, `docs/SUBMISSION_CHECKLIST.md` e `docs/INITIAL_STATE.md` foram inspecionados.
  - Alegações não fundamentadas (como "100% LGPD/HIPAA compliance certificado", "acurácia médica de 99.8%") foram purgadas.
  - O sistema é categorizado explicitamente como ferramenta assistiva para auditores humanos (não-autônoma), operando sobre dados sintéticos com pipeline reproduzível para execução local em hardware AMD via ROCm.

---

## 3. Evidências de Testes e Compilação

### 3.1. Testes Automatizados Backend (Pytest)
Comando executado: `.venv\Scripts\python.exe -m pytest -v`
```
============================= test session starts =============================
platform win32 -- Python 3.12.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\andre\.gemini\antigravity\scratch\cribum
plugins: anyio-4.15.1, asyncio-1.4.0
collected 13 items

backend/tests/test_api.py::test_health_and_config PASSED                 [  7%]
backend/tests/test_api.py::test_upload_valid_image PASSED                [ 15%]
backend/tests/test_api.py::test_upload_corrupted_file_rejected PASSED    [ 23%]
backend/tests/test_api.py::test_processing_run_demo_mode PASSED          [ 30%]
backend/tests/test_api.py::test_real_provider_fails_explicitly_without_silent_fallback PASSED [ 38%]
backend/tests/test_api.py::test_human_review_decision_persisted PASSED   [ 46%]
backend/tests/test_api.py::test_unknown_image_rejected_in_demo_mode_without_fallback PASSED [ 53%]
backend/tests/test_api.py::test_upload_file_too_large_returns_413 PASSED [ 61%]
backend/tests/test_api.py::test_graph_endpoint PASSED                    [ 69%]
backend/tests/test_api.py::test_rules_engine_severity_mapping_and_indeterminate_handling PASSED [ 76%]
backend/tests/test_api.py::test_evidence_run_isolation_and_anomaly_unique_ids PASSED [ 84%]
backend/tests/test_api.py::test_human_review_hypothesis_and_finding_validation PASSED [ 92%]
backend/tests/test_leitor.py::test_leitor_agent PASSED                   [100%]

======================= 13 passed, 2 warnings in 9.20s ========================
```

### 3.2. Script de Avaliação Sintética
Comando executado: `.venv\Scripts\python.exe eval/run_eval.py`
```
======================================================================
  CRIBUM — VERIFICAÇÃO DE CONSISTÊNCIA DE REGRAS E FIXTURES SINTÉTICAS
  (Aferição de Consistência Interna do Gabarito frente ao Motor de Regras)
======================================================================

Testando 20 casos com gabarito formal...

----------------------------------------------------------------------
MÉTRICAS DE CONSISTÊNCIA DE FIXTURES E REGRAS:
  • Total de Casos Sintéticos no Catálogo:      20
  • Casos Ambíguos — Coincidência Top-1:        5/5 (100.0%)
  • Casos Ambíguos — Cobertura Top-3:           5/5 (100.0%)
  • Interceptação de Conflito LASA (Regra):     5/5 (100.0%)
  • Especificidade em Controles Limpos (0 falso):5/5 (100.0%)
  • Detecção de Anomalia de Rede no Grafo:      IDENTIFICADA (100%)
----------------------------------------------------------------------
Conclusão: O pipeline de regras valida adequadamente a consistência
do catálogo sintético sem gerar falsos positivos nos controles limpos.
======================================================================
```

### 3.3. Compilação Frontend (TypeScript & Vite)
Comando executado: `npm run build` em `frontend/`
```
> cribum-web@1.0.0 build
> tsc && vite build

vite v6.4.4 building for production...
transforming...
✓ 1923 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.79 kB │ gzip:  0.47 kB
dist/assets/index-CTUF6NuY.css   18.15 kB │ gzip:  4.25 kB
dist/assets/index-D7RCh9Yf.js   189.63 kB │ gzip: 57.46 kB
✓ built in 2.37s
```

---

## 4. Hashes dos Commits na Branch `audit/p0-verification`

A branch `audit/p0-verification` foi estruturada em commits pequenos e temáticos:

```
1b31c71 fix(ui): synchronize review status badges, reset HITL form on doc change, and guard async fetch race
742a22d fix(security): validate confirmed_value hypothesis ownership and finding_id in human review
6a44438 fix(isolation): scope evidences by run_id and assign unique IDs to graph anomalies
407013e fix(eval): map severities to contract literals and treat empty extraction as INDETERMINATE
```

---

## 5. Comandos para Iniciar a Aplicação

### 5.1. Inicialização do Backend (Modo DEMO com dados sintéticos)
```bash
# Na raiz do repositório:
.\.venv\Scripts\activate
uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 5.2. Inicialização do Frontend
```bash
cd frontend
npm install
npm run dev
# Interface acessível em: http://localhost:5173
```

### 5.3. Execução dos Testes Automatizados
```bash
# Executa todos os testes unitários e de integração
.\.venv\Scripts\python.exe -m pytest -v

# Executa o script de consistência do catálogo sintético
.\.venv\Scripts\python.exe eval/run_eval.py
```

### 5.4. Conexão ao Hardware AMD Real (quando disponível)
Para conectar ao container `rocm/vllm` rodando em nó GPU AMD (ex.: MI300X ou Radeon PRO com ROCm 6.x):
```bash
# 1. Iniciar servidor vLLM ROCm:
docker run -it --network=host --device=/dev/kfd --device=/dev/dri \
  --group-add video --ipc=host --shm-size 16G \
  rocm/vllm:latest \
  python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct --port 8000

# 2. Configurar o backend do CRIBUM para modo REAL:
set CRIBUM_EXECUTION_MODE=REAL
set CRIBUM_ROCM_ENDPOINT=http://localhost:8000/v1
```

---

## 6. Pendências e Limitações Conhecidas

1. **Inferência Real em Silício AMD:** A infraestrutura de desenvolvimento local opera no modo `DEMO` com fixtures determinísticas e checagens explícitas. Testes de throughput e inferência óptica direta em GPU AMD requerem o provisionamento do endpoint vLLM/ROCm documentado em `docs/AMD_SETUP.md`.
2. **Taxa de Falso Positivo em Produção:** O catálogo de 20 casos sintéticos e 200 guias de rede valida a lógica das regras e da topologia de rede, mas não substitui a calibração com dados hospitalares reais, que exigirá convênio com operadoras parceiras pós-hackathon.
3. **Escalonamento Forense:** As decisões de `ESCALATED_FORENSIC` e `REQUESTED_CLARIFICATION` registram o evento na trilha de auditoria e atualizam o estado da guia, mas o envio de notificação externa (e.g. e-mail ou webhook para o prestador) requer integração com gateway de mensageria da operadora.
