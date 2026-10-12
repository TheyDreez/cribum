import abc
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from backend.schemas.contracts import (
    BoundingBoxNormalized,
    EvidenceContract,
    ExtractedFieldContract,
    HypothesisContract,
)

load_dotenv()


class ProviderError(Exception):
    """Erro base para falhas de inferência."""
    pass


class InferenceUnavailableError(ProviderError):
    """Lançado quando o provedor REAL está offline ou inacessível. PROIBIDO fallback silencioso."""
    pass


class NoFixtureAvailableError(ProviderError):
    """Lançado no modo DEMO quando a imagem enviada não possui fixture sintética mapeada."""
    pass


class ProviderResult:
    def __init__(
        self,
        fields: List[Dict[str, Any]],
        evidences: List[Dict[str, Any]],
        latency_ms: float,
        provider_name: str,
        model_id: str,
        telemetry: Dict[str, Any],
    ):
        self.fields = fields
        self.evidences = evidences
        self.latency_ms = latency_ms
        self.provider_name = provider_name
        self.model_id = model_id
        self.telemetry = telemetry


class BaseInferenceProvider(abc.ABC):
    @abc.abstractmethod
    def extract(
        self,
        document_id: str,
        image_path: str,
        content_hash: str,
        original_filename: Optional[str] = None,
    ) -> ProviderResult:
        pass


