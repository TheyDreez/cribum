# CRIBUM — Relatório de Redesign da Experiência de Auditoria

**Data:** 13 de Outubro de 2026  
**Branch:** `redesign/audit-experience`  
**Documento:** `docs/AUDIT_EXPERIENCE_REDESIGN_REPORT.md`  
**Responsável:** Antigravity / Time Inédito Viável  

---

## 1. Resumo Executivo

A interface do **CRIBUM** foi integralmente reformulada para eliminar a estética "gamer / cyberpunk neon" do protótipo inicial e estabelecer uma **estação de trabalho pericial clínica, sóbria e documental**. 

Todos os fluxos funcionais, contratos de API, regras determinísticas, persistência SQLite e validações HITL foram estritamente preservados, conforme comprovado pela suíte automatizada de testes Playwright (12/12 cenários operacionais aprovados).

---

## 2. Diagnóstico Comparativo: Antes vs. Depois

| Aspecto | Estado Inicial (Rejeitado) | Novo Redesign CRIBUM |
|---|---|---|
| **Tema Geral** | Dark mode agressivo (`#0b0d10`) com contraste ofuscante contra o papel branco da guia | **Modo Claro / Neutro Sóbrio** (`#F8FAFC` / `#F1F5F9`), superfícies brancas (`#FFFFFF`) e texto escuro de alto contraste (`#0F172A`) |
| **Acentos de Cor** | Ciano neon (`#14b8a6`), brilhos intensos e gradientes artificiais | **Cores Clínicas Defensáveis**: Acento ardósia/marinho (`#0F172A`), azul documental (`#2563EB`) |
| **Sinalização de Risco** | Cartões vermelhos saturados competindo entre si | **Âmbar para incerteza** (`#D97706` / `bg-amber-50`) e **Carmim apenas para risco iminente** (`#BE123C` / `bg-rose-50`) |
| **Tipografia** | Excesso de fonte monoespaçada em quase todos os textos | **Inter / System Sans** legível; mono restrito estritamente a CRMs, hashes e IDs de regra |
| **Banner de Modo** | Faixa amarela berrante dominando o topo e empurrando a interface | **Aviso sutil e informativo** de modo DEMO no cabeçalho, sem repetição de texto |
| **Visualizador da Guia** | Imagem presa em caixa estreita de 760px cercada de vazio negro | **Canvas documental centralizado**, com modos nativos de Encaixar à Largura, Encaixar à Altura e Zoom fino |
| **Painel de Decisão** | Hierarquia desordenada, histórico empurrando o formulário para fora da tela | **Hierarquia probatória estrita**: Alertas → Hipóteses VLM → Parecer Humano → Histórico Retrátil |
| **Monitores Grandes** | Espaço desperdiçado em resoluções 1080p e 1440p | **Escalonamento responsivo** até 1300px de largura de documento em monitores amplos |

---

## 3. Estrutura e Ergonomia da Interface

### 3.1. Cabeçalho Institucional & Modo de Operação
- **Marca:** Nome unificado e centralizado: **CRIBUM** (v1.0.0).
- **Banner de Demonstração:** Notificação discreta e elegante em tom âmbar suave (`bg-amber-50 text-amber-900 border-amber-200/80`), declarando com transparência: *"Resultados originados de fixtures determinísticas documentadas. Não comprova inferência em hardware real."*
- **Selo de Hardware:** Identificação sóbria do motor ativo (`Fixture Demo Engine` em DEMO ou `AMD ROCm (vLLM)` em REAL).

### 3.2. Fila Documental Retrátil (Barra Lateral Esquerda)
- Largura calibrada (320px) com fundo branco e borda sutil (`border-slate-200`).
- Títulos amigáveis pré-formatados com indicação clara do teste pericial (e.g. *"Caso 01: Losartana vs Lorazepam (LASA)"*).
- Badges semafóricos legíveis:
  - Casos com inconformidades: `1 alerta` / `2 alertas` em pílula carmim suave.
  - Casos regulares: `Sem inconsistências` em cinza neutro.
  - Status de revisão: `Pendente` (cinza) e `Em Revisão` (âmbar discreto).
- Busca rápida por caso, nome ou ID, além de filtros de triagem rápida (*Todos*, *Pendentes*, *Com Alertas*).

### 3.3. Estação de Exame Documental (Centro)
- **Barra de Ferramentas:**
  - Botões de ajuste: `↔ Largura` e `↕ Altura` com indicação de estado ativo.
  - Controles de zoom: `-20%`, indicador numérico percentual (clique para redefinir para 100%), `+20%` e botão de reset `↺`.
  - Indicador pericial dinâmico do alerta selecionado, com truncamento elíptico seguro em telas compactas.
- **Bounding Boxes SVG:**
  - Evidências inativas: traço pontilhado azul celeste fino (`#0284c7`, 1.5px, 8% opacidade).
  - Evidência ativa do alerta: traço contínuo carmim pericial (`#f43f5e`, 2.5px, 20% opacidade) com etiqueta legível com o status pericial do campo.
