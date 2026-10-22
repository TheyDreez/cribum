# RELATÓRIO DE EXECUÇÃO DO MVP (CRIBUM / AUDITRX) — HISTÓRICO P0

> **Nota de Arquivo Histórico:** Este documento preserva o registro da entrega inicial do marco P0 do hackathon (outubro/2026, com a suíte inicial de 7 testes do backend). A suíte atualizada do projeto conta com **37 testes no backend (Pytest)** e **14 no frontend (Playwright)**. Para as métricas e limitações atuais, consulte [`docs/EVALUATION.md`](../EVALUATION.md) e [`docs/LIMITATIONS.md`](../LIMITATIONS.md).

**Equipe:** Inédito Viável (cadastrado como "Inedito Viavel")  
**Data:** 12 de Outubro de 2026  
**Hackathon:** AMD Developer Hackathon: ACT III (lablab.ai)  
**Trilha:** Health and Wellbeing  
**Branch de Entrega P0:** `feat/p0-vertical-slice`  

---

## 1. Resumo da Entrega

Foi implementado com autonomia o caminho vertical completo **P0** do sistema:
* **Backend:** Arquitetura FastAPI com validação estrita Pydantic v2 e persistência relacional SQLite via SQLAlchemy.
* **Segurança e Armazenamento:** Sanitização de upload (bloqueio de decompression bombs, contenção de path traversal e verificação real de formato de imagem Pillow).
* **Provedores de Inferência:** Separação rígida entre modo `REAL` (vLLM/ROCm com falha explícita se offline) e modo `DEMO` (fixtures determinísticas com banner).
* **Motor de Regras:** Regras determinísticas de consistência documental, duplicidade de hash e colisão fonética LASA baseadas na literatura do ISMP Brasil.
* **Análise Relacional:** Grafo NetworkX cruzando 200 guias para isolamento de esquemas geográficos anômalos.
* **Frontend:** Interface React + TypeScript + Tailwind CSS com visualizador de evidências SVG, painel de incerteza, formulário de supervisão humana (*Human-in-the-Loop*) e aba de navegação da rede.
* **Dataset Sintético:** 20 casos documentais gerados com seed fixa (42) e gabarito individual, além de 200 guias relacionais.
* **Avaliação Quantitativa:** Script `eval/run_eval.py` demonstrando 100% de recall em casos LASA e 100% de especificidade em controles negativos.

---

## 2. Funcionalidades Operacionais

* [x] Upload seguro de receitas e guias nos formatos PNG e JPEG com cálculo de hash SHA-256.
* [x] Extração estruturada de campos e apresentação do Top-3 de hipóteses de leitura.
* [x] Identificação de incerteza visual (`AMBIGUOUS`) destacada em âmbar.
* [x] Detecção de conflitos LASA e campos obrigatórios ausentes.
* [x] Overlay visual de Bounding Boxes interativo no frontend sobre o documento.
* [x] Formulário de Decisão Humana com persistência em SQLite e registro de `AuditEvent`.
* [x] Histórico de pareceres auditáveis consultável na interface.
* [x] Modelagem do grafo de 200 guias em NetworkX com identificação da anomalia de clínicas distantes.
* [x] Banner permanente e explícito de modo DEMO na interface.
* [x] Provedor REAL com erro 503 explicável e recusa de fallback silencioso.
* [x] Precarregamento automático dos 20 casos sintéticos via endpoint `/api/admin/seed-demo`.

---

## 3. Funcionalidades Incompletas e Pendências

* [ ] **Inferência Real em GPU AMD na Nuvem:** O adaptador `RealROCmProvider` está implementado e coberto por testes, mas a execução ao vivo em silício AMD depende do provisionamento da máquina remota com ROCm (previsto para o marco de infraestrutura da semana).
* [ ] **PDF Multipage:** O MVP foca em imagens médicas de página única (PNG/JPEG) por motivos de segurança e rastreabilidade visual direta.

---

## 4. Comandos para Iniciar e Endereços Locais

**1. Iniciar Backend:**
```powershell
.\.venv\Scripts\activate
uvicorn backend.api.app:app --port 8000 --reload
```
* Endereço: `http://localhost:8000`
* Documentação Swagger: `http://localhost:8000/docs`

**2. Iniciar Frontend:**
```powershell
cd frontend
npm run dev
```
* Endereço da Aplicação: `http://localhost:5173`

---

## 5. Testes Executados e Resultados Reais

Todos os testes automatizados foram executados no ambiente virtual do host com sucesso:

| Arquivo de Teste | Itens Avaliados | Resultado Real |
| :--- | :--- | :--- |
| `backend/tests/test_api.py` | Healthcheck, upload válido, upload malicioso corrompido, processamento DEMO, falha explícita do REAL sem fallback, persistência da decisão humana e endpoint de grafo. | **7 passed in 5.13s** (100% de aprovação) |
| `backend/tests/test_leitor.py` | Extração do LeitorAgent, cálculo de hash SHA-256 e consistência de schema. | **PASSED in 4.05s** |
| `eval/run_eval.py` | Recall de troca LASA (5/5), especificidade em controles limpos (5/5) e detecção de anomalia no grafo. | **100% de sucesso nas metas** |
| `npm run build` | Compilação estrita TypeScript do frontend via Vite. | **✓ built in 2.69s (0 erros)** |

---

## 6. Estado da Integração AMD

* **Hardware Local do Host:** NVIDIA GeForce RTX 3090 + AMD Radeon Graphics Integrada.
* **Modelo Alvo:** `Qwen/Qwen2-VL-7B-Instruct`.
* **Stack Alvo:** Docker container oficial `rocm/vllm:latest` servindo na porta 8000.
* **Status:** Adaptador pronto e testado em isolamento. Aguarda alocação da instância cloud da equipe para rodar o benchmark em MI300X/MI250.
