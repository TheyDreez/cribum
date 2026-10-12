import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.types import JSON

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename_original = Column(String(255), nullable=False)
    storage_key = Column(String(255), nullable=False, unique=True)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    media_type = Column(String(50), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    runs = relationship("ProcessingRunModel", back_populates="document", cascade="all, delete-orphan")
    evidences = relationship("EvidenceModel", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("FindingModel", back_populates="document", cascade="all, delete-orphan")
    decisions = relationship("ReviewDecisionModel", back_populates="document", cascade="all, delete-orphan")


class ProcessingRunModel(Base):
    __tablename__ = "processing_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    mode = Column(String(20), nullable=False)  # REAL, DEMO, REPLAY
    provider = Column(String(50), nullable=False)  # vLLM-ROCm, DemoFixture, ReplayStorage
    model_id = Column(String(100), nullable=False)
    model_revision = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED, REVIEW_REQUIRED
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    schema_version = Column(String(20), default="1.0.0", nullable=False)

    document = relationship("DocumentModel", back_populates="runs")
    fields = relationship("ExtractedFieldModel", back_populates="run", cascade="all, delete-orphan")
    findings = relationship("FindingModel", back_populates="run", cascade="all, delete-orphan")


class EvidenceModel(Base):
    __tablename__ = "evidences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page = Column(Integer, default=1, nullable=False)
    bbox = Column(JSON, nullable=True)  # {"x_min": float, "y_min": float, "x_max": float, "y_max": float} 0..1
    coordinate_system = Column(String(30), default="NORMALIZED_0_1", nullable=False)
    localization_status = Column(String(30), default="UNLOCALIZED", nullable=False)  # VALIDATED, UNLOCALIZED, MANUAL_FIXTURE
    source = Column(String(50), nullable=False)  # VLM_OUTPUT, FIXTURE, MANUAL_ANNOTATION
    excerpt = Column(Text, nullable=True)

    document = relationship("DocumentModel", back_populates="evidences")


class ExtractedFieldModel(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("processing_runs.id"), nullable=False, index=True)
    field_type = Column(String(50), nullable=False)  # medication, posology, crm, patient, date, clinic, cid
    raw_text = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=True)
    hypotheses = Column(JSON, nullable=False)  # [{"text": str, "rank": int, "score": float, "score_kind": str, "supporting_evidence_ids": []}]
    uncertainty_status = Column(String(30), nullable=False)  # CERTAIN, AMBIGUOUS, INDETERMINATE
    confidence_kind = Column(String(30), nullable=False)  # HEURISTIC_MODEL, DETERMINISTIC, MANUAL
    score = Column(Float, nullable=True)  # explicit non-calibrated heuristic score
    evidence_ids = Column(JSON, default=list, nullable=False)
    requires_review = Column(Boolean, default=False, nullable=False)

    run = relationship("ProcessingRunModel", back_populates="fields")


class FindingModel(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("processing_runs.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # DOCUMENT_INCONSISTENCY, LASA_SIMILARITY, MISSING_MANDATORY_FIELD, DUPLICATE_CLAIM, GRAPH_ANOMALY
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    rule_id = Column(String(50), nullable=False)
    rule_version = Column(String(20), default="1.0.0", nullable=False)
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_ids = Column(JSON, default=list, nullable=False)
    related_document_ids = Column(JSON, default=list, nullable=False)
    limitations = Column(Text, nullable=False)
    requires_review = Column(Boolean, default=True, nullable=False)

    document = relationship("DocumentModel", back_populates="findings")
    run = relationship("ProcessingRunModel", back_populates="findings")


class ReviewDecisionModel(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=True)
    actor_id = Column(String(100), default="auditor-default", nullable=False)
    action = Column(String(50), nullable=False)  # CONFIRMED_HYPOTHESIS, REJECTED_CLAIM, APPROVED_CLAIM, ESCALATED_FORENSIC, REQUESTED_CLARIFICATION
    previous_value = Column(Text, nullable=True)
    confirmed_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("DocumentModel", back_populates="decisions")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    metadata_sanitized = Column(JSON, default=dict, nullable=False)


# Database Initialization Helper
def get_engine(database_url: str = "sqlite:///./cribum.db"):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def init_db(database_url: str = "sqlite:///./cribum.db"):
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
