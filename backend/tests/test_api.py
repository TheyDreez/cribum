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


def test_cors_security_headers():
    # 1. Allowed origin request
    res_allowed = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res_allowed.headers.get("access-control-allow-credentials") == "true"

    # 2. Preflight request with allowed origin, method, and header
    res_preflight = client.options(
        "/api/documents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert res_preflight.status_code == 200
    assert res_preflight.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in res_preflight.headers.get("access-control-allow-methods", "")

    # 3. Disallowed origin request
    res_disallowed = client.get(
        "/health",
        headers={"Origin": "http://malicious-attacker.com"}
    )
    assert res_disallowed.headers.get("access-control-allow-origin") is None


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

    # Obtém o field_id extraído para vincular a confirmação
    doc_data = client.get(f"/api/documents/{doc_id}").json()
    field_id = doc_data["fields"][0]["id"]

    # Auditor humano confere e envia decisão vinculada ao campo específico
    review_payload = {
        "action": "CONFIRMED_HYPOTHESIS",
        "actor_id": "auditor-andre-01",
        "field_id": field_id,
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


def test_human_review_hypothesis_and_finding_validation():
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]
    client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")

    doc_data = client.get(f"/api/documents/{doc_id}").json()
    med_field_id = next(f["id"] for f in doc_data["fields"] if f["field_type"] == "medication")

    # 1. Submissão sem field_id para CONFIRMED_HYPOTHESIS deve retornar 400
    res_no_field = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "confirmed_value": "Losartana 50mg",
            "reason": "Sem informar field_id.",
        },
    )
    assert res_no_field.status_code == 400
    assert "field_id" in res_no_field.json()["detail"]

    # 2. Submissão com finding_id inexistente/de outro documento deve retornar 400
    res_fake_finding = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "finding_id": "fake-finding-9999",
            "confirmed_value": "Losartana 50mg",
            "reason": "Testando finding falso.",
        },
    )
    assert res_fake_finding.status_code == 400
    assert "não pertence ao documento" in res_fake_finding.json()["detail"]

    # 3. Submissão de hipótese alienígena (não extraída no documento) deve retornar 400
    res_alien_hyp = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "confirmed_value": "Morfina 100mg Ampola Injetável",
            "reason": "Tentativa de confirmação de valor arbitrário fora do documento.",
        },
    )
    assert res_alien_hyp.status_code == 400
    assert "não corresponde a uma hipótese deste campo" in res_alien_hyp.json()["detail"]

    # 4. Submissão sem confirmed_value para CONFIRMED_HYPOTHESIS deve retornar 400
    res_empty_val = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "confirmed_value": "   ",
            "reason": "Valor em branco.",
        },
    )
    assert res_empty_val.status_code == 400
    assert "exige o campo 'confirmed_value'" in res_empty_val.json()["detail"]


def test_cross_field_hypothesis_injection_prevented():
    # Previne que a hipótese de um campo (ex: CRM) seja confirmada em outro campo (ex: medicação)
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]
    client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")

    doc_data = client.get(f"/api/documents/{doc_id}").json()
    med_field_id = next(f["id"] for f in doc_data["fields"] if f["field_type"] == "medication")
    crm_field = next(f for f in doc_data["fields"] if f["field_type"] == "crm")
    crm_value = crm_field["raw_text"]

    # Tenta confirmar o valor do CRM dentro do campo de medicação
    res_cross = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "confirmed_value": crm_value,
            "reason": "Tentando forçar valor de CRM no campo de medicamento.",
        },
    )
    assert res_cross.status_code == 400
    assert "não corresponde a uma hipótese deste campo" in res_cross.json()["detail"]


def test_exact_hypothesis_validation_and_rejections():
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]
    run_id = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO").json()["id"]

    doc_data = client.get(f"/api/documents/{doc_id}").json()
    med_field_id = next(f["id"] for f in doc_data["fields"] if f["field_type"] == "medication")
    findings = doc_data["findings"]
    finding_id = findings[0]["id"] if findings else None

    # 1. Hipótese exata aceita (com casefold/normalização NFKC)
    res_exact = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "run_id": run_id,
            "finding_id": finding_id,
            "confirmed_value": "losartana 50mg",
            "reason": "Conferido visualmente.",
        },
    )
    assert res_exact.status_code == 201
    assert res_exact.json()["confirmed_value"] == "losartana 50mg"

    # 2. Apenas parte da hipótese (substring) rejeitada
    res_sub = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "run_id": run_id,
            "confirmed_value": "Losartana",
            "reason": "Tentativa de confirmação de substring.",
        },
    )
    assert res_sub.status_code == 400
    assert "não corresponde a uma hipótese deste campo" in res_sub.json()["detail"]

    # 3. Hipótese com conteúdo extra (superstring) rejeitada
    res_super = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "CONFIRMED_HYPOTHESIS",
            "actor_id": "auditor-01",
            "field_id": med_field_id,
            "run_id": run_id,
            "confirmed_value": "Losartana 50mg comprimidos via oral",
            "reason": "Tentativa de confirmação de superstring.",
        },
    )
    assert res_super.status_code == 400
    assert "não corresponde a uma hipótese deste campo" in res_super.json()["detail"]

    # 4. Run de outro documento rejeitado
    res_alien_run = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "APPROVED_CLAIM",
            "actor_id": "auditor-01",
            "run_id": "non-existent-or-alien-run-12345",
            "reason": "Tentativa de vincular run inexistente.",
        },
    )
    assert res_alien_run.status_code == 400
    assert "não pertence ao documento" in res_alien_run.json()["detail"]

    # 5. Justificativa com menos de 3 caracteres úteis rejeitada
    res_short_reason = client.post(
        f"/api/documents/{doc_id}/reviews",
        json={
            "action": "APPROVED_CLAIM",
            "actor_id": "auditor-01",
            "reason": "  ok  ",
        },
    )
    assert res_short_reason.status_code == 400
    assert "pelo menos 3 caracteres" in res_short_reason.json()["detail"]


