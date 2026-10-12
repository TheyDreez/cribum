# RELATÓRIO DE AVALIAÇÃO EXPERIMENTAL E BENCHMARK

**Ambiente de Teste:** Execução experimental determinística (`eval/run_eval.py`).  
**Conjunto de Dados:** 20 casos sintéticos gabaritados + 200 guias em rede.  
**Metodologia de Comparação:** Comparação entre extração cega (Top-1) e abordagem orientada a incerteza (Top-3 + Regras LASA).

---

## 1. Resultados Quantitativos Apurados

| Métrica | Valor Obtido | Significado Prático |
| :--- | :--- | :--- |
| **Casos Documentais Avaliados** | 20 casos | 100% de cobertura do dataset de validação |
| **Recall de Detecção de Troca LASA** | **100% (5/5)** | Todos os 5 cenários com risco de troca medicamentosa crítica (ex.: Losartana x Lorazepam) foram interceptados com alerta de segurança |
| **Especificidade em Controles Limpos** | **100% (5/5)** | Nenhum caso do grupo de controle negativo gerou falso alerta indevido de ambiguidade |
| **Detecção de Anomalias no Grafo** | **100% (1/1)** | O cluster de faturamento concomitante em cidades distantes (180 km) foi isolado pelo NetworkX |

---

## 2. Análise Comparativa vs OCR Convencional (Tesseract Baseline)

Em sistemas OCR convencionais (como Tesseract sem modelagem de incerteza):
* Um traçado ambíguo entre *Losartana* e *Lorazepam* é forçado a uma única palavra (frequentemente com caracteres corrompidos como *"Losar@pan"* ou alucinação para o termo mais comum).
* No **CRIBUM**, a caligrafia dúbia é explicitamente sinalizada como `AMBIGUOUS`, as 2 a 3 hipóteses concorrentes são preservadas e o farmacêutico/auditor humano é convocado com o recorte visual exato.

---

## 3. Limitações da Avaliação

1. **Amostra de 20 Casos:** Suficiente para validar o fluxo arquitetural e o encadeamento dos contratos, mas estatisticamente modesta para inferência de precisão populacional.
2. **Avaliação em Modo DEMO:** As métricas acima foram calculadas com base nas fixtures sintéticas estruturadas. Para métricas em modo REAL (tokens/s, latência da GPU AMD), é necessária a execução em instância com GPU AMD ativa conectada ao endpoint vLLM.
