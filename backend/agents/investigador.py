from typing import Any, Dict, List
from backend.services.graph_engine import GraphEngine


class InvestigadorAgent:
    """
    Agente Investigador de Rede Relacional (Motor de Grafos NetworkX):
    Modela relações entre pacientes, médicos (CRM), clínicas e guias médicas
    para identificar indícios de conluio geográfico e faturamento concomitante.
    """

    def __init__(self):
        self.engine = GraphEngine()

    def analyze_claims_network(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.engine.build_graph_from_claims(claims)