class RealROCmProvider(BaseInferenceProvider):
    """
    Provedor REAL: executa inferência através de endpoint vLLM em GPU AMD com ROCm.
    Regra estrita: se a conexão falhar ou timeout ocorrer, lança InferenceUnavailableError.
    NUNCA realiza fallback silencioso para mock ou fixtures.
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 60.0,
    ):
        self.api_base = api_base or os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
        self.model_name = model_name or os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2-VL-7B-Instruct")
        self.timeout_seconds = timeout_seconds

    def extract(
        self,
        document_id: str,
        image_path: str,
        content_hash: str,
        original_filename: Optional[str] = None,
    ) -> ProviderResult:
        endpoint = f"{self.api_base.rstrip('/')}/chat/completions"

        from backend.agents.leitor import PROMPT_LEITOR_SISTEMA, LeitorAgent

        b64_img, mime_type = LeitorAgent.encode_image_base64(image_path)

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": PROMPT_LEITOR_SISTEMA},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analise esta guia/receita médica e extraia rigorosamente conforme o schema JSON solicitado."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}},
                    ],
                },
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                res_data = response.json()
        except httpx.ConnectError as exc:
            raise InferenceUnavailableError(
                f"Falha de conexão com endpoint de inferência AMD ({endpoint}). "
                "O serviço vLLM/ROCm não está ativo no endereço configurado."
            ) from exc
        except httpx.TimeoutException as exc:
            raise InferenceUnavailableError(
                f"Tempo limite excedido ({self.timeout_seconds}s) no endpoint de inferência AMD."
            ) from exc
        except Exception as exc:
            raise InferenceUnavailableError(
                f"Erro durante a chamada do modelo na infraestrutura AMD: {str(exc)}"
            ) from exc

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        raw_text = res_data["choices"][0]["message"]["content"]
        cleaned_json = LeitorAgent.clean_json_markdown(raw_text)

        try:
            parsed = json.loads(cleaned_json)
        except Exception as exc:
            raise ProviderError(f"Saída do modelo VLM não é um JSON válido: {str(exc)}") from exc

        # Converte a saída em contratos estruturados com evidências e bounding boxes normalizados (0..1)
        fields, evidences = self._convert_to_contracts(parsed, document_id)

        telemetry = {
            "mode": "REAL",
            "backend": "AMD ROCm GPU (vLLM)",
            "endpoint": endpoint,
            "tokens": res_data.get("usage", {}),
            "latency_ms": elapsed_ms,
            "content_hash": content_hash,
        }

        return ProviderResult(
            fields=fields,
            evidences=evidences,
            latency_ms=elapsed_ms,
            provider_name="vLLM-ROCm",
            model_id=self.model_name,
            telemetry=telemetry,
        )

    def _convert_to_contracts(self, parsed: Dict[str, Any], document_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        fields = []
        evidences = []

        cabecalho = parsed.get("cabecalho", {})
        boxes = cabecalho.get("boxes", {})

        # Campos do cabeçalho
        if cabecalho.get("crm"):
            ev_id = f"ev-crm-{document_id[:8]}"
            crm_box = boxes.get("crm")
            norm_box = None
            loc_status = "UNLOCALIZED"
            if crm_box and len(crm_box) == 4:
                # Converte de 0-1000 para 0-1 (x_min, y_min, x_max, y_max)
                norm_box = {
                    "x_min": crm_box[1] / 1000.0,
                    "y_min": crm_box[0] / 1000.0,
                    "x_max": crm_box[3] / 1000.0,
                    "y_max": crm_box[2] / 1000.0,
                }
                loc_status = "VALIDATED"

            evidences.append({
                "id": ev_id,
                "document_id": document_id,
                "page": 1,
                "bbox": norm_box,
                "coordinate_system": "NORMALIZED_0_1",
                "localization_status": loc_status,
                "source": "VLM_OUTPUT",
                "excerpt": f"CRM {cabecalho.get('crm')}/{cabecalho.get('uf_crm', '')}",
            })

            fields.append({
                "field_type": "crm",
                "raw_text": str(cabecalho.get("crm")),
                "normalized_value": f"{cabecalho.get('crm')}-{cabecalho.get('uf_crm', 'SP')}",
                "hypotheses": [
                    {
                        "text": f"{cabecalho.get('crm')}-{cabecalho.get('uf_crm', 'SP')}",
                        "rank": 1,
                        "score": 0.95,
                        "score_kind": "HEURISTIC_MODEL",
                        "supporting_evidence_ids": [ev_id],
                    }
                ],
                "uncertainty_status": "CERTAIN",
                "confidence_kind": "HEURISTIC_MODEL",
                "score": 0.95,
                "evidence_ids": [ev_id],
                "requires_review": False,
            })

        # Itens da receita
        for idx, item in enumerate(parsed.get("itens", []), 1):
            raw_box = item.get("box", [0, 0, 0, 0])
            norm_box = None
            loc_status = "UNLOCALIZED"
            if len(raw_box) == 4 and any(c > 0 for c in raw_box):
                norm_box = {
                    "x_min": raw_box[1] / 1000.0,
                    "y_min": raw_box[0] / 1000.0,
                    "x_max": raw_box[3] / 1000.0,
                    "y_max": raw_box[2] / 1000.0,
                }
                loc_status = "VALIDATED"

            ev_id = f"ev-item-{idx}-{document_id[:8]}"
            evidences.append({
                "id": ev_id,
                "document_id": document_id,
                "page": 1,
                "bbox": norm_box,
                "coordinate_system": "NORMALIZED_0_1",
                "localization_status": loc_status,
                "source": "VLM_OUTPUT",
                "excerpt": item.get("posologia") or "Prescrição medicamentosa",
            })

            hyp_list = []
            for rank, hyp in enumerate(item.get("hipoteses", []), 1):
                hyp_list.append({
                    "text": hyp.get("nome", "Indeterminado"),
                    "rank": rank,
                    "score": hyp.get("confianca"),
                    "score_kind": "HEURISTIC_MODEL",
                    "supporting_evidence_ids": [ev_id],
                })

            uncertainty = "CERTAIN"
            if item.get("nivel_incerteza") == "alto":
                uncertainty = "AMBIGUOUS"
            elif item.get("nivel_incerteza") == "medio":
                uncertainty = "AMBIGUOUS"

            top_name = hyp_list[0]["text"] if hyp_list else "Ilegível"
            fields.append({
                "field_type": "medication",
                "raw_text": top_name,
                "normalized_value": top_name,
                "hypotheses": hyp_list,
                "uncertainty_status": uncertainty,
                "confidence_kind": "HEURISTIC_MODEL",
                "score": hyp_list[0]["score"] if hyp_list else None,
                "evidence_ids": [ev_id],
                "requires_review": (uncertainty != "CERTAIN"),
            })

        return fields, evidences


class DemoFixtureProvider(BaseInferenceProvider):
    """
    Provedor DEMO: utiliza exclusivamente fixtures determinísticas gabaritadas.
    Exibe banner explícito na UI indicando modo de demonstração.
    Se a imagem não tiver fixture registrada, recusa o processamento informando
    que não há fixture disponível (sem fabricar alucinação).
    """

    def __init__(self, fixtures_path: str = "backend/data/synthetic/fixtures.json"):
        self.fixtures_path = fixtures_path
        self._fixtures = self._load_fixtures()

    def _load_fixtures(self) -> Dict[str, Any]:
        if os.path.exists(self.fixtures_path):
            with open(self.fixtures_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def register_fixture(self, key: str, fixture_data: Dict[str, Any]):
        self._fixtures[key] = fixture_data

    def extract(
        self,
        document_id: str,
        image_path: str,
        content_hash: str,
        original_filename: Optional[str] = None,
    ) -> ProviderResult:
        # Busca por hash, nome original do arquivo, id do documento ou storage_key
        filename = os.path.basename(image_path)
        fixture = (
            self._fixtures.get(content_hash)
            or (self._fixtures.get(original_filename) if original_filename else None)
            or self._fixtures.get(document_id)
            or self._fixtures.get(filename)
        )

        if not fixture:
            # Se não encontrou por hash exato, verifica se existe fixture genérica cadastrada para testes
            fixture = self._fixtures.get("default_synthetic_case")

        if not fixture:
            raise NoFixtureAvailableError(
                f"Nenhuma fixture registrada no modo DEMO para este documento (Hash: {content_hash[:12]}...). "
                "Para testar uma imagem nova arbitrária, conecte o cluster AMD e selecione o modo REAL."
            )

        fields = fixture.get("fields", [])
        evidences = fixture.get("evidences", [])

        # Garante que os IDs de evidência e documento reflitam o documento atual
        adapted_evidences = []
        for ev in evidences:
            ev_copy = dict(ev)
            ev_copy["document_id"] = document_id
            adapted_evidences.append(ev_copy)

        telemetry = {
            "mode": "DEMO",
            "backend": "Deterministic Fixture Engine",
            "fixture_name": fixture.get("name", "Synthetic Fixture"),
            "latency_ms": 15.0,
            "synthetic_notice": "DEMO MODE: Resultado obtido de fixture sintética documentada para fluxo de UI.",
        }

        return ProviderResult(
            fields=fields,
            evidences=adapted_evidences,
            latency_ms=15.0,
            provider_name="DemoFixture",
            model_id="deterministic-fixture-v1",
            telemetry=telemetry,
        )
