import pytest
from backend.services.graph_engine import GraphEngine


def test_export_graph_data_empty():
    """Verifica se export_graph_data em um grafo vazio retorna dicionário com listas vazias."""
    engine = GraphEngine()
    data = engine.export_graph_data()
    assert data == {"nodes": [], "links": []}


def test_export_graph_data_from_claims():
    """Verifica se export_graph_data exporta corretamente a estrutura de nós e arestas a partir de guias."""
    engine = GraphEngine()
    claims = [
        {
            "id": "DOC-101",
            "paciente_id": "PAC-01",
            "crm_profissional": "12345",
            "clinica_id": "CLI-99",
            "data": "2026-03-30",
            "cidade": "São Paulo",
            "procedimentos": ["EXAME-01", "EXAME-02"],
        }
    ]
    data = engine.build_graph_from_claims(claims)

    assert "nodes" in data
    assert "links" in data

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    assert "DOC-101" in nodes_by_id
    assert nodes_by_id["DOC-101"]["type"] == "documento"
    assert nodes_by_id["DOC-101"]["label"] == "Guia DOC-101"

    assert "PAC-01" in nodes_by_id
    assert nodes_by_id["PAC-01"]["type"] == "paciente"

    assert "12345" in nodes_by_id
    assert nodes_by_id["12345"]["type"] == "profissional"

    assert "CLI-99" in nodes_by_id
    assert nodes_by_id["CLI-99"]["type"] == "clinica"
    assert nodes_by_id["CLI-99"]["cidade"] == "São Paulo"

    assert "PROC-EXAME-01" in nodes_by_id
    assert nodes_by_id["PROC-EXAME-01"]["type"] == "procedimento"

    # Verificar links e relações
    links = data["links"]
    assert len(links) == 5  # paciente, prof, clinica + 2 procedimentos

    doc_links = [l for l in links if l["source"] == "DOC-101"]
    relations = {l["relation"] for l in doc_links}
    assert "referente_a_paciente" in relations
    assert "emitido_por_profissional" in relations
    assert "faturado_em_clinica" in relations
    assert "contem_procedimento" in relations

    for link in links:
        assert link["document_id"] == "DOC-101"


def test_export_graph_data_defaults_and_type_conversion():
    """Verifica valores padrão e conversão de ID/vértices não-string para string."""
    engine = GraphEngine()
    # Adiciona nós manuais sem os atributos 'type', 'label' ou 'cidade', com IDs numéricos
    engine.graph.add_node(100)
    engine.graph.add_node(200, label="Node Customizado", cidade="Rio de Janeiro")

    # Adiciona aresta manual sem 'relation' ou 'document_id'
    engine.graph.add_edge(100, 200)

    data = engine.export_graph_data()

    node_100 = next(n for n in data["nodes"] if n["id"] == "100")
    assert node_100["type"] == "desconhecido"
    assert node_100["label"] == "100"
    assert node_100["cidade"] is None
    assert node_100["degree"] == 1

    node_200 = next(n for n in data["nodes"] if n["id"] == "200")
    assert node_200["type"] == "desconhecido"
    assert node_200["label"] == "Node Customizado"
    assert node_200["cidade"] == "Rio de Janeiro"
    assert node_200["degree"] == 1

    assert len(data["links"]) == 1
    link = data["links"][0]
    assert link["source"] == "100"
    assert link["target"] == "200"
    assert link["relation"] == "relacionado"
    assert link["document_id"] is None


def test_export_graph_data_multigraph_multiple_edges_and_degree():
    """Verifica se múltiplas arestas entre os mesmos nós e o cálculo de grau funcionam em MultiGraph."""
    engine = GraphEngine()
    engine.graph.add_node("A", type="paciente", label="Paciente A")
    engine.graph.add_node("B", type="clinica", label="Clinica B")

    engine.graph.add_edge("A", "B", relation="consulta", document_id="DOC-1")
    engine.graph.add_edge("A", "B", relation="retorno", document_id="DOC-2")

    data = engine.export_graph_data()

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    assert nodes_by_id["A"]["degree"] == 2
    assert nodes_by_id["B"]["degree"] == 2

    assert len(data["links"]) == 2
    relations = {l["relation"] for l in data["links"]}
    assert relations == {"consulta", "retorno"}
    doc_ids = {l["document_id"] for l in data["links"]}
    assert doc_ids == {"DOC-1", "DOC-2"}