- **Suporte a Pan:** Arraste livre com o mouse quando o documento estiver ampliado.

### 3.4. Painel de Revisão Pericial (Barra Lateral Direita)
Hierarquia probatória implementada em 4 níveis verticais:
1. **Alertas de Inconsistência:** Cartões de alerta com nível de severidade (`CRITICAL`, `HIGH`, `MEDIUM`), fundamentação da regra pericial, limitações do modelo e atalho `Ver Evidência` que ilumina a respectiva bounding box no documento.
2. **Hipóteses de Leitura do VLM:** Agrupamento por campo extraído, com selo descritivo de incerteza (*Ambiguidade Caligráfica*, *Leitura Indeterminada*, *Leitura Unívoca*). As alternativas de leitura contam com seleção via *radio button* direto e identificação transparente de *Score heurístico (não calibrado)*.
3. **Parecer do Auditor Humano (HITL):** Seleção de ação pericial, espelho visual da hipótese selecionada para confirmação, campo de fundamentação textual obrigatória e botão *"Registrar revisão"*.
4. **Histórico Persistido:** Seção retrátil (*Recolher ▲ / Expandir ▼*) que exibe decisões anteriores sem disputar espaço vertical com a tarefa ativa de revisão.

### 3.5. Grafo Relacional Multi-Entidade (NetworkX)
- Grade de métricas em cartões brancos limpos: Médicos, Clínicas/Hospitais, Procedimentos e Pacientes.
- Banner de limites probatórios em tom âmbar suave, ressaltando que distância geográfica e mesmo dia são indícios que demandam averiguação humana e não prova conclusiva de fraude.
- Visualização de subgrafo com distinção visual entre médicos investigados (carmim suave) e estabelecimentos vinculados (ardósia neutro).

---

## 4. Validação em Múltiplas Resoluções e Monitores Amplos

Foram capturados screenshots em navegadores com proporções e resoluções distintas:

| Resolução | Cenário de Uso | Arquivo de Screenshot |
|---|---|---|
| **1366 × 768** | Notebook corporativo | `docs/screenshots/redesign/notebook_1366x768.png` |
| **1920 × 1080** | Desktop padrão Full HD | `docs/screenshots/redesign/desktop_1920x1080.png` |
| **2560 × 1440** | Monitor amplo / QHD 2K | `docs/screenshots/redesign/wide_2560x1440.png` |
| **1920 × 1080** | Grafo Multi-Entidade | `docs/screenshots/redesign/desktop_1920x1080_graph.png` |

Em monitores amplos (2560px), a receita médica aproveita o espaço central de forma generosa (expandindo até 1300px em modo largura), garantindo perfeita nitidez da caligrafia médica sem gerar faixas pretas ou confinamento visual.

---

## 5. Resultados dos Testes Automatizados

### 5.1. Testes de Navegador E2E (Playwright)
Executados via `npx playwright test` contra a interface redesenhada:
```
Running 12 tests using 1 worker
  ok  1 Cenário 01: Selecionar documento na fila e acionar visualização pericial (46ms)
  ok  2 Cenário 02: Clicar em alerta/evidência e verificar destaque da bounding box SVG (65ms)
  ok  3 Cenário 03: Selecionar hipótese no radio button e refletir no formulário (117ms)
  ok  4 Cenário 04: Trocar de documento e verificar limpeza rigorosa do formulário HITL (141ms)
  ok  5 Cenário 05: Impedimento de confirmação quando nenhuma hipótese for selecionada (69ms)
  ok  6 Cenário 06: Submeter hipótese confirmada e verificar persistência no banco após reload (341ms)
  ok  7 Cenário 07: Verificar badges de status de revisão na fila documental (8ms)
  ok  8 Cenário 08: Race guard: alternância rápida entre documentos sem misturar imagens e dados (618ms)
  ok  9 Cenário 09: Coerência estrita entre imagem, achados e campos do mesmo documento (157ms)
  ok 10 Cenário 10: Seleção de anomalias no grafo exibe cards e guias distintas (264ms)
  ok 11 Cenário 11: Banner de modo DEMO e ausência de falsas alegações de hardware (18ms)
  ok 12 Cenário 12: Tentativa de inferência REAL sem endpoint falha explicitamente sem fallback (2.1s)
  12 passed (4.9s)
```

### 5.2. Testes de Backend (Pytest)
```
collected 20 items
backend/tests/test_amd_protocol.py ....                                  [ 20%]
backend/tests/test_api.py ...............                                [ 95%]
backend/tests/test_leitor.py .                                           [100%]
======================= 20 passed, 2 warnings in 9.26s ========================
```

---

## 6. Como Visualizar na Máquina Local

Com os serviços ativos na máquina:
- **Interface Visual Redesenhada:** [http://localhost:5173](http://localhost:5173)
- **API & Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