def test_multiple_runs_and_failed_run_isolation():
    # Verifica que uma execução com falha subsequente não mascara falhas com dados antigos
    img_path = "backend/data/synthetic/cases/caso_01_losartana_lorazepam.jpg"
    with open(img_path, "rb") as f:
        files = {"file": ("caso_01_losartana_lorazepam.jpg", f.read(), "image/jpeg")}
    doc_id = client.post("/api/documents", files=files).json()["id"]

    # Run 1: Sucesso em DEMO
    run1 = client.post(f"/api/documents/{doc_id}/runs?mode_override=DEMO")
    assert run1.status_code == 200
    detail1 = client.get(f"/api/documents/{doc_id}").json()
    assert detail1["document"]["findings_count"] > 0
    assert detail1["document"]["last_execution_status"] in ("REVIEW_REQUIRED", "COMPLETED")

    # Run 2: Falha explícita em REAL (servidor offline)
    run2 = client.post(f"/api/documents/{doc_id}/runs?mode_override=REAL")
    assert run2.status_code == 503

    # O detalhe atualizado do documento DEVE exibir last_execution_status == FAILED
    # e NÃO mascarar o erro retornando os campos e evidências do Run 1 antigo!
    detail2 = client.get(f"/api/documents/{doc_id}").json()
    assert detail2["document"]["last_execution_status"] == "FAILED"
    assert detail2["document"]["last_execution_error"] is not None
    assert detail2["document"]["findings_count"] == 0
    assert len(detail2["fields"]) == 0
    assert len(detail2["findings"]) == 0


def test_schema_auto_migration_for_legacy_database(tmp_path):
    import sqlite3
    from sqlalchemy import text
    from backend.models.database import init_db, EvidenceModel, ReviewDecisionModel

    db_file = tmp_path / "legacy_test.db"
    db_url = f"sqlite:///{db_file}"

    # Cria tabelas legadas simulando versão antiga do banco (sem evidences.run_id e sem review_decisions.run_id/field_id)
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE documents (
            id VARCHAR(36) PRIMARY KEY,
            filename_original VARCHAR(255) NOT NULL,
            storage_key VARCHAR(255) NOT NULL UNIQUE,
            content_hash VARCHAR(64) NOT NULL,
            media_type VARCHAR(50) NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            synthetic BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE processing_runs (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            mode VARCHAR(20) NOT NULL,
            provider VARCHAR(50) NOT NULL,
            model_id VARCHAR(100) NOT NULL,
            status VARCHAR(30) NOT NULL,
            started_at DATETIME NOT NULL,
            schema_version VARCHAR(20) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE evidences (
            id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            page INTEGER NOT NULL,
            bbox JSON,
            coordinate_system VARCHAR(30) NOT NULL,
            localization_status VARCHAR(30) NOT NULL,
            source VARCHAR(50) NOT NULL,
            excerpt TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE review_decisions (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            finding_id VARCHAR(36),
            actor_id VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            previous_value TEXT,
            confirmed_value TEXT,
            reason TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Inicializa a aplicação com o banco legado: ensure_schema_migrations deve rodar e adicionar colunas
    SessionMaker = init_db(db_url)
    session = SessionMaker()

    try:
        # Inserção de registro usando as novas colunas deve funcionar sem OperationalError
        ev = EvidenceModel(
            id="ev-migrated-1",
            document_id="doc-migrated",
            run_id="run-migrated-1",
            page=1,
            coordinate_system="NORMALIZED_0_1",
            localization_status="UNLOCALIZED",
            source="TEST",
        )
        session.add(ev)

        dec = ReviewDecisionModel(
            id="dec-migrated-1",
            document_id="doc-migrated",
            run_id="run-migrated-1",
            field_id="field-migrated-1",
            actor_id="auditor-test",
            action="CONFIRMED_HYPOTHESIS",
            confirmed_value="Losartana",
            reason="Migração bem-sucedida.",
        )
        session.add(dec)
        session.commit()

        # Consulta e valida que as novas colunas foram persistidas
        ev_queried = session.query(EvidenceModel).filter_by(id="ev-migrated-1").first()
        assert ev_queried is not None
        assert ev_queried.run_id == "run-migrated-1"

        dec_queried = session.query(ReviewDecisionModel).filter_by(id="dec-migrated-1").first()
        assert dec_queried is not None
        assert dec_queried.run_id == "run-migrated-1"
        assert dec_queried.field_id == "field-migrated-1"
    finally:
        session.close()





