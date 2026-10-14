export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface Hypothesis {
  text: string;
  rank: number;
  score?: number | null;
  score_kind: string;
  supporting_evidence_ids: string[];
}

export interface ExtractedField {
  id: string;
  field_type: string;
  raw_text: string;
  normalized_value?: string | null;
  hypotheses: Hypothesis[];
  uncertainty_status: 'CERTAIN' | 'AMBIGUOUS' | 'INDETERMINATE';
  confidence_kind: string;
  score?: number | null;
  evidence_ids: string[];
  requires_review: boolean;
}

export interface Evidence {
  id: string;
  page: number;
  bbox?: BoundingBox | null;
  coordinate_system: string;
  localization_status:
    | 'PROPOSED_BY_MODEL'
    | 'HUMAN_VERIFIED'
    | 'MANUAL_FIXTURE'
    | 'UNLOCALIZED'
    | 'INVALID_GEOMETRY'
    | 'VALIDATED';
  source: string;
  excerpt?: string | null;
}

export interface Finding {
  id: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  rule_id: string;
  title: string;
  explanation: string;
  evidence_ids: string[];
  limitations: string;
  requires_review: boolean;
}

export interface ReviewDecision {
  id: string;
  run_id?: string | null;
  field_id?: string | null;
  finding_id?: string | null;
  action: string;
  actor_id: string;
  previous_value?: string | null;
  confirmed_value?: string | null;
  reason: string;
  created_at: string;
}

export interface ReviewSubmission {
  action: string;
  confirmed_value?: string;
  field_id?: string;
  run_id?: string;
  reason: string;
  finding_id?: string;
}

export interface DocumentItem {
  id: string;
  filename_original: string;
  content_hash: string;
  media_type: string;
  width: number;
  height: number;
  synthetic: boolean;
  created_at: string;
  findings_count: number;
  review_status:
    | 'PENDING'
    | 'IN_REVIEW'
    | 'APPROVED'
    | 'REJECTED'
    | 'ESCALATED'
    | 'CLARIFICATION_REQUESTED'
    | string;
  last_execution_mode?: string | null;
  last_execution_status?: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | string | null;
  last_execution_error?: string | null;
}


export interface DocumentDetail {
  document: DocumentItem;
  fields: ExtractedField[];
  evidences: Evidence[];
  findings: Finding[];
  decisions: ReviewDecision[];
}

export interface AppConfig {
  app_name: string;
  version: string;
  environment: string;
  execution_mode: 'DEMO' | 'REAL';
  amd_inference_enabled: boolean;
  model_name: string;
  demo_banner_message?: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  cidade?: string;
  degree: number;
}

export interface GraphLink {
  source: string;
  target: string;
  relation: string;
  document_id?: string;
}

export interface NetworkAnomaly {
  id: string;
  category: string;
  severity: string;
  rule_id: string;
  title: string;
  explanation: string;
  related_document_ids: string[];
  limitations: string;
  requires_review: boolean;
}

export interface GraphResponse {
  nodes: GraphNode[];
  links: GraphLink[];
  anomalies: NetworkAnomaly[];
  total_claims: number;
}

export type DocumentSummary = DocumentItem;
export type EvidenceItem = Evidence;
export type FindingItem = Finding;
export type ReviewDecisionItem = ReviewDecision;
export type ReviewDecisionCreatePayload = ReviewSubmission;

