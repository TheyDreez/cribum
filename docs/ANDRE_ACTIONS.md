# AÇÕES NECESSÁRIAS DO ANDRÉ (CONFIGURAÇÃO & OPERAÇÃO)

Este arquivo lista estritamente as ações que exigem sua intervenção manual ou credenciais externas.

---

## Ação 1: Iniciar os Servidores Locais para Demonstração (Modo DEMO)

* **Onde executar:** Terminal local (PowerShell).
* **Pré-requisito:** Runtimes Python 3.12 (`.venv`) e Node.js instalados.
* **Comandos exatos:**

**Janela 1 (Backend FastAPI):**
```powershell
cd C:\Users\andre\.gemini\antigravity\scratch\cribum
.\.venv\Scripts\activate
uvicorn backend.api.app:app --port 8000 --reload
```
* **Resultado esperado:** Mensagem indicando `Application startup complete` em `http://127.0.0.1:8000`.
* **Como validar:** Acessar `http://127.0.0.1:8000/health` e receber `{"status": "ok"}`.

**Janela 2 (Frontend React/Vite):**
```powershell
cd C:\Users\andre\.gemini\antigravity\scratch\cribum\frontend
npm run dev
```
* **Resultado esperado:** Servidor Vite ativo em `http://localhost:5173`.
* **Como validar:** Abrir `http://localhost:5173` no navegador e clicar no botão *"Carregar 20 Casos Sintéticos"*.

---

## Ação 2: Conectar Instância com GPU AMD Cloud (Quando Disponível)

* **Onde executar:** Servidor remoto na cloud (AMD Developer Cloud / Crusoe / TensorDock) com GPU AMD (MI300X/MI250/Radeon).
* **Pré-requisito:** Docker instalado no servidor remoto e porta 8000 liberada na rede interna ou via túnel SSH.
* **Comando exato no servidor da GPU:**
```bash
docker run -d --name cribum-vllm-rocm \
  --network=host \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  --shm-size 16G \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  rocm/vllm:latest \
  python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --port 8000
```
* **Variável a preencher no `.env` do backend local:**
```ini
EXECUTION_MODE=REAL
AMD_INFERENCE_ENABLED=true
VLLM_API_BASE=http://<IP_DO_SERVIDOR_AMD>:8000/v1
```
* **Resultado esperado:** O backend passa a processar as imagens via vLLM real na GPU AMD com medição de latência física.
* **Como validar:** Executar `.\.venv\Scripts\python -m pytest backend/tests/test_amd_protocol.py` e disparar requisição pericial real com `curl -X POST "http://127.0.0.1:8000/api/documents/CASE-CTR-020/runs?mode_override=REAL"`.
* **Como desfazer:** No servidor remoto, executar `docker stop cribum-vllm-rocm && docker rm cribum-vllm-rocm` para pausar custos.
