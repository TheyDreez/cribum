<div align="center">

# CRIBUM 🛡️
### *Medical Forensics & Clinical Integrity Suite*
> **The Intelligent Sieve for Medical Claims, LASA Safety, and Healthcare Fraud Auditing.**  
> *Engineered for high-performance open-source vision-language models on **AMD ROCm™ & Instinct MI300X**.*

[![AMD ROCm](https://img.shields.io/badge/Engineered%20for-AMD%20ROCm%20%26%20Instinct-ED1C24?logo=amd&logoColor=white)](https://rocm.docs.amd.com/)
[![Domain](https://img.shields.io/badge/Domain-Clinical%20AI%20%26%20Forensics-blue)](https://github.com/TheyDreez/cribum)
[![RFC 6962](https://img.shields.io/badge/Auditability-Merkle%20Chain%20RFC%206962-10b981)](https://datatracker.ietf.org/doc/html/rfc6962)
[![Tests](https://img.shields.io/badge/Tests-22%20Pytest%20%7C%2014%20Playwright-success)](https://github.com/TheyDreez/cribum)
[![License](https://img.shields.io/badge/License-Proprietary%20%7C%20Source--Available-red.svg)](LICENSE)
[![Video Demo PT-BR](https://img.shields.io/badge/%E2%96%B6%EF%B8%8F%20Assistir%20Demo%20(PT--BR)-Campus%20Mobile-8b5cf6)](https://github.com/TheyDreez/cribum/raw/main/docs/Cribum_Campus_Mobile_Demo.mp4)

</div>

---

## 💎 Vitrine Visual da Workstation Pericial

> *Interface reativa em React 18 & TypeScript desenvolvida para peritos médicos, operadoras de saúde (ANS/TUSS) e equipes de Compliance (Blue Team).*

```text
+---------------------------------------------------------------------------------+
| [CRIBUM WORKSTATION v1.0]   | Case: CASE-AMB-001 [AMBIGUOUS / LASA]  [CCRI: 94] |
+---------------------------------+-----------------------------------------------+
| [A4 Medical Image & BBox]       | [AI Findings & Clinical Correlation]          |
|  .---------------------------.  | - Alerta LASA: Losartana 50mg vs Lorazepam    |
|  | [X] Bounding Box 0..1     |  | - CID-10 I10 (Hipertensão) × Incompatibilidade|
|  |     (Visual Evidence)     |  | - Glosa Preventiva Calculada: R$ 1.480,00     |
|  '---------------------------'  | - Cadeia de Custódia SHA-256 (RFC 6962 Ativa) |
+---------------------------------+-----------------------------------------------+
| [Filtros Ópticos Forenses: Negatoscópio | High-Pass | Otsu Binarization]        |
+---------------------------------------------------------------------------------+
```

| Mesa de Inspeção Documental & Correlação Clínica (`CASE-AMB-001`) | Topologia Relacional & Conluio Geográfico (`NetworkGraphView`) |
| :---: | :---: |
| ![Workstation Pericial](docs/screenshots/redesign/desktop_1920x1080.png) | ![Grafo de Rede](docs/screenshots/redesign/desktop_1920x1080_graph.png) |

---

## 🚀 O Problema & A Solução

* **O Desafio Global:** Fraudes, desperdícios e abusos drenam **R$ 34 bilhões anualmente** da saúde suplementar no Brasil (IESS), enquanto erros de dispensação por caligrafia ilegível em medicamentos de Alta Vigilância (**LASA** — *Look-Alike Sound-Alike*, ex: *Losartana* vs *Lorazepam*) colocam vidas em risco iminente.
* **A Resposta do CRIBUM:** Uma plataforma soberana e auto-hospedada que unifica **Visão Computacional Multimodal (Qwen2-VL)**, **motores determinísticos de regras (ISMP Brasil)**, **análise de redes complexas (NetworkX / Grafo)** e **trilha imutável baseada em Merkle Chains (RFC 6962)** sobre aceleradores **AMD ROCm™**.

---

## 🏛️ Arquitetura Multi-Agente & Soberania de Dados

O sistema opera de forma estritamente colaborativa (`backend/agents/`), posicionando a inteligência artificial como assistente de evidências sob **supervisão humana obrigatória (Human-in-the-Loop - HITL)**:

1. **`Leitor` (`backend/agents/leitor.py` — VLM Qwen2-VL em AMD ROCm):** Extração de hipóteses top-3, metadados e coordenadas de *Bounding Box* normalizadas (`0..1`) com tratamento rigoroso de incerteza.
2. **`Farmacêutico` (`backend/agents/farmaceutico.py` — Motor de Regras ISMP):** Cruzamento estrito de listas de medicamentos LASA, validação de compatibilidade diagnóstica via CID-10 e verificação de duplicidade por hash SHA-256.
3. **`Investigador` (`backend/agents/investigador.py` — Grafo de Anomalias de Rede):** Detecção de conluio geográfico em lote de 200 guias (ex: faturamentos concomitantes pelo mesmo CRM no mesmo dia em municípios distantes).
4. **`Relator` (`backend/agents/relator.py` — Dossiê Criptográfico & ROI):** Emissão de laudo pericial estruturado com cálculo de glosa preventiva (TUSS/ANS), Score Multimodal CCRI (0–100) e selo criptográfico encadeado via SHA-256 (`prev_chain_hash` $\rightarrow$ `chain_hash`).

---

## ⚙️ Prontidão de Hardware AMD Instinct MI300X / ROCm™ 6.2

O CRIBUM foi arquitetado para extrair o máximo potencial dos aceleradores AMD de alta capacidade de memória HBM3 (`docker/docker-compose.rocm.yml`):
* **Paralelismo de Dados no Vision Encoder (`--mm-encoder-tp-mode data`):** Processamento nativo de guias A4 em alta resolução sem fatiamento destrutivo de traços caligráficos.
* **Prefix Caching Ativo (`--enable-prefix-caching`):** Compartilhamento de contexto de sistema na HBM3 para reduzir o *Time-To-First-Token* em prompts de auditoria estruturados.
* **Zero Mock Silencioso:** Garantia de integridade contratual. Se o modo `REAL` for acionado sem endpoint vLLM/ROCm ativo, o sistema reporta `HTTP 503 INFERENCE_UNAVAILABLE` explicitamente de forma auditável, sem inventar resultados falsos.

---

## ⚡ Guia Rápido de Instalação e Testes

### Pré-requisitos
* Python 3.12+
* Node.js 18+

### 1. Backend (FastAPI + SQLite + Merkle Chain)
```bash
git clone -b main https://github.com/TheyDreez/cribum.git
cd cribum
python -m venv .venv
source .venv/bin/activate  # No Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.api.app:app --port 8000 --reload
```

### 2. Frontend (React 18 + Tailwind Workstation)
Em outro terminal:
```bash
cd cribum/frontend
npm install
npm run dev
```
Acesse `http://localhost:5173` e clique em **"Carregar 20 Casos Sintéticos"** no topo para popular o workspace.

### 3. Validação de Testes Automatizados (100% Verde)
* **Testes Unitários & Contratos Backend (22 testes Pytest):**
```bash
python -m pytest -v
```
* **Testes E2E de Navegador (14 cenários Playwright):**
```bash
cd frontend && npx playwright test
```

---

## ⚖️ Licença
Distribuído sob a Licença MIT. Veja [`LICENSE`](LICENSE) para mais detalhes.
