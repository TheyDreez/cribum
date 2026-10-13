# CRIBUM — Relatório de Integridade da Revisão e Confiabilidade do Redesign

**Data:** 13 de Outubro de 2026  
**Branch:** `fix/redesign-integrity` (a partir de `redesign/audit-experience`)  
**Documento:** `docs/REDESIGN_INTEGRITY_REPORT.md`  
**Time:** Inédito Viável (Health & Wellbeing Track — AMD Developer Hackathon: ACT III)  

---

## 1. Resumo Executivo

O presente relatório consolida a implementação das correções diretas de integridade funcional, rigor probatório e isolamento de estado na aplicação **CRIBUM**. 

A estética sênior de estação de trabalho documental clínica (fundo em cinza cirúrgico suave `#F8FAFC`, tipografia Inter, cartões brancos sem glow/neon e realce em âmbar `#B45309`) foi integralmente preservada, ao mesmo tempo em que foram sanadas todas as fragilidades de concorrência, dimensionamento geométrico de evidências e correspondência de dados entre frontend e backend.

Nenhuma alegação de funcionalidade ou teste foi computada sem execução empírica demonstrada neste host.

---

## 2. Detalhamento das Implementações Realizadas

### 2.1. Isolamento Estrito do Documento Ativo (`App.tsx`)
* **Problema anterior:** A seleção do documento na fila disparava a atualização do ID antes do término da requisição de detalhes (`docDetail`), abrindo brecha para renderizar imagens do documento B com achados ou evidências residuais do documento A.
* **Solução implementada:**
  1. Criação do wrapper derivado:
     ```tsx
     const activeDetail = docDetail?.document.id === selectedDocId ? docDetail : null;
     ```
  2. Rastreamento da versão de requisição via `detailRequestVersion.current` e referência síncrona `selectedDocIdRef.current`.
  3. AbortController cancelando requisições obsoletas e descartando respostas cujo ID não corresponda exatamente ao selecionado.
  4. Wrapper observável no JSX com atributo pericial:
     ```tsx
     <section data-testid="document-workspace" data-document-id={activeDetail.document.id}>
     ```
  5. Se `activeDetail` for nulo durante o carregamento ou erro, nenhum painel renderiza dados incorretos ou imagem de outro documento.

### 2.2. Integridade da Submissão e Parecer Humano (HITL)
* **Problema anterior:** Falha de rede ou validação HTTP 400 limpava prematuramente o texto digitado pelo auditor, e o envio retornava `void`, impossibilitando o controle reativo de limpeza.
* **Solução implementada:**
  1. Tipagem unificada compartilhada `ReviewSubmission`:
     ```tsx
     export interface ReviewSubmission {
       action: string;
       confirmed_value?: string;
       field_id?: string;
       run_id?: string;
       reason: string;
       finding_id?: string;
     }
     ```
  2. Parser estruturado de erros `extractApiError(payload, fallback)` tratando strings, objetos e arrays de validação FastAPI.
  3. `handleSubmitDecision` agora retorna `Promise<boolean>`. O formulário (`FindingsPanel.tsx`) apenas limpa o campo `decisionReason` quando `saved === true`.
  4. Em caso de HTTP 400 ou 500, a justificativa digitada é **100% preservada**, e um alerta com `role="alert"` informa o motivo do erro.
  5. Validação mínima de 3 caracteres úteis (`decisionReason.trim().length >= 3`), alinhada ao backend.
  6. Ações em nível de guia (`APPROVED_CLAIM`, `REJECTED_CLAIM`, etc.) não enviam `confirmed_value` residual de hipóteses.

