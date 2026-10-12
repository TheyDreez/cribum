# GUIA DE CONFIGURAÇÃO DE INFRAESTRUTURA AMD (ROCm & vLLM)

Este documento descreve os passos exatos para provisionar e validar a inferência com modelos visuais abertos em GPUs AMD via ROCm.

---

## 1. Pré-Requisitos de Hardware e Driver

* **Acelerador Recomendado:** AMD Instinct MI300X, MI250 ou GPUs Radeon compatíveis com ROCm 6.1+.
* **Driver do Host:** AMD GPU driver instalado com suporte a KFD (`amdgpu-install`).
* **Permissões do Usuário:** Usuário pertencente aos grupos `video` e `render`.

Verifique se a GPU AMD é reconhecida no terminal:
```bash
rocm-smi
```

---

## 2. Inicialização do Contêiner vLLM com Suporte a ROCm

Execute o contêiner oficial otimizado da AMD:

```bash
docker run -d --name cribum-vllm-rocm \
  --network=host \
  --ipc=host \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --shm-size 16G \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  rocm/vllm:latest \
  python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --trust-remote-code \
  --port 8000
```

---

## 3. Smoke Test de Conectividade do Modelo

Valide se o endpoint OpenAI-compatible está respondendo:

```bash
curl http://localhost:8000/v1/models
```

Resposta esperada:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2-VL-7B-Instruct",
      "object": "model",
      "owned_by": "vllm"
    }
  ]
}
```

---

## 4. Configuração no CRIBUM para Ativar Modo REAL

No arquivo `.env` na raiz do projeto:

```ini
EXECUTION_MODE=REAL
AMD_INFERENCE_ENABLED=true
VLLM_API_BASE=http://localhost:8000/v1
VLLM_MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
```

Para testar a inferência no pipeline:
```bash
.venv/Scripts/python backend/tests/test_leitor.py
```

---

## 5. Como Encerrar Recursos e Evitar Gastos Desnecessários

Ao finalizar os testes ou benchmark na nuvem:
```bash
docker stop cribum-vllm-rocm
docker rm cribum-vllm-rocm
```
Se estiver utilizando instância alugada na nuvem (Crusoe, Lambda, TensorDock ou AMD Developer Cloud), certifique-se de pausar ou destruir a máquina para não consumir créditos ociosos.
