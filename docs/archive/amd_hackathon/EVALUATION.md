# RELATÓRIO DE AVALIAÇÃO EM FIXTURES SINTÉTICAS

**Ambiente de Teste:** Execução experimental determinística (`eval/run_eval.py`).  
**Conjunto de Dados:** 20 casos sintéticos gabaritados + 200 guias em rede.  
**Metodologia de Comparação:** Comparação entre extração cega (Top-1) e abordagem orientada a incerteza (Top-3 + Regras LASA).

---

## 1. Resultados Quantitativos Apurados (Fixtures Sintéticas)

O script `eval/run_eval.py` afere a consistência determinística do motor de regras frente às fixtures do catálogo sintético.

Dos 20 casos sintéticos gerados:
* **11 cenários possuem validação determinística ativa no script**:
  * **5/5 Casos Críticos LASA** (`CASE-AMB-001` a `005`): 100% interceptados com alerta de segurança farmacológica (Top-1 e Top-3).
  * **5/5 Casos de Controle Limpo** (`CASE-CTR-016` a `020`): 100% validados com zero falso positivo (especificidade 100%).
  * **1/1 Anomalia de Rede no Grafo** (`claims_200.json`): cluster de faturamento concomitante em municípios distantes (Sorocaba e Santos) isolado pelo NetworkX.
* **9 cenários adicionais (Casos 06 a 15)**: Casos de inconformidades estruturais (CRM ausente/incompleto, dose sem unidade) e duplicidades de lote. Esses casos integram o catálogo sintético para testes de robustez de schema e inspeção visual, possuindo `expected_findings: []` no gabarito formal (não disparam alertas farmacológicos LASA no motor determinístico).

Em resumo, os resultados aferidos pelo script cobrem com rigor:
**5/5 LASA, 5/5 controles limpos e 1/1 anomalia de grafo em fixtures sintéticas**.

| Métrica | Resultado nas Fixtures | Escopo do Teste |
| :--- | :--- | :--- |
| **Interceptação de Conflito LASA** | **5/5 (100%)** | Casos ambíguos com risco de troca crítica (ex.: Losartana x Lorazepam) |
| **Especificidade em Controles Limpos** | **5/5 (100%)** | Prescrições de controle sem falsos alertas indevidos de ambiguidade |
| **Detecção de Anomalia de Rede** | **1/1 (100%)** | Detecção topológica de faturamento simultâneo no grafo de 200 guias |
| **Catálogo Sintético Total** | **20 casos** | 11 com regras ativas no eval + 9 de carga e inspeção visual |

---

## 2. Análise Comparativa vs OCR Convencional (Tesseract Baseline)

Em sistemas OCR convencionais (como Tesseract sem modelagem de incerteza):
* Um traçado ambíguo entre *Losartana* e *Lorazepam* é forçado a uma única palavra (frequentemente com caracteres corrompidos como *"Losar@pan"* ou alucinação para o termo mais comum).
* No **CRIBUM**, a caligrafia dúbia é explicitamente sinalizada como `AMBIGUOUS`, as 2 a 3 hipóteses concorrentes são preservadas e o farmacêutico/auditor humano é convocado com o recorte visual exato.

---

## 3. Limitações da Avaliação

1. **Amostra de 20 Casos:** Suficiente para validar o fluxo arquitetural e o encadeamento dos contratos, mas estatisticamente modesta para inferência de precisão populacional.
2. **Avaliação em Modo DEMO:** As métricas acima foram calculadas com base nas fixtures sintéticas estruturadas. Para métricas em modo REAL (tokens/s, latência da GPU AMD), é necessária a execução em instância com GPU AMD ativa conectada ao endpoint vLLM.
