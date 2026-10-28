# REGISTRO DE DECISÕES ARQUITETURAIS (ADR)

---

## ADR-001: Persistência Relacional Leve (SQLite + SQLAlchemy)
* **Contexto:** Necessidade de persistir decisões do auditor humano, histórico de revisões e metadados de execução com garantia de durabilidade após reinicializações.
* **Decisão:** Utilizar SQLite local via SQLAlchemy 2.0.
* **Justificativa:** Elimina a complexidade de gerenciar instâncias de PostgreSQL/Redis durante o hackathon, mantendo total conformidade com transações ACID e integridade referencial.
* **Consequência:** Adequado para escala de MVP (milhares de guias locais). Migração para PostgreSQL requer apenas alteração da connection string.

---

## ADR-002: Proibição Estrita de Fallback Silencioso entre REAL e DEMO
* **Contexto:** Risco de mascarar indisponibilidade de infraestrutura GPU AMD retornando mocks estáticos sem que o usuário ou avaliador perceba.
* **Decisão:** Se o modo configurado for `REAL` e o endpoint vLLM/ROCm estiver offline ou responder com erro, a API falha explicitamente com código HTTP 503 (`INFERENCE_UNAVAILABLE`).
* **Justificativa:** Transparência pericial e honestidade de engenharia. O modo DEMO é ativado exclusivamente por configuração explícita e sinalizado por banner permanente na interface.

---

## ADR-003: Contrato de Coordenadas Normalizadas (0.0 a 1.0)
* **Contexto:** Bounding boxes retornados por modelos visuais variam conforme a resolução original da imagem, zoom da tela e rotação.
* **Decisão:** Padronizar todas as coordenadas de evidência em formato normalizado `[x_min, y_min, x_max, y_max]` entre 0.0 e 1.0.
* **Justificativa:** Permite que a camada de visualização em SVG no React redimensione as caixas perfeitamente em qualquer tamanho de tela sem distorção.

---

## ADR-004: Separação entre Incerteza Visual e Alerta de Regra
* **Contexto:** Tendência de sistemas de IA de aglutinar "dúvida na leitura" com "suspeita de fraude" em uma única métrica vaga de risco.
* **Decisão:** Manter campos distintos: `uncertainty_status` (qualidade da leitura visual) e `category`/`severity` de `Finding` (regras clínicas e documentais).
* **Justificativa:** Caligrafia ilegível é uma barreira de comunicação, não necessariamente uma fraude. Misturar esses conceitos compromete a credibilidade da auditoria.
