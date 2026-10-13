import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.models.database import (
    AuditEventModel,
    DocumentModel,
    EvidenceModel,
    ExtractedFieldModel,
    FindingModel,
    ProcessingRunModel,
    ReviewDecisionModel,
    init_db,
)
from backend.schemas.contracts import (
    AppConfigContract,
    DocumentContract,
    EvidenceContract,
    ExtractedFieldContract,
    FindingContract,
    ProcessingRunContract,
    ReviewDecisionContract,
    ReviewDecisionCreate,
)
from backend.services.graph_engine import GraphEngine
from backend.services.provider import (
    DemoFixtureProvider,
    InferenceUnavailableError,
    NoFixtureAvailableError,
    RealROCmProvider,
)
from backend.services.rules_engine import RulesEngine
from backend.services.storage import (
    FileTooLargeError,
    InvalidImageError,
    get_image_path,
    read_upload_file_chunked,
    validate_and_save_image,
)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cribum.db")
SessionLocal = init_db(DATABASE_URL)

APP_NAME = os.getenv("APP_NAME", "CRIBUM")
VERSION = "1.0.0"
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "DEMO").upper()  # DEMO ou REAL
AMD_INFERENCE_ENABLED = os.getenv("AMD_INFERENCE_ENABLED", "false").lower() == "true"
VLLM_MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2-VL-7B-Instruct")

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Auditor de Guias e Prescrições Médicas — Ambiente de Revisão Documental Rastreável",
)

# CORS Allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Desenvolvimento local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rules_engine = RulesEngine()
graph_engine = GraphEngine()
demo_provider = DemoFixtureProvider()
real_provider = RealROCmProvider()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app_name": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(DocumentModel.__table__.select().limit(1))
        return {"status": "ready", "database": "connected", "mode": EXECUTION_MODE}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serviço não está pronto: {str(exc)}",
        )


@app.get("/api/config", response_model=AppConfigContract)
def get_config():
    demo_msg = None
    if EXECUTION_MODE == "DEMO":
        demo_msg = "MODO DEMO ATIVO: Resultados originados de fixtures determinísticas documentadas. Não comprova inferência em hardware real."

    return AppConfigContract(
        app_name=APP_NAME,
        version=VERSION,
        environment=os.getenv("ENVIRONMENT", "development"),
        execution_mode=EXECUTION_MODE,
        amd_inference_enabled=AMD_INFERENCE_ENABLED,
        model_name=VLLM_MODEL_NAME,
        demo_banner_message=demo_msg,
    )


def compute_document_review_status(decisions: List[ReviewDecisionModel]) -> str:
    """
    Determina o status de revisão da guia a partir do histórico de decisões do auditor humano:
    - Se nenhuma decisão foi registrada: 'PENDING'
    - Se a decisão mais recente de nível de guia for 'APPROVED_CLAIM': 'APPROVED'
    - Se a decisão mais recente de nível de guia for 'REJECTED_CLAIM': 'REJECTED'
    - Se houver escalonamento pericial: 'ESCALATED'
    - Se houver pedido de esclarecimento: 'CLARIFICATION_REQUESTED'
    - Se houver apenas confirmações de hipótese de campos: 'IN_REVIEW'
    """
    if not decisions:
        return "PENDING"

    # Itera sobre decisões da mais recente para a mais antiga
    for dec in decisions:
        act = dec.action
        if act in ("APPROVED_CLAIM", "APPROVE"):
            return "APPROVED"
        if act in ("REJECTED_CLAIM", "REJECT"):
            return "REJECTED"
        if act in ("ESCALATED_FORENSIC", "ESCALATE"):
            return "ESCALATED"
        if act in ("REQUESTED_CLARIFICATION", "CLARIFICATION"):
            return "CLARIFICATION_REQUESTED"

    # Se houver apenas confirmação de campo/hipótese
    if any(d.action in ("CONFIRMED_HYPOTHESIS", "CONFIRM") for d in decisions):
        return "IN_REVIEW"

    return "PENDING"


