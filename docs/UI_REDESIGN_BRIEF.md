# CRIBUM — Briefing de Redesign Visual e Ergonômico da Interface

**Data:** 13 de Outubro de 2026  
**Documento:** `docs/UI_REDESIGN_BRIEF.md`  
**Status:** Planejamento para Sprint de Redesign (Aprovado para Implementação Futura)  
**Público-Alvo:** Auditores Médicos, Farmacêuticos Clínicos, Analistas de Sinistros e Peritos Forenses  

---

## 1. Justificativa e Diagnóstico da Interface Atual

A interface inicial do protótipo foi rejeitada na revisão de produto. Embora funcionalmente íntegra após as correções de P0 (isolamento de execuções, HITL rigoroso e vínculo estrito de hipóteses), o layout visual apresenta atritos operacionais severos para uso em ambiente de produção:

1. **Tema "Cyberpunk / Dark Mode Saturado":**
   - O esquema de cores escuras profundas (`#0f172a`, `#090d16`) combinado com bordas ciano/neon e brilhos intensos cansa a vista de auditores que passam de 6 a 8 horas por dia analisando guias digitalizadas (frequentemente escaneadas em fundo branco com ruído de digitalização).
   - O contraste extremo entre o papel branco da receita médica e o fundo escuro da interface gera ofuscamento ocular e fadiga visual rápida.

2. **Densidade e Distribuição Espacial Rígida:**
   - A divisão tripartida da tela possui larguras desbalanceadas (a lista de documentos ocupa espaço lateral fixo desproporcional em relação à área de leitura pericial).
   - O visualizador do documento dependia de rolagem cruzada e não possuía modos de encaixe adaptativo (*fit-to-width* / *fit-to-page* nativos) até a implementação recente dos botões mínimos de zoom.

3. **Poluição de Badges e Terminologia:**
   - Termos como "Certeza Visual" e porcentagens estáticas (e.g. 95%) induziam falsa precisão matemática.
   - O painel de anomalias acumulava cartões vermelhos que competiam visualmente entre si, sem distinguir o que era risco clínico iminente (LASA) de mera irregularidade cadastral (falta de carimbo).

---

## 2. Princípios de Design e Ergonomia Pericial

### 2.1. Sobriedade Clínica e Tema Neutro/Claro (*Sober Professional*)
- **Paleta Neutra:** Fundo principal em tons de cinza cirúrgico e ardósia claro (`#F8FAFC`, `#F1F5F9`), bordas suaves (`#E2E8F0`), texto de alto contraste tipográfico (`#0F172A`, `#334155`).
- **Opção de Tema Dual:** Alternância explícita entre Modo Dia (fundo claro ideal para leitura de laudos e guias brancas) e Modo Neutro Noturno (cinza escuro balanceado `#1E293B`, sem neons).
- **Sem Saturação Gamificada:** Acentos de cor reservados estritamente para dados periciais (verde para concordância, âmbar para atenção/incerteza, carmim para risco clínico ou incompatibilidade).

### 2.2. Hierarquia de Informação Centrada no Documento
O fluxo cognitivo do auditor segue a ordem probatória natural:
```
1. Verificação Primária (Imagem Real da Guia + Bounding Boxes com Zoom Pericial)
       ↓
2. Desambiguação Heurística (Hipóteses VLM ordenadas por rank probatório)
       ↓
3. Contexto Relacional (Alertas Clínicos & Cruzamento Cadastral CFM/CNES)
       ↓
4. Parecer & Despacho Humano (Decisão vinculada ao run_id e field_id com justificativa)
```

---

## 3. Especificação dos Componentes da Nova Interface

### 3.1. Fila Documental Retrátil (*Audit Triage Sidebar*)
- Lista compacta recolhível para maximizar a área útil de leitura.
- Indicador unificado de risco:
  - **Ícone de Risco Clínico:** Triângulo âmbar para fármacos LASA ou dosagens críticas.
  - **Status de Auditoria:** "Pendente", "Em Análise", "Validado", "Rejeitado" ou "Escalado".
  - **Busca Rápida:** Filtro por CRM, Nome do Paciente, Medicamento e Protocolo.

### 3.2. Estação de Exame Documental (*Document Inspection Canvas*)
- **Barra de Ferramentas Superior:**
  - Controles de zoom: Encaixar na Largura, Encaixar na Página, 100%, 200%.
  - Rotação de imagem em 90° (essencial para guias digitalizadas invertidas).
  - Filtro de realce de contraste e inversão binária (facilita leitura de caligrafia em caneta esferográfica fraca).
- **Camada de Bounding Boxes Vetoriais:**
  - Caixas SVG com linhas finas e etiquetas semi-transparentes que não ocultam o traço da tinta original.
  - Realce sutil em hover com foco suave na região clicada.

### 3.3. Painel de Hipóteses e Evidências (*Findings & Hypotheses Panel*)
- Comparador lado a lado de hipóteses do modelo VLM.
- Destaque claro entre:
  - Hipótese Principal do Modelo.
  - Alternativas de Leitura Fonética/Gráfica (com indicação do risco LASA correspondente).
  - Leitura Indeterminada / Ilegível (requer transcrição manual pelo auditor).
- Exibição transparente da heurística empregada, sem falsos percentuais de acurácia.

### 3.4. Terminal de Parecer e Despacho (*HITL Adjudication Console*)
- Seleção direta por teclado (atalhos numéricos `1`, `2`, `3` para seleção de hipótese).
- Campo de justificativa com modelos periciais pré-formatados (ex.: "Caligrafia ilegível no campo posologia", "Concordância com prescrição anterior", "Discrepância em relação à especialidade").
- Registro de auditoria assinado digitalmente com carimbo de tempo, `run_id`, `field_id` e identificação do auditor.

### 3.5. Grafo de Relações e Vínculos Multi-Entidade
- Visualização limpa em SVG/Canvas sem elementos de cenário estáticos ou ilustrações fictícias.
- Foco em conexões reais extraídas da base: Médico ↔ Paciente ↔ Estabelecimento ↔ Data do Atendimento.
- Painel lateral com disclaimers probatórios explícitos, separando fatos verificados de indícios estatísticos.

---

## 4. Guia de Implementação e Tokens de Design Recomendados

| Elemento | Token / Estilo Proposto | Finalidade |
|---|---|---|
| Background Geral | `#F8FAFC` (Slate 50) | Conforto óptico em turnos prolongados |
| Superfície de Cartões | `#FFFFFF` com borda `#E2E8F0` | Separação física clara dos módulos |
| Imagem Documental | Borda fina `#CBD5E1`, sombra suave | Foco absoluto no documento original |
| Bounding Box Ativa | `#DC2626` (Red 600) com tracejado 2px | Destaque imediato sem cobrir a grafia |
| Bounding Box Secundária | `#2563EB` (Blue 600) com linha contínua 1px | Localização dos demais campos da guia |
| Alerta LASA | `#FEF3C7` (Amber 100) / `#92400E` (Amber 800) | Alerta de segurança sem pânico visual |
| Tipografia | Inter ou Geist Sans, tabular nums | Leitura rápida de CRMs, datas e posologias |

---

## 5. Próximos Passos
1. Validar os protótipos de baixa e alta fidelidade com os auditores clínicos de referência.
2. Implementar a alternância de tema no Tailwind (`light`/`neutral-dark`).
3. Refatorar o layout das 3 colunas para um grid responsivo com barra lateral retrátil.
4. Adicionar atalhos de teclado periciais para agilizar a revisão de documentos em massa.
