import base64
import hashlib
import json
import mimetypes
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

from backend.schemas.claim import HeaderData, ItemHypothesis, PrescriptionItem

load_dotenv()

PROMPT_LEITOR_SISTEMA = """Você é o AGENTE LEITOR do CRIBUM, um sistema especialista em auditoria pericial de receitas médicas e guias de convênio.
Sua missão é extrair dados textuais e estruturados de imagens médicas manuscritas ou impressas.

REGRAS DE OURO INEGOCIÁVEIS:
1. NUNCA invente medicamentos ou adivinhe com certeza absoluta se a caligrafia for ambígua.
2. Para cada medicamento/procedimento prescrito:
   - Forneça SEMPRE até 3 hipóteses de leitura (ordenadas da mais provável para a menos provável).
   - Ordene as hipóteses por plausibilidade visual (1ª mais provável, 2ª, 3ª). Não invente precisão estatística ou scores decimais arbitrários se o texto for ilegível.
   - Se houver dúvida visual razoável (caligrafia corrida, ilegível ou rasurada), marque 'nivel_incerteza': 'alto' ou 'medio' e explique a dúvida em 'justificativa_leitura'.

3. ANCORAGEM VISUAL (BOUNDING BOXES):
   - Cada item DEVE conter sua coordenada exata normalizada na imagem: [ymin, xmin, ymax, xmax] em escala de 0 a 1000.
   - Exemplo: [450, 120, 520, 850] representa a faixa horizontal onde o remédio foi escrito.
4. CABEÇALHO:
   - Extraia CRM, UF, data de emissão (YYYY-MM-DD), nome do paciente, clínica/hospital e CID-10 (se visível).

RESPONDA EXCLUSIVAMENTE UM OBJETO JSON VÁLIDO SEGUINDO ESTE SCHEMA EXATO:
{
  "cabecalho": {
    "crm": "string ou null",
    "uf_crm": "string ou null",
    "data_emissao": "YYYY-MM-DD ou null",
    "paciente_nome": "string ou null",
    "paciente_cpf": "string ou null",
    "clinica_nome": "string ou null",
    "clinica_cnpj": "string ou null",
    "diagnostico_cid": "string ou null",
    "boxes": {
      "crm": [0, 0, 0, 0],
      "data": [0, 0, 0, 0]
    }
  },
  "itens": [
    {
      "id": "item_1",
      "box": [ymin, xmin, ymax, xmax],
      "hipoteses": [
        {"nome": "Hipótese mais provável", "confianca": 0.70},
        {"nome": "Segunda hipótese plausível", "confianca": 0.20},
        {"nome": "Terceira hipótese plausível", "confianca": 0.10}
      ],
      "posologia": "Dose, frequência e duração extraída",
      "nivel_incerteza": "baixo|medio|alto",
      "justificativa_leitura": "Análise da caligrafia e motivo das hipóteses"
    }
  ]
}
"""


