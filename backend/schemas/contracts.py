from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ExecutionMode(str, Enum):
    REAL = "REAL"
    DEMO = "DEMO"
    REPLAY = "REPLAY"


class BoundingBoxNormalized(BaseModel):
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "BoundingBoxNormalized":
        if self.x_max <= self.x_min:
            raise ValueError(f"x_max ({self.x_max}) must be strictly greater than x_min ({self.x_min})")
        if self.y_max <= self.y_min:
            raise ValueError(f"y_max ({self.y_max}) must be strictly greater than y_min ({self.y_min})")
        return self



class HypothesisContract(BaseModel):
    text: str
    rank: int = Field(..., ge=1, le=3)
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Explicit non-calibrated heuristic score")
    score_kind: str = Field(default="HEURISTIC_MODEL", description="Origin of score: HEURISTIC_MODEL, DETERMINISTIC, MANUAL")
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class ExtractedFieldContract(BaseModel):
    id: str
    run_id: str
    field_type: str
    raw_text: str
    normalized_value: Optional[str] = None
    hypotheses: List[HypothesisContract] = Field(default_factory=list)
    uncertainty_status: Literal["CERTAIN", "AMBIGUOUS", "INDETERMINATE"]
    confidence_kind: str = "HEURISTIC_MODEL"
    score: Optional[float] = None
    evidence_ids: List[str] = Field(default_factory=list)
    requires_review: bool = False


class EvidenceContract(BaseModel):
    id: str
    document_id: str
    run_id: Optional[str] = None
    page: int = 1
    bbox: Optional[BoundingBoxNormalized] = None
    coordinate_system: str = "NORMALIZED_0_1"
    localization_status: Literal[
        "PROPOSED_BY_MODEL",
        "HUMAN_VERIFIED",
        "MANUAL_FIXTURE",
        "UNLOCALIZED",
        "INVALID_GEOMETRY",
        "VALIDATED"
    ] = "UNLOCALIZED"
    source: str = "VLM_OUTPUT"
    excerpt: Optional[str] = None


class FindingContract(BaseModel):
    id: str
    document_id: str
    run_id: str
    category: Literal[
        "DOCUMENT_INCONSISTENCY",
        "LASA_SIMILARITY",
        "MISSING_MANDATORY_FIELD",
        "DUPLICATE_CLAIM",
        "GRAPH_ANOMALY"
    ]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    rule_id: str
    rule_version: str = "1.0.0"
    title: str
    explanation: str
    evidence_ids: List[str] = Field(default_factory=list)
    related_document_ids: List[str] = Field(default_factory=list)
    limitations: str
    requires_review: bool = True


class ReviewDecisionCreate(BaseModel):
    action: Literal[
        "CONFIRMED_HYPOTHESIS",
        "REJECTED_CLAIM",
        "APPROVED_CLAIM",
        "ESCALATED_FORENSIC",
        "REQUESTED_CLARIFICATION"
    ]
    finding_id: Optional[str] = None
    field_id: Optional[str] = None
    run_id: Optional[str] = None
    actor_id: str = "auditor-default"
    previous_value: Optional[str] = None
    confirmed_value: Optional[str] = None
    reason: str = Field(..., min_length=3, description="Justificativa da decisão humana")


class ReviewDecisionContract(BaseModel):
    id: str
    document_id: str
    run_id: Optional[str] = None
    field_id: Optional[str] = None
    finding_id: Optional[str] = None
    actor_id: str
    action: str
    previous_value: Optional[str] = None
    confirmed_value: Optional[str] = None
    reason: str
    created_at: str


class DocumentContract(BaseModel):
    id: str
    filename_original: str
    content_hash: str
    media_type: str
    width: int
    height: int
    synthetic: bool
    created_at: str
    findings_count: int = 0
    review_status: Literal[
        "PENDING",
        "IN_REVIEW",
        "APPROVED",
        "REJECTED",
        "ESCALATED",
        "CLARIFICATION_REQUESTED"
    ] = "PENDING"
    last_execution_mode: Optional[str] = None
    last_execution_status: Optional[str] = None
    last_execution_error: Optional[str] = None



class ProcessingRunContract(BaseModel):
    id: str
    document_id: str
    mode: str
    provider: str
    model_id: str
    model_revision: Optional[str] = None
    status: str
    started_at: str
    finished_at: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None
    schema_version: str


class AppConfigContract(BaseModel):
    app_name: str
    version: str
    environment: str
    execution_mode: str  # REAL, DEMO, REPLAY
    amd_inference_enabled: bool
    model_name: str
    demo_banner_message: Optional[str] = None
