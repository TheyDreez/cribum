# MANIFESTO E DOCUMENTAÇÃO DO DATASET SINTÉTICO

**Seed de Reprodutibilidade:** `42`  
**Origem dos Dados:** 100% gerados sinteticamente por script determinístico (`backend/data/synthetic/generate_dataset.py`).  
**Identificadores:** Explicitamente fictícios (`PACIENTE-DEMO-xxx`, `PROF-DEMO-xxx`, `CLINICA-DEMO-xxx`).

---

## 1. Conjunto Documental de Teste (20 Casos)

O conjunto de 20 casos é dividido em quatro quadrantes metodológicos com gabarito formal em `backend/data/synthetic/ground_truth/`:

| Faixa de Casos | Categoria | Quantidade | Descrição do Desafio | Alerta Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **Casos 01 a 05** | `AMBIGUITY_LASA` | 5 casos | Grafia ambígua simulada entre pares críticos do ISMP (Losartana x Lorazepam, Fluoxetina x Flunarizina, etc.). | `MED-001-AMBIGUOUS-READING`, `MED-002-LASA-xxx` |
| **Casos 06 a 10** | `DOCUMENT_INCONSISTENCY` | 5 casos | Falhas estruturais de preenchimento (CRM ausente, dose sem unidade mg/ml, divergência de diagnóstico CID-10). | `DOC-002-MISSING-CRM` |
| **Casos 11 a 15** | `DUPLICATE_CLAIM` | 5 casos | Guias reemitidas ou reenviadas com procedimentos de repetição para teste de hash e duplicidade. | Teste de consistência de envio |
| **Casos 16 a 20** | `CONTROL_CLEAN` | 5 casos | Casos clínicos perfeitamente preenchidos sem qualquer irregularidade (grupo de controle negativo). | **Nenhum alerta esperado** |

---

## 2. Conjunto de Rede Relacional (200 Guias)

* **Arquivo:** `backend/data/synthetic/network/claims_200.json`
* **Entidades:** 100 pacientes, 24 profissionais, 5 clínicas/hospitais em cidades do estado de SP (Sorocaba, Campinas, São Paulo, São José dos Campos, Santos).
* **Anomalia Injetada (Gabarito de Fraude):**
  * O profissional `PROF-DEMO-007` possui faturamentos de procedimentos no mesmo dia (`2026-10-14`) tanto em Sorocaba (`CLINICA-DEMO-001`) quanto em Santos (`CLINICA-DEMO-005`), cidades a 180 km de distância rodoviária.
  * O motor de regras de rede (`NET-001-CONCURRENT-DISTANT-CLINICS`) deve detectar esse cluster e apresentar a evidência para auditoria humana.

---

## 3. Limitações Metodológicas Declaradas

1. **Simulação Caligráfica:** Documentos gerados com fontes ou caixas padronizadas não reproduzem a complexidade e degradação física de receitas médicas manuscritas reais em papel carbono ou com tinta desbotada.
2. **Uso Exclusivo para Avaliação:** Os dados sintéticos servem estritamente para validar a arquitetura, o fluxo de auditoria e a consistência das regras. Não possuem validação epidemiológica.