### 2.3. Coordenadas SVG Baseadas em Dimensões Naturais da Imagem
* **Problema anterior:** O SVG utilizava porcentagens no `<rect>` enquanto a etiqueta pericial multiplicava coordenadas por `7.6` presumindo 760px de largura fixa, desalinhando a caixa do texto explicativo.
* **Solução implementada:**
  1. Eliminação definitiva do fator multiplicador `7.6`.
  2. Captura das dimensões intrínsecas da imagem (`naturalWidth` e `naturalHeight`) no evento `onLoad`.
  3. `viewBox="0 0 naturalWidth naturalHeight"` unificado tanto para o retângulo quanto para o rótulo de texto explicativo.
  4. Matching estrito de evidência por ID idêntico (`activeEvidenceIds.includes(evidence.id)`), sem correspondência permissiva por prefixo.
  5. Cores ajustadas para a paleta clínica documental: âmbar `#B45309` com preenchimento sutil `rgba(217, 119, 6, 0.12)` para evidências em revisão.

### 2.4. Zoom Real com Dimensões Renderizadas e Pan com Captura de Ponteiro
* **Problema anterior:** O zoom utilizava puramente CSS `transform: scale()`, impedindo que barras de rolagem nativas concedessem acesso às 4 bordas do documento ampliado.
* **Solução implementada:**
  1. Medição contínua da viewport útil via `ResizeObserver`.
  2. Cálculo dinâmico das escalas:
     - `fitWidthScale = availableWidth / naturalWidth`
     - `fitHeightScale = availableHeight / naturalHeight`
     - `fitPageScale = min(fitWidthScale, fitHeightScale)`
  3. Aplicação de largura e altura em pixels reais (`renderedWidth`, `renderedHeight`) no invólucro do documento.
  4. Área de rolagem configurada com `w-max h-max m-auto`, garantindo centralização quando menor e acesso integral a todas as 4 bordas quando ampliado (ex: 200%).
  5. Indicador numérico exibindo a escala efetiva real (ex: `76%`, `100%`, `150%`).
  6. Pan via `Pointer Events` com `setPointerCapture` e `releasePointerCapture`.

### 2.5. Painéis Recolhíveis Reais
* **Problema anterior:** A interface possuía colunas com larguras fixas que não podiam ser recolhidas de fato.
* **Solução implementada:**
  1. Estados independentes `queueOpen` e `reviewOpen` no `App.tsx`.
  2. Botões acessíveis sempre visíveis na barra superior: *"Ocultar fila"* / *"Mostrar fila"* e *"Ocultar revisão"* / *"Mostrar revisão"*.
  3. Conformidade de acessibilidade com atributos `aria-expanded` e `aria-controls="document-queue"` / `aria-controls="review-panel"`.
  4. Layout em grid responsivo:
     ```tsx
     const workspaceColumns = [
       queueOpen ? 'clamp(260px, 19vw, 340px)' : '0px',
       'minmax(0, 1fr)',
     ].join(' ');
     ```
  5. Painéis ocultados via controle de exibição (`display: none` / zero width) sem desmontagem no React, **preservando qualquer texto digitado na justificativa ao recolher e reabrir**.

### 2.6. Backend: Validação Exata de Hipótese e Pertencimento de Execução
* **Problema anterior:** Em `submit_human_review`, a expressão `target_val == v or target_val in v or v in target_val` permitia que o auditor confirmasse pedaços incompletos de hipóteses (ex: apenas `"Losartana"` em vez de `"Losartana 50mg"`) ou strings infladas com texto extra.
* **Solução implementada:**
  1. Normalização Unicode canônica conservadora via `unicodedata`:
     ```python
     def normalize_review_value(value: str) -> str:
         normalized = unicodedata.normalize("NFKC", value)
         return " ".join(normalized.split()).casefold()
     ```
  2. Validação por pertinência exata de conjunto (`target_value in valid_values`).
  3. Não inclusão de `raw_text` ou `normalized_value` como hipóteses confirmáveis se não constarem no rol gerado pelo modelo.
  4. Validação estrita de posse de `run_id`: se o auditor informar um `run_id`, ele obrigatoriamente deve pertencer àquele documento em **todas** as ações (não apenas em confirmação de hipótese).
  5. Validação de `finding_id`: pertence ao documento e ao `run_id` correspondente.
  6. Validação de justificativa humana com pelo menos 3 caracteres úteis após `.strip()`.
  7. Resolução da execução mais recente por `order_by(ProcessingRunModel.started_at.desc(), ProcessingRunModel.id.desc())` explícito, sem indexação frágil `runs[-1]`.
  8. Decisões de execuções anteriores não mascaram o status de um novo processamento.