@app.get("/api/documents", response_model=List[DocumentContract])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    results = []
    for d in docs:
        latest_run = (
            db.query(ProcessingRunModel)
            .filter(ProcessingRunModel.document_id == d.id)
            .order_by(ProcessingRunModel.started_at.desc())
            .first()
        )
        findings_count = (
            db.query(FindingModel).filter(FindingModel.run_id == latest_run.id).count()
            if latest_run
            else 0
        )
        decisions = (
            db.query(ReviewDecisionModel)
            .filter(ReviewDecisionModel.document_id == d.id)
            .order_by(ReviewDecisionModel.created_at.desc())
            .all()
        )
        review_status = compute_document_review_status(decisions)

        results.append(
            DocumentContract(
                id=d.id,
                filename_original=d.filename_original,
                content_hash=d.content_hash,
                media_type=d.media_type,
                width=d.width,
                height=d.height,
                synthetic=d.synthetic,
                created_at=d.created_at.isoformat(),
                findings_count=findings_count,
                review_status=review_status,
                last_execution_mode=latest_run.mode if latest_run else None,
                last_execution_status=latest_run.status if latest_run else None,
                last_execution_error=latest_run.error_message if latest_run else None,
            )
        )
    return results


@app.post("/api/documents", response_model=DocumentContract, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    synthetic: bool = Query(True, description="Identifica se o documento é de dados sintéticos"),
    db: Session = Depends(get_db),
):
    try:
        content = await read_upload_file_chunked(file)
        storage_key, content_hash, width, height, media_type = validate_and_save_image(
            file_bytes=content,
            original_filename=file.filename or "upload.jpg",
            content_type=file.content_type,
        )
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except InvalidImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no armazenamento: {str(exc)}")

    doc = DocumentModel(
        filename_original=file.filename or storage_key,
        storage_key=storage_key,
        content_hash=content_hash,
        media_type=media_type,
        width=width,
        height=height,
        synthetic=synthetic,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Registra evento de auditoria
    audit = AuditEventModel(
        actor_id="auditor-default",
        action="DOCUMENT_UPLOADED",
        entity_type="Document",
        entity_id=doc.id,
        metadata_sanitized={"filename": doc.filename_original, "hash": content_hash, "media_type": media_type},
    )
    db.add(audit)
    db.commit()

    return DocumentContract(
        id=doc.id,
        filename_original=doc.filename_original,
        content_hash=doc.content_hash,
        media_type=doc.media_type,
        width=doc.width,
        height=doc.height,
        synthetic=doc.synthetic,
        created_at=doc.created_at.isoformat(),
        findings_count=0,
        review_status="PENDING",
        last_execution_mode=None,
    )


@app.get("/api/documents/{doc_id}")
def get_document_details(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    runs = db.query(ProcessingRunModel).filter(ProcessingRunModel.document_id == doc.id).all()
    fields = []
    evidences = []
    findings = []
    latest_run = runs[-1] if runs else None
    if latest_run and latest_run.status != "FAILED":
        fields = db.query(ExtractedFieldModel).filter(ExtractedFieldModel.run_id == latest_run.id).all()
        evidences = db.query(EvidenceModel).filter(EvidenceModel.run_id == latest_run.id).all()
        findings = db.query(FindingModel).filter(FindingModel.run_id == latest_run.id).all()
    elif not latest_run:
        evidences = db.query(EvidenceModel).filter(EvidenceModel.document_id == doc.id).all()
        findings = db.query(FindingModel).filter(FindingModel.document_id == doc.id).all()

    decisions = db.query(ReviewDecisionModel).filter(ReviewDecisionModel.document_id == doc.id).order_by(ReviewDecisionModel.created_at.desc()).all()
    review_status = compute_document_review_status(decisions)

    return {
        "document": {
            "id": doc.id,
            "filename_original": doc.filename_original,
            "content_hash": doc.content_hash,
            "media_type": doc.media_type,
            "width": doc.width,
            "height": doc.height,
            "synthetic": doc.synthetic,
            "created_at": doc.created_at.isoformat(),
            "review_status": review_status,
            "findings_count": len(findings),
            "last_execution_mode": latest_run.mode if latest_run else None,
            "last_execution_status": latest_run.status if latest_run else None,
            "last_execution_error": latest_run.error_message if latest_run else None,
        },

        "fields": [
            {
                "id": f.id,
                "field_type": f.field_type,
                "raw_text": f.raw_text,
                "normalized_value": f.normalized_value,
                "hypotheses": f.hypotheses,
                "uncertainty_status": f.uncertainty_status,
                "confidence_kind": f.confidence_kind,
                "score": f.score,
                "evidence_ids": f.evidence_ids,
                "requires_review": f.requires_review,
            }
            for f in fields
        ],
        "evidences": [
            {
                "id": ev.id,
                "page": ev.page,
                "bbox": ev.bbox,
                "coordinate_system": ev.coordinate_system,
                "localization_status": ev.localization_status,
                "source": ev.source,
                "excerpt": ev.excerpt,
            }
            for ev in evidences
        ],
        "findings": [
            {
                "id": fn.id,
                "category": fn.category,
                "severity": fn.severity,
                "rule_id": fn.rule_id,
                "title": fn.title,
                "explanation": fn.explanation,
                "evidence_ids": fn.evidence_ids,
                "limitations": fn.limitations,
                "requires_review": fn.requires_review,
            }
            for fn in findings
        ],
        "decisions": [
            {
                "id": dec.id,
                "run_id": dec.run_id,
                "field_id": dec.field_id,
                "finding_id": dec.finding_id,
                "action": dec.action,
                "actor_id": dec.actor_id,
                "previous_value": dec.previous_value,
                "confirmed_value": dec.confirmed_value,
                "reason": dec.reason,
                "created_at": dec.created_at.isoformat(),
            }
            for dec in decisions
        ],
    }


@app.get("/api/documents/{doc_id}/image")
def get_document_image(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    try:
        path = get_image_path(doc.storage_key)
        return FileResponse(path, media_type=doc.media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo físico de imagem não encontrado no storage.")


@app.post("/api/documents/{doc_id}/runs", response_model=ProcessingRunContract)
def run_document_processing(
    doc_id: str,
    mode_override: Optional[str] = Query(None, description="Permite alternar entre REAL e DEMO para teste explícito"),
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    active_mode = (mode_override or EXECUTION_MODE).upper()
    if active_mode not in ("REAL", "DEMO"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Modo de execução inválido: {active_mode}. Apenas REAL e DEMO são suportados.",
        )
    provider = real_provider if active_mode == "REAL" else demo_provider


    image_path = get_image_path(doc.storage_key)

    run = ProcessingRunModel(
        document_id=doc.id,
        mode=active_mode,
        provider=provider.__class__.__name__,
        model_id=getattr(provider, "model_name", "deterministic-fixture"),
        status="PROCESSING",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        result = provider.extract(
            document_id=doc.id,
            image_path=image_path,
            content_hash=doc.content_hash,
            original_filename=doc.filename_original,
        )
    except InferenceUnavailableError as exc:
        run.status = "FAILED"
        run.error_code = "INFERENCE_UNAVAILABLE"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "INFERENCE_UNAVAILABLE", "message": str(exc), "run_id": run.id},
        )
    except NoFixtureAvailableError as exc:
        run.status = "FAILED"
        run.error_code = "NO_FIXTURE_AVAILABLE"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "NO_FIXTURE_AVAILABLE", "message": str(exc), "run_id": run.id},
        )
    except Exception as exc:
        run.status = "FAILED"
        run.error_code = "PROCESSING_ERROR"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno de processamento: {str(exc)}",
        )

    # 1. Salva Evidências isoladas por run_id e document_id
    id_map = {}
    for idx, ev_data in enumerate(result.evidences, 1):
        raw_id = ev_data.get("id") or f"ev-{run.id[:8]}-{idx}"
        scoped_id = f"{raw_id}-{run.id[:8]}" if not raw_id.endswith(run.id[:8]) else raw_id
        id_map[raw_id] = scoped_id
        ev = EvidenceModel(
            id=scoped_id,
            document_id=doc.id,
            run_id=run.id,
            page=ev_data.get("page", 1),
            bbox=ev_data.get("bbox"),
            coordinate_system=ev_data.get("coordinate_system", "NORMALIZED_0_1"),
            localization_status=ev_data.get("localization_status", "UNLOCALIZED"),
            source=ev_data.get("source", "VLM_OUTPUT"),
            excerpt=ev_data.get("excerpt"),
        )
        db.merge(ev)

    # 2. Salva Campos Extraídos
    saved_fields = []
    for f_data in result.fields:
        f_model = ExtractedFieldModel(
            run_id=run.id,
            field_type=f_data.get("field_type", "medication"),
            raw_text=f_data.get("raw_text", ""),
            normalized_value=f_data.get("normalized_value"),
            hypotheses=f_data.get("hypotheses", []),
            uncertainty_status=f_data.get("uncertainty_status", "CERTAIN"),
            confidence_kind=f_data.get("confidence_kind", "HEURISTIC_MODEL"),
            score=f_data.get("score"),
            evidence_ids=[id_map.get(eid, eid) for eid in f_data.get("evidence_ids", [])],
            requires_review=f_data.get("requires_review", False),
        )
        db.add(f_model)
        saved_fields.append(f_model)

    db.flush()

    # 3. Executa Motor de Regras
    findings = rules_engine.evaluate(document=doc, run_id=run.id, fields=saved_fields, db_session=db)
    for fn in findings:
        db.add(fn)

    # 4. Atualiza Run com sucesso
    run.status = "REVIEW_REQUIRED" if any(f.requires_review for f in findings) else "COMPLETED"
    run.finished_at = datetime.now(timezone.utc)
    run.latency_ms = result.latency_ms

    audit = AuditEventModel(
        actor_id="system",
        action="RUN_COMPLETED",
        entity_type="ProcessingRun",
        entity_id=run.id,
        metadata_sanitized={
            "mode": run.mode,
            "provider": run.provider,
            "latency_ms": run.latency_ms,
            "findings_count": len(findings),
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(run)

    return ProcessingRunContract(
        id=run.id,
        document_id=run.document_id,
        mode=run.mode,
        provider=run.provider,
        model_id=run.model_id,
        model_revision=run.model_revision,
        status=run.status,
        started_at=run.started_at.isoformat(),
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        error_code=run.error_code,
        error_message=run.error_message,
        latency_ms=run.latency_ms,
        schema_version=run.schema_version,
    )


@app.get("/api/documents/{doc_id}/findings", response_model=List[FindingContract])
def get_document_findings(doc_id: str, db: Session = Depends(get_db)):
    findings = db.query(FindingModel).filter(FindingModel.document_id == doc_id).all()
    return [
        FindingContract(
            id=fn.id,
            document_id=fn.document_id,
            run_id=fn.run_id,
            category=fn.category,
            severity=fn.severity,
            rule_id=fn.rule_id,
            rule_version=fn.rule_version,
            title=fn.title,
            explanation=fn.explanation,
            evidence_ids=fn.evidence_ids,
            related_document_ids=fn.related_document_ids,
            limitations=fn.limitations,
            requires_review=fn.requires_review,
        )
        for fn in findings
    ]


@app.post("/api/documents/{doc_id}/reviews", response_model=ReviewDecisionContract, status_code=status.HTTP_201_CREATED)
def submit_human_review(
    doc_id: str,
    decision_in: ReviewDecisionCreate,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    # 1. Validação de integridade referencial: finding_id deve pertencer a este documento
    if decision_in.finding_id:
        finding = (
            db.query(FindingModel)
            .filter(FindingModel.id == decision_in.finding_id, FindingModel.document_id == doc.id)
            .first()
        )
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O apontamento (finding_id '{decision_in.finding_id}') não pertence ao documento '{doc.id}'.",
            )

    # 2. Validação da confirmação de hipótese: exige valor confirmado, field_id e valida pertinência ao campo específico
    field_record = None
    target_run_id = decision_in.run_id
    if decision_in.action == "CONFIRMED_HYPOTHESIS":
        if not decision_in.confirmed_value or not decision_in.confirmed_value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A ação CONFIRMED_HYPOTHESIS exige o campo 'confirmed_value' preenchido.",
            )

        if not decision_in.field_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A ação CONFIRMED_HYPOTHESIS exige o identificador do campo específico ('field_id').",
            )

        field_record = (
            db.query(ExtractedFieldModel)
            .filter(ExtractedFieldModel.id == decision_in.field_id)
            .first()
        )
        if not field_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campo extraído (field_id '{decision_in.field_id}') não encontrado.",
            )

        field_run = (
            db.query(ProcessingRunModel)
            .filter(ProcessingRunModel.id == field_record.run_id)
            .first()
        )
        if not field_run or field_run.document_id != doc.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O campo '{field_record.id}' não pertence a nenhuma execução do documento '{doc.id}'.",
            )

        if decision_in.run_id and decision_in.run_id != field_record.run_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O campo '{field_record.id}' pertence à execução '{field_record.run_id}', não à execução informada '{decision_in.run_id}'.",
            )

        target_run_id = field_record.run_id

        # Valida contra o conjunto de hipóteses daquele campo específico
        valid_field_hypotheses = set()
        if field_record.normalized_value:
            valid_field_hypotheses.add(field_record.normalized_value.strip().lower())
        if field_record.raw_text:
            valid_field_hypotheses.add(field_record.raw_text.strip().lower())
        for h in (field_record.hypotheses or []):
            if isinstance(h, dict) and h.get("text"):
                valid_field_hypotheses.add(h["text"].strip().lower())

        target_val = decision_in.confirmed_value.strip().lower()
        is_matched = any(
            target_val == v or target_val in v or v in target_val
            for v in valid_field_hypotheses
        ) if valid_field_hypotheses else False

        if not is_matched:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"O valor confirmado '{decision_in.confirmed_value}' não corresponde a nenhuma das hipóteses "
                    f"extraídas para o campo específico '{field_record.field_type}' (id: '{field_record.id}')."
                ),
            )
    else:
        if not target_run_id:
            latest_run = (
                db.query(ProcessingRunModel)
                .filter(ProcessingRunModel.document_id == doc.id)
                .order_by(ProcessingRunModel.started_at.desc())
                .first()
            )
            target_run_id = latest_run.id if latest_run else None

    decision = ReviewDecisionModel(
        document_id=doc.id,
        run_id=target_run_id,
        field_id=field_record.id if field_record else decision_in.field_id,
        finding_id=decision_in.finding_id,
        actor_id=decision_in.actor_id,
        action=decision_in.action,
        previous_value=decision_in.previous_value or (field_record.raw_text if field_record else None),
        confirmed_value=decision_in.confirmed_value,
        reason=decision_in.reason,
    )
    db.add(decision)
    db.flush()

    audit = AuditEventModel(
        actor_id=decision_in.actor_id,
        action=f"REVIEW_DECISION_{decision_in.action}",
        entity_type="ReviewDecision",
        entity_id=decision.id,
        metadata_sanitized={
            "document_id": doc.id,
            "run_id": target_run_id,
            "field_id": field_record.id if field_record else decision_in.field_id,
            "action": decision_in.action,
            "confirmed_value": decision_in.confirmed_value,
            "reason": decision_in.reason,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(decision)

    return ReviewDecisionContract(
        id=decision.id,
        document_id=decision.document_id,
        run_id=decision.run_id,
        field_id=decision.field_id,
        finding_id=decision.finding_id,
        actor_id=decision.actor_id,
        action=decision.action,
        previous_value=decision.previous_value,
        confirmed_value=decision.confirmed_value,
        reason=decision.reason,
        created_at=decision.created_at.isoformat(),
    )


@app.get("/api/graph")
def get_graph():
    """Retorna o grafo de 200 guias e anomalias de rede do dataset sintético."""
    network_path = "backend/data/synthetic/network/claims_200.json"
    if not os.path.exists(network_path):
        return {"nodes": [], "links": [], "anomalies": []}

    import json
    with open(network_path, "r", encoding="utf-8") as f:
        claims = json.load(f)

    graph_data = graph_engine.build_graph_from_claims(claims)
    anomalies = graph_engine.detect_anomalies(claims)

    return {
        "nodes": graph_data["nodes"],
        "links": graph_data["links"],
        "anomalies": anomalies,
        "total_claims": len(claims),
    }


@app.post("/api/admin/seed-demo")
def seed_demo_cases(db: Session = Depends(get_db)):
    """Precarrega os 20 casos sintéticos diretamente no banco de dados para teste imediato de interface."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação administrativa de seed bloqueada em ambiente de produção.",
        )

    cases_dir = "backend/data/synthetic/cases"

    if not os.path.exists(cases_dir):
        raise HTTPException(status_code=400, detail="Casos sintéticos ainda não gerados.")

    manifest_path = "backend/data/synthetic/manifest.json"
    import json
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    loaded = 0
    for c in manifest.get("cases", []):
        img_file = c["filename"]
        source_img = os.path.join(cases_dir, img_file)
        if not os.path.exists(source_img):
            continue

        with open(source_img, "rb") as f:
            bytes_data = f.read()

        storage_key, content_hash, w, h, m_type = validate_and_save_image(
            bytes_data, img_file, "image/jpeg"
        )

        existing = db.query(DocumentModel).filter(DocumentModel.content_hash == content_hash).first()
        if not existing:
            doc = DocumentModel(
                id=c["id"],
                filename_original=img_file,
                storage_key=storage_key,
                content_hash=content_hash,
                media_type=m_type,
                width=w,
                height=h,
                synthetic=True,
            )
            db.add(doc)
            db.commit()

            # Executa o processamento em modo DEMO para já popular os alertas
            run_document_processing(doc.id, mode_override="DEMO", db=db)
            loaded += 1

    return {"message": f"Preenchidos {loaded} casos no banco de dados com sucesso."}