class LeitorAgent:
    """
    Agente Leitor responsável pela extração multimodal de receitas e guias médicas.
    Conecta-se ao servidor vLLM servindo modelos visuais abertos (ex: Qwen2-VL)
    acelerados por GPUs AMD via ROCm.
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
    ):
        self.api_base = api_base or os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
        self.model_name = model_name or os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2-VL-7B-Instruct")
        self.timeout = timeout

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Gera hash SHA-256 para rastreabilidade pericial e verificação de integridade da imagem."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def encode_image_base64(file_path: str) -> Tuple[str, str]:
        """Converte imagem local para string base64 e detecta o tipo MIME."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg"

        with open(file_path, "rb") as f:
            b64_content = base64.b64encode(f.read()).decode("utf-8")
        return b64_content, mime_type

    @staticmethod
    def clean_json_markdown(raw_text: str) -> str:
        """Remove blocos markdown ```json ... ``` caso o modelo os inclua."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def processar_guia(
        self,
        image_path: str,
        allow_mock_fallback: bool = True,
    ) -> Tuple[HeaderData, List[PrescriptionItem], Dict[str, Any]]:
        """
        Executa a extração completa da guia médica.

        Retorna:
            - HeaderData: dados estruturados do cabeçalho
            - List[PrescriptionItem]: lista de itens com as 3 hipóteses e boxes
            - Dict[str, Any]: métricas de telemetria da GPU AMD (latência ms, tokens, etc.)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")

        file_sha256 = self.compute_sha256(image_path)
        b64_img, mime_type = self.encode_image_base64(image_path)

        endpoint = f"{self.api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": PROMPT_LEITOR_SISTEMA,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analise esta guia/receita médica e extraia rigorosamente conforme o schema JSON solicitado.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
                        },
                    ],
                },
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        start_time = time.perf_counter()
        telemetria: Dict[str, Any] = {
            "documento_sha256": file_sha256,
            "modelo": self.model_name,
            "endpoint": endpoint,
            "backend_hardware": "AMD ROCm GPU",
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            res_json = response.json()
            usage = res_json.get("usage", {})
            raw_content = res_json["choices"][0]["message"]["content"]

            telemetria.update(
                {
                    "tempo_inferencia_ms": elapsed_ms,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "status_chamada": "sucesso_vllm_rocm",
                }
            )

            cleaned_json_str = self.clean_json_markdown(raw_content)
            parsed_data = json.loads(cleaned_json_str)

        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if not allow_mock_fallback:
                raise RuntimeError(f"Falha na inferência VLM no ROCm: {str(exc)}") from exc

            # Modo de contingência e desenvolvimento offline
            telemetria.update(
                {
                    "tempo_inferencia_ms": elapsed_ms,
                    "status_chamada": f"mock_fallback (vLLM offline: {type(exc).__name__})",
                    "aviso": "Inferência gerada via pipeline de simulação estruturada para testes",
                }
            )
            parsed_data = self._gerar_mock_extracao()

        # Validação estrita via Pydantic
        cabecalho = HeaderData(**parsed_data.get("cabecalho", {}))
        itens = [PrescriptionItem(**item) for item in parsed_data.get("itens", [])]

        return cabecalho, itens, telemetria

    def _gerar_mock_extracao(self) -> Dict[str, Any]:
        """Gera dados simulados realistas para testes de pipeline quando o cluster AMD estiver offline."""
        return {
            "cabecalho": {
                "crm": "142857",
                "uf_crm": "SP",
                "data_emissao": "2026-10-12",
                "paciente_nome": "Carlos Eduardo Silveira",
                "paciente_cpf": "123.456.789-00",
                "clinica_nome": "Centro Médico Sorocaba",
                "clinica_cnpj": "12.345.678/0001-90",
                "diagnostico_cid": "I10",
                "boxes": {
                    "crm": [80, 710, 110, 890],
                    "data": [80, 120, 110, 310],
                },
            },
            "itens": [
                {
                    "id": "item_1",
                    "box": [320, 110, 410, 890],
                    "hipoteses": [
                        {"nome": "Losartana Potássica 50mg", "confianca": 0.65},
                        {"nome": "Lorazepam 2mg", "confianca": 0.25},
                        {"nome": "Levotiroxina 50mcg", "confianca": 0.10},
                    ],
                    "posologia": "Tomar 1 comprimido pela manhã em jejum",
                    "nivel_incerteza": "alto",
                    "justificativa_leitura": (
                        "Grafia cursiva com traçado inicial ambíguo entre 'Los' e 'Lor'. "
                        "Terminação em 'ana' levemente truncada, gerando sobreposição com 'epam'."
                    ),
                },
                {
                    "id": "item_2",
                    "box": [440, 110, 520, 890],
                    "hipoteses": [
                        {"nome": "Hidroclorotiazida 25mg", "confianca": 0.95},
                        {"nome": "Hidroxicloroquina 400mg", "confianca": 0.05},
                    ],
                    "posologia": "1 comprimido ao dia após o café",
                    "nivel_incerteza": "baixo",
                    "justificativa_leitura": "Caligrafia clara e dosagem compatível com diurético tiazídico.",
                },
            ],
        }
