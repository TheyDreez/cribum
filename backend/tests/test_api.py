import io
import os
import sys
from PIL import Image
import pytest
from fastapi.testclient import TestClient

# Garante raiz no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.api.app import app, get_db
from backend.models.database import Base, get_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configura banco de dados em memória compartilhado para os testes
test_engine = get_engine("sqlite://")
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_test_image_bytes(width: int = 400, height: int = 500, format: str = "JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_health_and_config():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_cfg = client.get("/api/config")
    assert res_cfg.status_code == 200
    cfg = res_cfg.json()
    assert "execution_mode" in cfg
    assert cfg["execution_mode"] in ("DEMO", "REAL")


def test_upload_valid_image():
    img_bytes = create_test_image_bytes(300, 400, "PNG")
    files = {"file": ("receita_teste.png", img_bytes, "image/png")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename_original"] == "receita_teste.png"
    assert len(data["content_hash"]) == 64
    assert data["width"] == 300
    assert data["height"] == 400


def test_upload_corrupted_file_rejected():
    fake_bytes = b"ESTE_NAO_E_UM_ARQUIVO_DE_IMAGEM_VALIDO"
    files = {"file": ("malicioso.jpg", fake_bytes, "image/jpeg")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 400
    assert "não é uma imagem válida" in response.json()["detail"]


def test_processing_run_demo_mode():
    # 1. Carrega um caso sintético documentado (caso_01_losartana_lorazepam.jpg)
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    assert os.path.exists(img_path), "Gere o dataset sintético antes de executar os testes."

    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}

    upload_res = client.post("/api/documents", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. Executa processamento em modo DEMO explícito
    run_res = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["mode"] == "DEMO"
    assert run_data["status"] == "REVIEW_REQUIRED"

    # 3. Consulta os detalhes do documento e valida que as hipóteses e alertas foram criados
    doc_details = client.get(f"/api/documents/{doc_id}").json()
    assert len(doc_details["fields"]) >= 1
    med_field = next(f for f in doc_details["fields"] if f["field_type"] == "medication")
    assert med_field["uncertainty_status"] == "AMBIGUOUS"
    assert len(med_field["hypotheses"]) >= 2

    # Verifica que achou o alerta de risco LASA
    findings = doc_details["findings"]
    assert any("LASA" in fn["category"] or "LASA" in fn["rule_id"] for fn in findings)


def test_real_provider_fails_explicitly_without_silent_fallback():
    # Cria documento
    img_bytes = create_test_image_bytes(200, 200)
    files = {"file": ("doc_real_test.jpg", img_bytes, "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]

    # Força modo REAL quando o servidor vLLM local em localhost:8000 não está ativo
    # Deve retornar HTTP 503 com erro explícito INFERENCE_UNAVAILABLE (NUNCA fazer fallback para DEMO)
    run_res = client.post(f"/api/documents/{doc_id}/runs?mode_override=REAL")
    assert run_res.status_code == 503
    err = run_res.json()["detail"]
    assert err["error"] == "INFERENCE_UNAVAILABLE"


def test_human_review_decision_persisted():
    # Cria documento e executa run em demo
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]
    client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")

    # Auditor humano confere e envia decisão
    review_payload = {
        "action": "CONFIRMED_HYPOTHESIS",
        "actor_id": "auditor-andre-01",
        "previous_value": "Losartana 50mg / Lorazepam 2mg (ambíguo)",
        "confirmed_value": "Losartana 50mg",
        "reason": "Conferido visualmente pelo auditor: o diagnóstico de hipertensão (I10) e a posologia matinal em jejum confirmam Losartana."
    }

    res_review = client.post(f"/api/documents/{doc_id}/reviews", json=review_payload)
    assert res_review.status_code == 201
    dec = res_review.json()
    assert dec["confirmed_value"] == "Losartana 50mg"
    assert dec["actor_id"] == "auditor-andre-01"

    # Confere persistência ao reconsultar o documento
    doc_after = client.get(f"/api/documents/{doc_id}").json()
    assert len(doc_after["decisions"]) >= 1
    assert doc_after["decisions"][0]["confirmed_value"] == "Losartana 50mg"
    # CONFIRMED_HYPOTHESIS não rejeita o documento: coloca em IN_REVIEW
    assert doc_after["document"]["review_status"] == "IN_REVIEW"

    # Agora submete aprovação final da guia
    approve_res = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "APPROVED_CLAIM",
            "actor_id": "auditor-chefe",
            "reason": "Todas as pendências sanadas pelo auditor.",
        },
    )
    assert approve_res.status_code == 201
    doc_approved = client.get(f"/api/documents/{doc_id}").json()
    assert doc_approved["document"]["review_status"] == "APPROVED"


def test_unknown_image_rejected_in_demo_mode_without_fallback():
    # Cria uma imagem arbitrária que NÃO pertence ao catálogo de 20 casos sintéticos
    img_bytes = create_test_image_bytes(250, 250, "JPEG")
    # Mesmo se o atacante passar o nome de um caso conhecido, o hash SHA-256 não coincidirá
    files = {"file": ("caso_01_losartana_lorazepam.jpg", img_bytes, "image/jpeg")}
    doc_res = client.post("/api/documents", files=files)
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # Tentativa de rodar em modo DEMO deve falhar com NO_FIXTURE_AVAILABLE
    # Provando que o sistema NÃO confia em nomes de arquivos e NÃO usa fallback genérico
    run_res = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")
    assert run_res.status_code == 400
    err = run_res.json()["detail"]
    assert err["error"] == "NO_FIXTURE_AVAILABLE"


def test_upload_file_too_large_returns_413():
    # Gera buffer ligeiramente acima de 10MB (10MB + 128KB)
    large_bytes = b"0" * (10 * 1024 * 1024 + 128 * 1024)
    files = {"file": ("arquivo_gigante.jpg", large_bytes, "image/jpeg")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 413
    assert "limite máximo permitido" in response.json()["detail"]


def test_graph_endpoint():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "anomalies" in data
    assert data["total_claims"] == 200
    assert len(data["anomalies"]) >= 1


def test_rules_engine_severity_mapping_and_indeterminate_handling():
    from backend.models.database import DocumentModel, ExtractedFieldModel
    from backend.schemas.contracts import FindingContract
    from backend.services.rules_engine import RulesEngine
    from backend.services.provider import RealROCmProvider

    engine = RulesEngine()
    doc = DocumentModel(id="test-doc-indet", filename_original="test.jpg", content_hash="hash123", media_type="image/jpeg", width=100, height=100)

    # 1. Campo ilegível / indeterminado
    f_indet = ExtractedFieldModel(
        id="f1",
        run_id="run1",
        field_type="medication",
        raw_text="Ilegível",
        hypotheses=[],
        uncertainty_status="INDETERMINATE",
        confidence_kind="HEURISTIC_MODEL",
        requires_review=True,
    )
    findings = engine.evaluate(document=doc, run_id="run1", fields=[f_indet])
    indet_finding = next((fn for fn in findings if fn.rule_id == "MED-003-INDETERMINATE-READING"), None)
    assert indet_finding is not None
    assert indet_finding.severity == "HIGH"
    assert indet_finding.requires_review is True

    # 2. Valida conformidade estrita com o FindingContract Pydantic (sem crash de ValidationError)
    contract = FindingContract(
        id="fn-1",
        document_id=doc.id,
        run_id="run1",
        category=indet_finding.category,
        severity=indet_finding.severity,
        rule_id=indet_finding.rule_id,
        rule_version=indet_finding.rule_version,
        title=indet_finding.title,
        explanation=indet_finding.explanation,
        evidence_ids=[],
        related_document_ids=[],
        limitations=indet_finding.limitations,
        requires_review=indet_finding.requires_review,
    )
    assert contract.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # 3. Teste do RealROCmProvider convertendo item vazio para INDETERMINATE
    provider = RealROCmProvider()
    parsed_output = {
        "cabecalho": {"crm": "12345", "uf_crm": "SP"},
        "itens": [
            {"posologia": "1x ao dia", "hipoteses": [], "nivel_incerteza": "indeterminado"}
        ]
    }
    fields, evidences = provider._convert_to_contracts(parsed_output, "doc-test-empty")
    med_field = next(f for f in fields if f["field_type"] == "medication")
    assert med_field["uncertainty_status"] == "INDETERMINATE"
    assert med_field["requires_review"] is True
    assert med_field["score"] is None


def test_evidence_run_isolation_and_anomaly_unique_ids():
    # 1. Verifica isolamento de evidências por run e que re-execução não duplica achados/evidências
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]

    run1_res = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")
    assert run1_res.status_code == 200
    doc_detail1 = client.get(f"/api/documents/{doc_id}").json()
    ev_count_1 = len(doc_detail1["evidences"])
    fn_count_1 = len(doc_detail1["findings"])
    assert ev_count_1 > 0
    assert fn_count_1 > 0

    # Executa segundo run no mesmo documento
    run2_res = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")
    assert run2_res.status_code == 200
    doc_detail2 = client.get(f"/api/documents/{doc_id}").json()

    # O detalhe do documento deve refletir o latest_run, NÃO acumular evidências e achados de run1 + run2
    assert len(doc_detail2["evidences"]) == ev_count_1
    assert len(doc_detail2["findings"]) == fn_count_1

    # 2. Verifica identificador único nas anomalias de grafo
    graph_res = client.get("/api/graph").json()
    anomalies = graph_res["anomalies"]
    assert len(anomalies) > 0
    anom_ids = [a.get("id") for a in anomalies]
    assert all(aid is not None and aid.startswith("ANOM-") for aid in anom_ids)
    # Todos os IDs de anomalia devem ser distintos
    assert len(anom_ids) == len(set(anom_ids))



