import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.models.database import DocumentModel, ExtractedFieldModel, FindingModel


def normalize_text(value: Optional[str]) -> str:
    """Remove acentos, espaços extras e converte para minúsculas para comparação determinística."""
    if not value or not isinstance(value, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def is_valid_crm_format(crm: Optional[str]) -> bool:
    """Verifica se o CRM possui dígitos de identificação (ex: CRM-SP 123456 ou 123456-SP)."""
    if not crm or not isinstance(crm, str):
        return False
    cleaned = crm.strip().upper()
    return bool(re.search(r"\d{4,7}", cleaned))


SEVERITY_MAP: Dict[str, str] = {
    "CRITICA": "CRITICAL",
    "CRITICAL": "CRITICAL",
    "ALTA": "HIGH",
    "HIGH": "HIGH",
    "MEDIA": "MEDIUM",
    "MEDIUM": "MEDIUM",
    "BAIXA": "LOW",
    "LOW": "LOW",
}


class RulesEngine:
    """
    Motor de regras determinísticas e rastreáveis do CRIBUM:
    Aplica regras documentais, ambiguidade de leitura e similaridade LASA.
    Não inventa fatos nem dá pareceres médicos autônomos.
    """

    def __init__(self, lasa_path: str = "backend/data/references/lasa_ismp.json"):
        self.lasa_database = self._load_lasa(lasa_path)

    def _load_lasa(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        processed = []
        for par in data:
            nome_a = normalize_text(par.get("droga_a", {}).get("nome", ""))
            nome_b = normalize_text(par.get("droga_b", {}).get("nome", ""))

            prefix_a = nome_a[:4] if len(nome_a) >= 4 else None
            prefix_b = nome_b[:4] if len(nome_b) >= 4 else None

            palavras = [normalize_text(p) for p in par.get("palavras_chave", []) if p]

            terms_a_set = {nome_a} if nome_a else set()
            terms_b_set = {nome_b} if nome_b else set()

            for p in palavras:
                if prefix_a and prefix_a in p:
                    terms_a_set.add(p)
                if prefix_b and prefix_b in p:
                    terms_b_set.add(p)

            par["_terms_a"] = tuple(terms_a_set)
            par["_terms_b"] = tuple(terms_b_set)
            processed.append(par)

        return processed

    def evaluate(
        self,
        document: DocumentModel,
        run_id: str,
        fields: List[ExtractedFieldModel],
        db_session: Optional[Any] = None
    ) -> List[FindingModel]:
        findings: List[FindingModel] = []

        # 1. Regra DOC-001: Verificação de duplicidade exata de documento por Hash SHA-256
        if db_session is not None:
            existing_dup = (
                db_session.query(DocumentModel)
                .filter(
                    DocumentModel.content_hash == document.content_hash,
                    DocumentModel.id != document.id
                )
                .first()
            )
            if existing_dup:
                findings.append(
                    FindingModel(
                        document_id=document.id,
                        run_id=run_id,
                        category="DUPLICATE_CLAIM",
                        severity="HIGH",
                        rule_id="DOC-001-EXACT-HASH-DUPLICATE",
                        rule_version="1.0.0",
                        title="Documento Idêntico Já Registrado",
                        explanation=(
                            f"O arquivo enviado possui hash SHA-256 ({document.content_hash[:12]}...) "
                            f"idêntico ao documento previamente registrado ID: {existing_dup.id} "
                            f"({existing_dup.filename_original})."
                        ),
                        evidence_ids=[],
                        related_document_ids=[existing_dup.id],
                        limitations="Validação puramente criptográfica. Não avalia se houve reenvio administrativo justificado.",
                        requires_review=True,
                    )
                )

        # 2. Regra DOC-002: Verificação de campos obrigatórios (CRM do prescritor)
        crm_field = next((f for f in fields if f.field_type == "crm"), None)
        crm_val = (crm_field.normalized_value or crm_field.raw_text or "").strip() if crm_field else ""
        if not crm_field or not crm_val:
            findings.append(
                FindingModel(
                    document_id=document.id,
                    run_id=run_id,
                    category="MISSING_MANDATORY_FIELD",
                    severity="HIGH",
                    rule_id="DOC-002-MISSING-CRM",
                    rule_version="1.0.0",
                    title="Identificador do Prescritor (CRM) Ausente",
                    explanation="Não foi possível identificar o número de CRM do médico na guia/receita.",
                    evidence_ids=crm_field.evidence_ids if crm_field else [],
                    related_document_ids=[],
                    limitations="Caligrafia ilegível no carimbo ou carimbo cortado na digitalização podem causar falso positivo.",
                    requires_review=True,
                )
            )

        # 3. Regra MED-001: Ambiguidade ou Ilegibilidade de Leitura em Medicamento
        med_fields = [f for f in fields if f.field_type == "medication"]
        for med in med_fields:
            if med.uncertainty_status == "INDETERMINATE":
                findings.append(
                    FindingModel(
                        document_id=document.id,
                        run_id=run_id,
                        category="MISSING_MANDATORY_FIELD",
                        severity="HIGH",
                        rule_id="MED-003-INDETERMINATE-READING",
                        rule_version="1.0.0",
                        title="Prescrição Ilegível ou Indeterminada",
                        explanation=(
                            f"O modelo não identificou hipóteses legíveis para a prescrição ('{med.raw_text or ''}'). "
                            "Exige conferência visual obrigatória pelo auditor humano ou solicitação de receita legível."
                        ),
                        evidence_ids=med.evidence_ids or [],
                        related_document_ids=[],
                        limitations="Traçado caligráfico severamente degradado, rasura ou falha de digitalização.",
                        requires_review=True,
                    )
                )
            elif med.uncertainty_status == "AMBIGUOUS":
                hypotheses_list = med.hypotheses or []
                hyp_texts = [
                    f"{h.get('text')} ({int((h.get('score') or 0)*100)}%)"
                    for h in hypotheses_list
                    if isinstance(h, dict) and h.get("text")
                ]
                hyp_summary = ", ".join(hyp_texts) if hyp_texts else "Múltiplas opções detectadas"

                findings.append(
                    FindingModel(
                        document_id=document.id,
                        run_id=run_id,
                        category="DOCUMENT_INCONSISTENCY",
                        severity="MEDIUM",
                        rule_id="MED-001-AMBIGUOUS-READING",
                        rule_version="1.0.0",
                        title=f"Leitura Ambígua: {med.raw_text or ''}",
                        explanation=(
                            f"O traçado caligráfico admite mais de uma leitura plausível: {hyp_summary}. "
                            "Requer conferência visual do auditor humano."
                        ),
                        evidence_ids=med.evidence_ids or [],
                        related_document_ids=[],
                        limitations="Baseado nas hipóteses geradas pelo modelo visual. A caligrafia pode ser resolvida com o contexto clínico.",
                        requires_review=True,
                    )
                )

            # 4. Regra MED-002: Detecção de Armadilha LASA (Look-Alike Sound-Alike)
            # Cruza as hipóteses do item com a base de pares de alto risco
            lasa_match = self._check_lasa_collision(med.hypotheses or [])
            if lasa_match:
                par_info, droga_detectada, droga_conflitante = lasa_match
                raw_sev = str(par_info.get("gravidade", "HIGH")).upper()
                norm_sev = SEVERITY_MAP.get(raw_sev, "HIGH")

                findings.append(
                    FindingModel(
                        document_id=document.id,
                        run_id=run_id,
                        category="LASA_SIMILARITY",
                        severity=norm_sev,
                        rule_id=f"MED-002-LASA-{par_info.get('par_id')}",
                        rule_version="1.0.0",
                        title=f"Risco Crítico de Troca LASA: {droga_detectada} vs {droga_conflitante}",
                        explanation=(
                            f"Identificada proximidade ortográfica/fonética entre as hipóteses de leitura. "
                            f"{par_info.get('risco_clinico')} "
                            f"Droga A: {par_info['droga_a']['nome']} ({par_info['droga_a']['classe']}) | "
                            f"Droga B: {par_info['droga_b']['nome']} ({par_info['droga_b']['classe']})."
                        ),
                        evidence_ids=med.evidence_ids or [],
                        related_document_ids=[],
                        limitations="Alerta de segurança preventiva. O prescritor pode ter indicado a droga corretamente.",
                        requires_review=True,
                    )
                )

        return findings

    def _check_lasa_collision(self, hypotheses: List[Dict[str, Any]]) -> Optional[tuple]:
        """
        Verifica se as hipóteses concorrentes colidem com pares LASA catalogados pelo ISMP.
        Uma colisão real ocorre quando a leitura é ambígua (>= 2 hipóteses) e apresenta
        hipóteses alternativas que coincidem simultaneamente com a Droga A e a Droga B do par.
        Normaliza strings para NFKD (insensível a acentuação e caixa).
        """
        if not hypotheses or len(hypotheses) < 2:
            return None

        hyp_texts = [
            normalize_text(h.get("text"))
            for h in hypotheses
            if isinstance(h, dict) and h.get("text")
        ]
        if not hyp_texts:
            return None

        joined_hyp = " \n ".join(hyp_texts)

        for par in self.lasa_database:
            has_match_a = any(term in joined_hyp for term in par["_terms_a"])
            has_match_b = any(term in joined_hyp for term in par["_terms_b"])

            # Colisão LASA confirmada quando o leitor hesita entre droga A e droga B
            if has_match_a and has_match_b:
                return (par, par["droga_a"]["nome"], par["droga_b"]["nome"])

        return None
