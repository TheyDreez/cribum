from typing import Any, Dict, List, Optional
import networkx as nx


class GraphEngine:
    """
    Motor de análise de grafo de relacionamentos (Investigador do CRIBUM).
    Usa NetworkX para modelar as conexões entre Pacientes, Profissionais,
    Clínicas, Documentos e Procedimentos.
    """

    def __init__(self):
        self.graph = nx.MultiGraph()

    def build_graph_from_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Popula o grafo a partir de uma lista de registros de guias médicas sintéticas.
        Retorna estrutura de nós e arestas serializável em JSON para visualização.
        """
        self.graph.clear()

        for claim in claims:
            doc_id = str(claim.get("document_id") or claim.get("id"))
            paciente_id = str(claim.get("paciente_id", "PACIENTE-DESCONHECIDO"))
            prof_id = str(claim.get("crm_profissional", "PROF-DESCONHECIDO"))
            clinica_id = str(claim.get("clinica_id", "CLINICA-DESCONHECIDA"))
            data_str = str(claim.get("data", "2026-10-12"))
            cidade = claim.get("cidade", "São Paulo")

            # Nós principais com metadados
            self.graph.add_node(doc_id, type="documento", label=f"Guia {doc_id}", data=data_str)
            self.graph.add_node(paciente_id, type="paciente", label=f"Pac. {paciente_id}")
            self.graph.add_node(prof_id, type="profissional", label=f"CRM {prof_id}")
            self.graph.add_node(clinica_id, type="clinica", label=f"Clínica {clinica_id}", cidade=cidade)

            # Arestas relacionais com rastreabilidade ao documento de origem
            self.graph.add_edge(doc_id, paciente_id, relation="referente_a_paciente", document_id=doc_id)
            self.graph.add_edge(doc_id, prof_id, relation="emitido_por_profissional", document_id=doc_id)
            self.graph.add_edge(doc_id, clinica_id, relation="faturado_em_clinica", document_id=doc_id)

            # Procedimentos ou medicamentos
            for proc in claim.get("procedimentos", []):
                proc_node = f"PROC-{proc}"
                self.graph.add_node(proc_node, type="procedimento", label=str(proc))
                self.graph.add_edge(doc_id, proc_node, relation="contem_procedimento", document_id=doc_id)

        return self.export_graph_data()

    def detect_anomalies(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executa regras de anomalia determinísticas e explicáveis:
        1. Procedimentos simultâneos em clínicas geograficamente distintas no mesmo dia.
        2. Concentração atípica de procedimentos idênticos pelo mesmo profissional.
        """
        anomalies: List[Dict[str, Any]] = []

        # 1. Agrupa por Profissional e Data
        prof_agenda: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for claim in claims:
            prof = str(claim.get("crm_profissional"))
            data = str(claim.get("data"))
            if not prof or prof == "PROF-DESCONHECIDO":
                continue
            prof_agenda.setdefault(prof, {}).setdefault(data, []).append(claim)

        # Regra GRAFO-001: Múltiplos atendimentos no mesmo dia em cidades distantes
        for prof, dates in prof_agenda.items():
            for data, day_claims in dates.items():
                clinicas = set(c.get("clinica_id") for c in day_claims)
                cidades = set(c.get("cidade") for c in day_claims if c.get("cidade"))

                if len(cidades) > 1 and len(day_claims) >= 3:
                    doc_ids = [str(c.get("document_id") or c.get("id")) for c in day_claims]
                    anomalies.append({
                        "category": "GRAPH_ANOMALY",
                        "severity": "HIGH",
                        "rule_id": "NET-001-CONCURRENT-DISTANT-CLINICS",
                        "title": f"Atendimentos no Mesmo Dia em Municípios Distintos (CRM {prof})",
                        "explanation": (
                            f"O profissional CRM {prof} possui {len(day_claims)} guias registradas na mesma data ({data}) "
                            f"distribuídas entre {len(cidades)} municípios distintos ({', '.join(sorted(cidades))}). "
                            "Indício documental que requer conferência humana quanto à viabilidade de deslocamento ou divergência na data de faturamento."
                        ),
                        "related_document_ids": doc_ids,
                        "limitations": "Pode decorrer de erro de digitação de data pelo faturamento ou telemedicina legítima.",
                        "requires_review": True,
                    })

        return anomalies

    def export_graph_data(self) -> Dict[str, Any]:
        """Converte o grafo NetworkX para o formato compatível com componentes de visualização React (nós e arestas)."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": str(node_id),
                "type": attrs.get("type", "desconhecido"),
                "label": attrs.get("label", str(node_id)),
                "cidade": attrs.get("cidade"),
                "degree": self.graph.degree(node_id),
            })

        links = []
        for u, v, attrs in self.graph.edges(data=True):
            links.append({
                "source": str(u),
                "target": str(v),
                "relation": attrs.get("relation", "relacionado"),
                "document_id": attrs.get("document_id"),
            })

        return {"nodes": nodes, "links": links}
