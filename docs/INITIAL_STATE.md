# ESTADO INICIAL DO WORKSPACE (INSPEÇÃO OBRIGATÓRIA)

**Data da Inspeção:** 12 de Outubro de 2026, 19:45 BRT  
**Diretório do Projeto:** `C:\Users\andre\.gemini\antigravity\scratch\cribum`  
**Repositório Git:** Inicializado e vinculado a `https://github.com/TheyDreez/cribum.git`  
**Branch Atual:** `feat/leitor-agent` (sincronizada com origin)

---

## 1. Ferramental e Runtimes Identificados

| Componente | Versão / Caminho | Status |
| :--- | :--- | :--- |
| **Python** | Python 3.12.14 (`.venv\Scripts\python.exe`) | Instalado e funcional via `uv` |
| **uv** | `C:\Users\andre\.local\bin\uv.exe` | Instalado e funcional |
| **Node.js** | v24.15.0 | Instalado e funcional |
| **npm** | 11.12.1 | Instalado e funcional |
| **Docker** | Docker version 29.7.2, build a7dcaa6 | Instalado |
| **Git** | git version 2.54.0.windows.1 | Autenticado como `TheyDreez` |

---

## 2. Inventário de Hardware e GPU Local

* **Controlador 1:** `NVIDIA GeForce RTX 3090` (Driver 32.0.16.1074)
* **Controlador 2:** `AMD Radeon(TM) Graphics` (Processador integrado 0x164E, Driver 32.0.21030.2001)
* **Observação de Infraestrutura:** A inferência oficial em GPU AMD ROCm (MI300X/MI250) é projetada para ser executada no ambiente AMD Developer Cloud / Cloud credenciada. O adaptador local implementará o padrão `ProviderAdapter` com modos explícitos `REAL` e `DEMO`.

---

## 3. Estado dos Arquivos Existentes no Repositório

Antes desta fase de expansão para o MVP P0 completo, o repositório continha:
1. `backend/schemas/claim.py`: Schemas Pydantic básicos (`PrescriptionItem`, `HeaderData`, `PharmacistAlert`, `NetworkAnomaly`, `HumanDecision`, `AuditDossier`).
2. `backend/agents/leitor.py`: `LeitorAgent` com suporte a base64, hash SHA-256 e integração HTTP ao vLLM.
3. `backend/data/references/lasa_ismp.json`: Base de 10 pares de alto risco do ISMP Brasil.
4. `backend/tests/test_leitor.py`: Teste de fumaça executado com sucesso.
5. `docker/docker-compose.rocm.yml`: Configuração Docker Compose para o vLLM em ROCm.
6. `README.md` e `LICENSE`: Documentação e licença MIT.

---

## 4. Plano de Preservação e Integração (Diretriz P0)

* **Preservar o que funciona:** O `LeitorAgent` e a base `lasa_ismp.json` já implementados serão mantidos e integrados aos novos contratos formais.
* **Novas adições para o MVP P0 completo:**
  1. **Contratos e Entidades Mínimas (ORM SQLAlchemy + SQLite):** `Document`, `ProcessingRun`, `ExtractedField`, `Finding`, `ReviewDecision`, `AuditEvent`.
  2. **Modos REAL vs DEMO Explícitos:** Provider com fallback proibido (falha real gera erro explícito; DEMO usa fixtures determinísticas marcadas).
  3. **Dataset Sintético Gabaritado:** 20 casos documentais sintéticos + manifesto com seed fixa.
  4. **API FastAPI:** Endpoints REST para upload seguro, processamento, listagem de evidências e persistência da decisão humana.
  5. **Frontend React + Vite + TypeScript:** Interface limpa com fila de auditoria, visualizador de evidências com bounding box, alternador de hipóteses e registro de parecer humano.
  6. **Documentação Completa de Arquitetura e Decisões.**
