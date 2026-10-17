from typing import Any, List, Optional
from backend.models.database import DocumentModel, ExtractedFieldModel, FindingModel
from backend.services.rules_engine import RulesEngine


class FarmaceuticoAgent:
    """
    Agente Farmacêutico & Auditor Clínico (Motor Normativo Determinístico):
    Avalia similaridade fonética/ortográfica LASA (ISMP Brasil), coerência diagnóstica CID-10,
    duplicidade documental por hash SHA-256 e campos obrigatórios ausentes.
    """

    def __init__(self, lasa_path: str = "backend/data/references/lasa_ismp.json"):
        self.engine = RulesEngine(lasa_path=lasa_path)

    def evaluate(
        self,
        document: DocumentModel,
        run_id: str,
        fields: List[ExtractedFieldModel],
        db_session: Optional[Any] = None,
    ) -> List[FindingModel]:
        return self.engine.evaluate(
            document=document,
            run_id=run_id,
            fields=fields,
            db_session=db_session,
        )
