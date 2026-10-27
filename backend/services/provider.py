import abc
from functools import lru_cache
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


def validate_bounding_box(raw_box: Any) -> Tuple[Optional[Dict[str, float]], str]:
    """
    Valida rigorosamente a geometria da bounding box:
    - Requer exatamente 4 números.
    - Se todos forem 0, indica ausência de localização ('UNLOCALIZED').
    - Converte escala 0-1000 (do VLM) para escala normalizada [0.0, 1.0].
    - Valida que todos os valores estão em [0.0, 1.0].
    - Valida que x_max > x_min e y_max > y_min com área mínima de 0.0001.
    - Retorna status 'PROPOSED_BY_MODEL' (não 'VALIDATED', pois a localização
      visual ainda requer conferência humana ou ground truth).
    """
    if not raw_box or not isinstance(raw_box, (list, tuple)) or len(raw_box) != 4:
        return None, "UNLOCALIZED"

    try:
        coords = [float(c) for c in raw_box]
    except (ValueError, TypeError):
        return None, "INVALID_GEOMETRY"

    if all(c == 0.0 for c in coords):
        return None, "UNLOCALIZED"

    y_min_raw, x_min_raw, y_max_raw, x_max_raw = coords

    if any(c > 1.0 for c in coords):
        x_min = round(x_min_raw / 1000.0, 4)
        y_min = round(y_min_raw / 1000.0, 4)
        x_max = round(x_max_raw / 1000.0, 4)
        y_max = round(y_max_raw / 1000.0, 4)
    else:
        x_min, y_min, x_max, y_max = round(x_min_raw, 4), round(y_min_raw, 4), round(x_max_raw, 4), round(y_max_raw, 4)

    for val in (x_min, y_min, x_max, y_max):
        if val < 0.0 or val > 1.0:
            return None, "INVALID_GEOMETRY"

    if x_max <= x_min or y_max <= y_min:
        return None, "INVALID_GEOMETRY"

    area = (x_max - x_min) * (y_max - y_min)
    if area < 0.0001:
        return None, "INVALID_GEOMETRY"

    return {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
    }, "PROPOSED_BY_MODEL"