### 2.7. Segurança Padrão no Playwright
* **Problema anterior:** A configuração do Playwright continha flags inseguras desnecessárias (`--disable-web-security`, `--no-sandbox`, etc.).
* **Solução implementada:**
  1. Remoção de todas as flags de desativação de segurança do `launchOptions` padrão.
  2. Execução sobre navegador padrão íntegro.
  3. Isolamento de `--no-sandbox` em variável opt-in documentada (`PLAYWRIGHT_INSECURE_SANDBOX=true`) caso contêineres Docker CI sem usuário não-root exijam.
  4. Configuração de rastreabilidade de falhas:
     - `trace: 'retain-on-failure'`
     - `screenshot: 'only-on-failure'`
     - `video: 'retain-on-failure'`

---

## 3. Resultados dos Testes Automatizados Executados

### 3.1. Testes de Unidade e Integração Backend (Pytest)
Comando executado: `.\.venv\Scripts\python.exe -m pytest`
```
collected 22 items

backend\tests\test_amd_protocol.py ....                                  [ 18%]
backend\tests\test_api.py ................                               [ 90%]
backend\tests\test_leitor.py ..                                          [100%]

======================= 22 passed, 2 warnings in 10.15s =======================
```
*Cobertura inclui:*
- Validação de hipótese exata aceita com casefold NFKC.
- Rejeição de substring incompleta (HTTP 400).
- Rejeição de superstring inflada (HTTP 400).
- Rejeição de injeção de hipótese cruzada entre campos distintos (HTTP 400).
- Rejeição de `run_id` alienígena não pertencente ao documento (HTTP 400).
- Rejeição de `finding_id` falso ou pertencente a outra execução (HTTP 400).
- Rejeição de justificativa com menos de 3 caracteres úteis (HTTP 400).
- Isolamento de execução falha sem mascaramento por execuções antigas.
- Auto-migração retrocompatível de esquema em bancos legados.
- Teste de protocolo vLLM/ROCm e falha explícita offline sem fallback.

### 3.2. Compilação e Verificação Estática Frontend (TypeScript + Vite)
Comando executado: `npm run build`
```
> tsc && vite build

vite v6.4.4 building for production...
transforming...
✓ 1923 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.79 kB │ gzip:  0.45 kB
dist/assets/index-Dh8I39Ix.css   20.11 kB │ gzip:  4.40 kB
dist/assets/index-Dik-pIRp.js   205.04 kB │ gzip: 61.36 kB
✓ built in 2.36s
```
*Zero erros de tipo TypeScript ou compilação.*

### 3.3. Testes End-to-End de Navegador (Playwright)
Comando executado: `npx playwright test` (Chromium padrão, sem desativação de segurança)
```
Running 14 tests using 1 worker

  ok  1 [chromium] › Cenário 01: Selecionar documento na fila e verificar document-workspace (78ms)
  ok  2 [chromium] › Cenário 02: Clicar em alerta/evidência e verificar destaque da bounding box SVG (136ms)
  ok  3 [chromium] › Cenário 03: Selecionar hipótese no radio button e refletir no formulário (167ms)
  ok  4 [chromium] › Cenário 04: Trocar de documento e verificar limpeza rigorosa do formulário HITL (192ms)
  ok  5 [chromium] › Cenário 05: Impedimento de confirmação quando nenhuma hipótese for selecionada (132ms)
  ok  6 [chromium] › Cenário 06: Submeter hipótese confirmada e verificar persistência no banco após reload (438ms)
  ok  7 [chromium] › Cenário 07: Badges de status de revisão na fila documental (56ms)
  ok  8 [chromium] › Cenário 08: Não mistura A com B quando A responde atrasado (intercepção controlada) (299ms)
  ok  9 [chromium] › Cenário 09: Erros HTTP 400 e 500 exibem alerta e preservam a justificativa digitada (254ms)
  ok 10 [chromium] › Cenário 10: Justificativa com menos de 3 caracteres não habilita envio (122ms)
  ok 11 [chromium] › Cenário 11: Painéis retráteis preservam estado e atualizam aria-expanded (258ms)
  ok 12 [chromium] › Cenário 12: Controles de zoom pericial (largura, página, manual e reset) (187ms)
  ok 13 [chromium] › Cenário 13: Rede de Guias e seleção de anomalias relacionais (325ms)
  ok 14 [chromium] › Cenário 14: Inferência REAL sem infraestrutura falha com 503 INFERENCE_UNAVAILABLE (2.3s)

  14 passed (6.3s)
```

