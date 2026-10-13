import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.models.database import DocumentModel, ExtractedFieldModel, FindingModel


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
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

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
        if not crm_field or not crm_field.normalized_value:
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
                    evidence_ids=[],
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
                            f"O modelo não identificou hipóteses legíveis para a prescrição ('{med.raw_text}'). "
                            "Exige conferência visual obrigatória pelo auditor humano ou solicitação de receita legível."
                        ),
                        evidence_ids=med.evidence_ids,
                        related_document_ids=[],
                        limitations="Traçado caligráfico severamente degradado, rasura ou falha de digitalização.",
                        requires_review=True,
                    )
                )
            elif med.uncertainty_status == "AMBIGUOUS":
                hyp_texts = [f"{h.get('text')} ({int((h.get('score') or 0)*100)}%)" for h in med.hypotheses]
                hyp_summary = ", ".join(hyp_texts) if hyp_texts else "Múltiplas opções detectadas"

                findings.append(
                    FindingModel(
                        document_id=document.id,
                        run_id=run_id,
                        category="DOCUMENT_INCONSISTENCY",
                        severity="MEDIUM",
                        rule_id="MED-001-AMBIGUOUS-READING",
                        rule_version="1.0.0",
                        title=f"Leitura Ambígua: {med.raw_text}",
                        explanation=(
                            f"O traçado caligráfico admite mais de uma leitura plausível: {hyp_summary}. "
                            "Requer conferência visual do auditor humano."
                        ),
                        evidence_ids=med.evidence_ids,
                        related_document_ids=[],
                        limitations="Baseado nas hipóteses geradas pelo modelo visual. A caligrafia pode ser resolvida com o contexto clínico.",
                        requires_review=True,
                    )
                )

            # 4. Regra MED-002: Detecção de Armadilha LASA (Look-Alike Sound-Alike)
            # Cruza as hipóteses do item com a base de pares de alto risco
            lasa_match = self._check_lasa_collision(med.hypotheses)
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
                        evidence_ids=med.evidence_ids,
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
        """
        if not hypotheses or len(hypotheses) < 2:
            return None

        hyp_texts = [h.get("text", "").lower() for h in hypotheses]

        for par in self.lasa_database:
            nome_a = par["droga_a"]["nome"].lower()
            nome_b = par["droga_b"]["nome"].lower()

            has_match_a = any(nome_a in t for t in hyp_texts)
            has_match_b = any(nome_b in t for t in hyp_texts)

            # Também verifica palavras-chave / marcas registradas do par
            palavras = [p.lower() for p in par.get("palavras_chave", [])]
            for t in hyp_texts:
                for p in palavras:
                    if p in t:
                        if nome_a[:4] in p:
                            has_match_a = True
                        if nome_b[:4] in p:
                            has_match_b = True

            # Colisão LASA confirmada quando o leitor hesita entre droga A e droga B
            if has_match_a and has_match_b:
                return (par, par["droga_a"]["nome"], par["droga_b"]["nome"])

        return None