def inspect_runtime_hardware() -> str:
    """Verifica dinamicamente a presença de GPU / ROCm sem assumir hardware fixo."""
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            hip_ver = getattr(torch.version, "hip", None)
            if hip_ver:
                return f"AMD ROCm GPU: {dev_name} (HIP {hip_ver})"
            return f"GPU: {dev_name} (CUDA/Direct)"
        return "CPU Local (ROCm não detectado no host atual)"
    except ImportError:
        return "Python Runtime (PyTorch não instalado no ambiente)"


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
            "backend": f"vLLM Endpoint ({self.api_base})",
            "detected_hardware": inspect_runtime_hardware(),
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
            raw_crm = str(cabecalho.get("crm")).strip()
            uf = str(cabecalho.get("uf_crm", "SP")).strip()
            ev_id = f"ev-crm-{document_id[:8]}"
            crm_box = boxes.get("crm")
            norm_box, loc_status = validate_bounding_box(crm_box)

            evidences.append({
                "id": ev_id,
                "document_id": document_id,
                "page": 1,
                "bbox": norm_box,
                "coordinate_system": "NORMALIZED_0_1",
                "localization_status": loc_status,
                "source": "VLM_OUTPUT",
                "excerpt": f"CRM {raw_crm}/{uf}",
            })

            is_valid_digits = raw_crm.replace(".", "").replace("-", "").isdigit()
            uncertainty = "CERTAIN" if is_valid_digits and len(raw_crm) >= 4 else "AMBIGUOUS"

            fields.append({
                "field_type": "crm",
                "raw_text": raw_crm,
                "normalized_value": f"{raw_crm}-{uf}",
                "hypotheses": [
                    {
                        "text": f"{raw_crm}-{uf}",
                        "rank": 1,
                        "score": None,  # Sem probabilidade inventada
                        "score_kind": "HEURISTIC_MODEL",
                        "supporting_evidence_ids": [ev_id] if norm_box else [],
                    }
                ],
                "uncertainty_status": uncertainty,
                "confidence_kind": "HEURISTIC_MODEL",
                "score": None,  # Nulo na ausência de calibração estatística
                "evidence_ids": [ev_id] if norm_box else [],
                "requires_review": (uncertainty != "CERTAIN"),
            })

        # Extração do CID-10 do cabeçalho para alimentar a Correlação Clínica no modo REAL
        if cabecalho.get("diagnostico_cid"):
            raw_cid = str(cabecalho.get("diagnostico_cid")).strip().upper()
            fields.append({
                "field_type": "cid",
                "raw_text": raw_cid,
                "normalized_value": raw_cid,
                "hypotheses": [
                    {
                        "text": raw_cid,
                        "rank": 1,
                        "score": None,
                        "score_kind": "HEURISTIC_MODEL",
                        "supporting_evidence_ids": [],
                    }
                ],
                "uncertainty_status": "CERTAIN",
                "confidence_kind": "HEURISTIC_MODEL",
                "score": None,
                "evidence_ids": [],
                "requires_review": False,
            })

        # Itens da receita
        for idx, item in enumerate(parsed.get("itens", []), 1):
            raw_box = item.get("box")
            norm_box, loc_status = validate_bounding_box(raw_box)

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
                    "supporting_evidence_ids": [ev_id] if norm_box else [],
                })

            uncertainty = "CERTAIN"
            if item.get("nivel_incerteza") in ("alto", "medio"):
                uncertainty = "AMBIGUOUS"
            elif item.get("nivel_incerteza") in ("indeterminado", "vazio", "ilegivel") or not hyp_list:
                uncertainty = "INDETERMINATE"

            top_name = hyp_list[0]["text"] if hyp_list else "Ilegível"
            if top_name in ("Ilegível", "Indeterminado", "") or not hyp_list:
                uncertainty = "INDETERMINATE"

            fields.append({
                "field_type": "medication",
                "raw_text": top_name,
                "normalized_value": top_name if uncertainty != "INDETERMINATE" else None,
                "hypotheses": hyp_list,
                "uncertainty_status": uncertainty,
                "confidence_kind": "HEURISTIC_MODEL",
                "score": hyp_list[0]["score"] if (hyp_list and uncertainty != "INDETERMINATE") else None,
                "evidence_ids": [ev_id] if norm_box else [],
                "requires_review": (uncertainty != "CERTAIN"),
            })

        return fields, evidences


@lru_cache(maxsize=32)
def _load_fixtures_from_disk(fixtures_path: str) -> Dict[str, Any]:
    if os.path.exists(fixtures_path):
        with open(fixtures_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class DemoFixtureProvider(BaseInferenceProvider):
    """
    Provedor DEMO: utiliza exclusivamente fixtures determinísticas gabaritadas.
    Exibe banner explícito na UI indicando modo de demonstração.
    VINCULA FIXTURES EXCLUSIVAMENTE AO HASH DE CONTEÚDO (SHA-256) OU AO ID
    DO CASO PRÉ-SEMEADO. NUNCA UTILIZA NOME DE ARQUIVO NEM FALLBACK GENÉRICO.
    """

    def __init__(self, fixtures_path: str = "backend/data/synthetic/fixtures.json"):
        self.fixtures_path = fixtures_path
        self._fixtures = dict(self._load_fixtures())

    def _load_fixtures(self, reload: bool = False) -> Dict[str, Any]:
        if reload:
            _load_fixtures_from_disk.cache_clear()
        return _load_fixtures_from_disk(self.fixtures_path)

    def register_fixture(self, key: str, fixture_data: Dict[str, Any]):
        self._fixtures[key] = fixture_data

    def extract(
        self,
        document_id: str,
        image_path: str,
        content_hash: str,
        original_filename: Optional[str] = None,
    ) -> ProviderResult:
        # Busca exclusivamente por content_hash (SHA-256) ou document_id conhecido
        fixture = self._fixtures.get(content_hash) or self._fixtures.get(document_id)

        if not fixture:
            raise NoFixtureAvailableError(
                f"Nenhuma fixture registrada no modo DEMO para o hash SHA-256 {content_hash}. "
                "No modo DEMO, apenas imagens sintéticas do catálogo gabaritado são aceitas. "
                "Para processar novas imagens arbitrárias, selecione o modo REAL com endpoint vLLM/ROCm ativo."
            )

        fields = fixture.get("fields", [])
        evidences = fixture.get("evidences", [])

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

