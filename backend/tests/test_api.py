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


def test_graph_endpoint():
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "anomalies" in data
    assert data["total_claims"] == 200
    assert len(data["anomalies"]) >= 1  # Detectou o esquema de distância impossível injetado
