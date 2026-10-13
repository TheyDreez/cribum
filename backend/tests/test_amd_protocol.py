import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

from backend.services.provider import (
    RealROCmProvider,
    InferenceUnavailableError,
    ProviderError,
)


class FakeVLLMServerHandler(BaseHTTPRequestHandler):
    """
    Servidor HTTP de teste explicitamente identificado como FAKE para validar
    o protocolo OpenAI Chat Completions esperado pelo adaptador RealROCmProvider.
    NÃO representa inferência em hardware real nem executa tensores em GPU.
    """

    response_scenario = "NORMAL"

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)

            # Valida estrutura mínima do payload esperado pelo vLLM
            assert "messages" in payload
            assert payload.get("model") == "Qwen/Qwen2-VL-7B-Instruct"

            if self.response_scenario == "NORMAL":
                vlm_content = json.dumps({
                    "cabecalho": {"crm": "98765", "uf_crm": "SP", "boxes": {"crm": [0.1, 0.1, 0.4, 0.2]}},
                    "itens": [
                        {
                            "posologia": "1 comprimido ao dia",
                            "box": [0.2, 0.3, 0.8, 0.4],
                            "nivel_incerteza": "baixo",
                            "hipoteses": [{"nome": "Atenolol 50mg", "confianca": 0.92}]
                        }
                    ]
                })
                resp_data = {
                    "id": "chatcmpl-test-fake",
                    "object": "chat.completion",
                    "model": "Qwen/Qwen2-VL-7B-Instruct",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": vlm_content},
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode("utf-8"))

            elif self.response_scenario == "EMPTY_ITEMS":
                vlm_content = json.dumps({
                    "cabecalho": {"crm": "12345", "uf_crm": "SP"},
                    "itens": [
                        {
                            "posologia": "",
                            "box": None,
                            "nivel_incerteza": "indeterminado",
                            "hipoteses": []
                        }
                    ]
                })
                resp_data = {
                    "id": "chatcmpl-test-empty",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": vlm_content}}],
                    "usage": {"total_tokens": 50}
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode("utf-8"))

            elif self.response_scenario == "MALFORMED_JSON":
                resp_data = {
                    "id": "chatcmpl-test-broken",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Não consegui ler a imagem [INVALID_JSON"}}],
                    "usage": {"total_tokens": 10}
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode("utf-8"))
            else:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suprime logs de acesso HTTP durante testes
        pass


@pytest.fixture(scope="module")
def fake_vllm_server():
    server = HTTPServer(("127.0.0.1", 0), FakeVLLMServerHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/v1"
    server.shutdown()


def test_real_provider_protocol_compliance_with_fake_server(fake_vllm_server):
    """
    Testa o protocolo cliente/servidor do adaptador RealROCmProvider
    contra um servidor de teste simulando a API OpenAI do vLLM.
    """
    FakeVLLMServerHandler.response_scenario = "NORMAL"
    provider = RealROCmProvider(api_base=fake_vllm_server, timeout_seconds=5.0)

    # Usa uma imagem sintética válida existente
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    result = provider.extract(
        document_id="doc-test-protocol",
        image_path=img_path,
        content_hash="test-hash-12345",
        original_filename="caso_01_losartana_lorazepam.jpg"
    )

    assert result.provider_name == "vLLM-ROCm"
    assert result.model_id == "Qwen/Qwen2-VL-7B-Instruct"
    assert result.latency_ms > 0
    assert len(result.fields) >= 2  # CRM e Medicamento
    assert len(result.evidences) >= 1

    # Verifica telemetria estruturada sem expor segredos
    assert "detected_hardware" in result.telemetry
    assert "latency_ms" in result.telemetry
    assert result.telemetry["mode"] == "REAL"


def test_real_provider_handles_empty_vlm_output_as_indeterminate(fake_vllm_server):
    """
    Verifica se itens vazios ou sem hipóteses geram status INDETERMINATE e exigem revisão.
    """
    FakeVLLMServerHandler.response_scenario = "EMPTY_ITEMS"
    provider = RealROCmProvider(api_base=fake_vllm_server, timeout_seconds=5.0)

    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    result = provider.extract(
        document_id="doc-test-empty",
        image_path=img_path,
        content_hash="test-hash-empty"
    )

    med_field = next(f for f in result.fields if f["field_type"] == "medication")
    assert med_field["uncertainty_status"] == "INDETERMINATE"
    assert med_field["requires_review"] is True
    assert med_field["score"] is None


def test_real_provider_handles_malformed_json_gracefully(fake_vllm_server):
    """
    Verifica que saídas do VLM que não sejam JSON válido disparam ProviderError explicitamente.
    """
    FakeVLLMServerHandler.response_scenario = "MALFORMED_JSON"
    provider = RealROCmProvider(api_base=fake_vllm_server, timeout_seconds=5.0)

    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with pytest.raises(ProviderError) as exc_info:
        provider.extract(
            document_id="doc-test-malformed",
            image_path=img_path,
            content_hash="test-hash-malformed"
        )
    assert "JSON válido" in str(exc_info.value)


def test_real_provider_offline_endpoint_raises_unavailable_error():
    """
    Verifica que um endpoint offline/inexistente gera InferenceUnavailableError
    e nunca realiza fallback silencioso para DEMO.
    """
    # Porta aleatória não mapeada
    offline_provider = RealROCmProvider(api_base="http://127.0.0.1:59999/v1", timeout_seconds=1.0)
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"

    with pytest.raises(InferenceUnavailableError) as exc_info:
        offline_provider.extract(
            document_id="doc-test-offline",
            image_path=img_path,
            content_hash="test-hash-offline"
        )
    assert any(m in str(exc_info.value) for m in ("Falha de conexão", "Tempo limite", "inferência AMD"))