---

## 4. Evidências Visuais e Viewports Capturadas

Foram gerados e persistidos screenshots reais da aplicação em operação em [`docs/screenshots/integrity/`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/docs/screenshots/integrity/):

1. **Notebook (1366×768):** [`docs/screenshots/integrity/notebook_1366x768.png`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/docs/screenshots/integrity/notebook_1366x768.png)  
   *Comprova que em telas menores as colunas são redimensionadas com proporção harmônica e o documento preserva área visualizável.*
2. **Desktop Padrão (1920×1080):** [`docs/screenshots/integrity/desktop_1920x1080.png`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/docs/screenshots/integrity/desktop_1920x1080.png)  
   *Estação de trabalho com fila documental à esquerda, visualizador de documento ao centro com bounding boxes âmbar periciais e painel HITL à direita.*
3. **Monitor Amplo / Ultrawide (2560×1440):** [`docs/screenshots/integrity/ultrawide_2560x1440.png`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/docs/screenshots/integrity/ultrawide_2560x1440.png)  
   *Comprova que o layout usa limites e proporções coerentes (`clamp`), sem esticar elementos de texto arbitrariamente ou degradar a legibilidade.*
4. **Painéis Recolhidos (1920×1080):** [`docs/screenshots/integrity/collapsed_panels_1920x1080.png`](file:///C:/Users/andre/.gemini/antigravity/scratch/cribum/docs/screenshots/integrity/collapsed_panels_1920x1080.png)  
   *Demonstra o recolhimento total da fila documental e do painel de revisão, maximizando a área de inspeção do documento médico.*

---

## 5. Declaração Transparente de Testes e Recursos Não Executados

Em cumprimento ao rigor ético e técnico exigido:

1. **Inferência Física em GPU AMD:** Registrada oficialmente como **NÃO EXECUTADA** nesta máquina de desenvolvimento por indisponibilidade de driver ROCm e acelerador físico AMD no host Windows local. O protocolo vLLM foi validado via servidor de teste estruturado (`test_amd_protocol.py`).
2. **Telemetria de VRAM Remota:** Não é coletada por não haver acesso direto ao subsistema `rocm-smi` da máquina remota de inferência; a telemetria reporta exclusivamente tempo de processamento em milissegundos e contagem de tokens do payload.
3. **Assinatura Digital PKI:** O sistema implementa uma trilha de auditoria e persistência relacional de decisões humanas com integridade referencial, e não uma infraestrutura de chaves públicas ou certificados criptográficos (ICP-Brasil).
4. **Benchmark de OCR Tesseract:** Não foi executado comparativo de OCR Tesseract por não fazer parte do escopo da pipeline multimodal baseada em VLM.

---

## 6. Histórico de Commits da Branch `fix/redesign-integrity`

| Hash | Mensagem do Commit | Componentes Afetados |
|---|---|---|
| `f0c7164` | `fix(review): enforce exact hypothesis and run ownership` | `backend/api/app.py`, `backend/tests/test_api.py` |
| `f2d0839` | `fix(ui): isolate active document and guard review refresh` | `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/components/FindingsPanel.tsx` |
| `4f217f4` | `fix(viewer): unify evidence coordinates and scrollable zoom` | `frontend/src/components/DocumentViewer.tsx` |
| `473f677` | `feat(ui): add collapsible audit panels` | `frontend/src/components/DocumentQueue.tsx` |
| `51987eb` | `test(ui): reproduce delayed responses and preserve failed review input` | `frontend/playwright.config.ts`, `frontend/tests/e2e.spec.ts` |
