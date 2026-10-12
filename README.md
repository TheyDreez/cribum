# CRIBUM 🛡️
> *From the Latin **Cribrum** — The Intelligent Sieve for Medical Claims & Prescription Auditing.*

[![AMD ROCm](https://img.shields.io/badge/Powered%20by-AMD%20ROCm-ED1C24?logo=amd&logoColor=white)](https://rocm.docs.amd.com/)
[![Track](https://img.shields.io/badge/Hackathon%20Track-Health%20%26%20Wellbeing-blue)](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CRIBUM** is a local, privacy-first multi-agent medical claim and prescription audit system built entirely on **AMD GPUs via ROCm**. Designed as an intelligent assistant for human auditors, health insurance compliance teams, and forensic analysts, CRIBUM detects medication errors, Look-Alike Sound-Alike (LASA) confusions, and systemic fraud networks without any sensitive patient data ever leaving the secure server.

Built by **Inédito Viável** (*"Untested Feasibility"*) — Sorocaba/SP, Brazil — for the **AMD Developer Hackathon: ACT III**.

---

## 🎯 3 Key Differentiators

Unlike traditional OCR solutions or opaque black-box APIs:

1. **Uncertainty-Aware Multi-Hypothesis Reading:**  
   Instead of guessing blindly on illegible handwriting, CRIBUM extracts the **top 3 most probable hypotheses** for each item, cross-checks against the official **LASA (Look-Alike Sound-Alike / ISMP)** safety database and clinical context, and raises critical alerts when high-risk medication swaps are suspected (e.g., *Losartana* vs. *Lorazepam*).

2. **Visual Traceability (Bounding Box Evidence):**  
   Every audit finding and discrepancy is physically linked to its exact normalized visual coordinate `[ymin, xmin, ymax, xmax]` on the source prescription. Auditors click the alert and immediately inspect the illuminated region.

3. **Multi-Claim Network Fraud Analysis:**  
   Moves beyond single-document review. A graph-based engine (**NetworkX**) analyzes cross-claim relationships across patients, physicians (CRM), clinics, and procedures to spot organized fraud patterns (e.g., impossible travel velocities, concurrent procedure billings, and statistical outliers).

---

## 🧠 Multi-Agent Architecture

```
                  ┌───────────────────────────────────────────────┐
                  │           Medical Document / Claim            │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │       AGENT 1: LEITOR           │
                         │  Open VLM (Qwen2-VL) on vLLM   │
                         │    AMD ROCm GPU Acceleration    │
                         └────────────────┬────────────────┘
                                          │ Top-3 Hypotheses + Bounding Boxes
                                          ▼
                         ┌─────────────────────────────────┐
                         │     AGENT 2: FARMACÊUTICO       │
                         │  LASA Rules, ISMP, Dosage,     │
                         │     Clinical Context Checks     │
                         └────────────────┬────────────────┘
                                          │ Clinical Validation
                                          ▼
                         ┌─────────────────────────────────┐
                         │     AGENT 3: INVESTIGADOR       │
                         │  Network Graph Anomaly Engine   │
                         │    (Cross-Claim Multi-Node)     │
                         └────────────────┬────────────────┘
                                          │ Fraud Patterns
                                          ▼
                         ┌─────────────────────────────────┐
                         │       AGENT 4: RELATOR          │
                         │  Explainable Audit Dossier      │
                         │  Risk Scoring + Human Escalation│
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │            Auditor Web Interface              │
                  │   Queue · Visual Inspection · Fraud Graph     │
                  └───────────────────────────────────────────────┘
```

---

## 🛡️ Safety & Human-in-the-Loop Safeguards

In strict compliance with the **Health and Wellbeing Track Safety Guidelines**:
- **Non-Autonomous:** CRIBUM is explicitly an auditor-support tool. It never provides direct clinical diagnosis or automated prescription decisions.
- **Fail-Safe Insecurity Escalation:** When visual confidence falls below safety thresholds or a LASA collision is flagged, the item is tagged with `incerteza: alta` and escalated directly into the human auditor review queue.
- **Data Privacy & Sovereignty:** Zero cloud API leakage. All weights run locally on AMD infrastructure, fully compliant with LGPD and GDPR medical record regulations.

---

## 💻 AMD Technology Stack & Evidence

- **Hardware:** AMD Instinct / Cloud-based AMD GPUs (AMD Developer Cloud).
- **Execution Stack:** AMD ROCm™ 6.x + `vLLM` ROCm Docker serving container.
- **Inference Pipeline:** Open Vision-Language Models (e.g., `Qwen/Qwen2-VL-7B-Instruct`) hosted via OpenAI-compatible endpoints with FP16/BF16 tensor cores.
- **Telemetry:** Built-in latency and VRAM telemetry benchmarks comparing local AMD throughput versus external pay-per-token commercial APIs.

---

## 📂 Project Structure

```
cribum/
├── backend/
│   ├── agents/            # Leitor, Farmacêutico, Investigador, Relator
│   ├── data/
│   │   ├── references/    # LASA lists, dosage reference ranges
│   │   └── synthetic/     # 20 hand-crafted & 200 synthetic claims + ground truth
│   ├── schemas/           # Pydantic JSON validation schemas
│   └── requirements.txt
├── benchmarks/            # ROCm latency, VRAM, and throughput benchmark scripts
├── docker/                # ROCm vLLM deployment configs
├── frontend/              # Auditor React UI (Queue, Visual BBox viewer, Graph)
└── README.md
```

---

## 🚀 Quickstart

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch AMD ROCm vLLM Server
```bash
docker run -it --network=host --device=/dev/kfd --device=/dev/dri \
  --group-add video --ipc=host --shm-size 16G \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  rocm/vllm:latest \
  python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --port 8000
```

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
