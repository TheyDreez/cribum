import pytest
from backend.services.graph_engine import GraphEngine


def test_build_graph_from_claims_empty():
    """Verifica se build_graph_from_claims lida com lista vazia de sinistros."""
    engine = GraphEngine()
    result = engine.build_graph_from_claims([])

    assert result == {"nodes": [], "links": []}
    assert engine.graph.number_of_nodes() == 0
    assert engine.graph.number_of_edges() == 0


def test_build_graph_from_claims_clears_previous_state():
    """Garante que chamadas subsequentes limpam o estado anterior do grafo."""
    engine = GraphEngine()
    initial_claims = [
        {
            "document_id": "DOC-OLD-01",
            "paciente_id": "PAC-01",
            "crm_profissional": "12345",
            "clinica_id": "CLIN-01",
        }
    ]
    engine.build_graph_from_claims(initial_claims)
    assert engine.graph.number_of_nodes() == 4

    new_result = engine.build_graph_from_claims([])
    assert new_result == {"nodes": [], "links": []}
    assert engine.graph.number_of_nodes() == 0
    assert engine.graph.number_of_edges() == 0


def test_build_graph_from_claims_standard_claim():
    """Testa a construção do grafo com um sinistro completo contendo todos os metadados."""
    engine = GraphEngine()
    claims = [
        {
            "document_id": "DOC-101",
            "paciente_id": "PAC-201",
            "crm_profissional": "CRM-SP 99999",
            "clinica_id": "CLIN-301",
            "data": "2026-05-20",
            "cidade": "Campinas",
        }
    ]

    result = engine.build_graph_from_claims(claims)

    assert "nodes" in result
    assert "links" in result
    assert len(result["nodes"]) == 4
    assert len(result["links"]) == 3

    nodes_by_id = {n["id"]: n for n in result["nodes"]}
    assert "DOC-101" in nodes_by_id
    assert nodes_by_id["DOC-101"]["type"] == "documento"
    assert nodes_by_id["DOC-101"]["label"] == "Guia DOC-101"

    assert "PAC-201" in nodes_by_id
    assert nodes_by_id["PAC-201"]["type"] == "paciente"

    assert "CRM-SP 99999" in nodes_by_id
    assert nodes_by_id["CRM-SP 99999"]["type"] == "profissional"

    assert "CLIN-301" in nodes_by_id
    assert nodes_by_id["CLIN-301"]["type"] == "clinica"
    assert nodes_by_id["CLIN-301"]["cidade"] == "Campinas"

    relations = {(link["source"], link["target"], link["relation"]) for link in result["links"]}
    assert ("DOC-101", "PAC-201", "referente_a_paciente") in relations
    assert ("DOC-101", "CRM-SP 99999", "emitido_por_profissional") in relations
    assert ("DOC-101", "CLIN-301", "faturado_em_clinica") in relations

    for link in result["links"]:
        assert link["document_id"] == "DOC-101"


def test_build_graph_from_claims_id_fallback():
    """Garante que a chave 'id' seja usada se 'document_id' não estiver presente no sinistro."""
    engine = GraphEngine()
    claims = [{"id": "GUID-555"}]

    result = engine.build_graph_from_claims(claims)

    doc_nodes = [n for n in result["nodes"] if n["type"] == "documento"]
    assert len(doc_nodes) == 1
    assert doc_nodes[0]["id"] == "GUID-555"
    assert doc_nodes[0]["label"] == "Guia GUID-555"


def test_build_graph_from_claims_missing_fields_defaults():
    """Verifica fallbacks padrão quando campos opcionais do sinistro estão ausentes."""
    engine = GraphEngine()
    claims = [{"document_id": "DOC-MINIMAL"}]

    result = engine.build_graph_from_claims(claims)

    nodes_by_id = {n["id"]: n for n in result["nodes"]}

    assert "PACIENTE-DESCONHECIDO" in nodes_by_id
    assert nodes_by_id["PACIENTE-DESCONHECIDO"]["type"] == "paciente"

    assert "PROF-DESCONHECIDO" in nodes_by_id
    assert nodes_by_id["PROF-DESCONHECIDO"]["type"] == "profissional"

    assert "CLINICA-DESCONHECIDA" in nodes_by_id
    assert nodes_by_id["CLINICA-DESCONHECIDA"]["type"] == "clinica"
    assert nodes_by_id["CLINICA-DESCONHECIDA"]["cidade"] == "São Paulo"


def test_build_graph_from_claims_with_procedimentos():
    """Verifica se procedimentos do sinistro são inseridos corretamente como nós e arestas."""
    engine = GraphEngine()
    claims = [
        {
            "document_id": "DOC-PROC-1",
            "procedimentos": ["10101012", "40301001"],
        }
    ]

    result = engine.build_graph_from_claims(claims)

    nodes_by_id = {n["id"]: n for n in result["nodes"]}
    assert "PROC-10101012" in nodes_by_id
    assert nodes_by_id["PROC-10101012"]["type"] == "procedimento"
    assert nodes_by_id["PROC-10101012"]["label"] == "10101012"

    assert "PROC-40301001" in nodes_by_id
    assert nodes_by_id["PROC-40301001"]["type"] == "procedimento"
    assert nodes_by_id["PROC-40301001"]["label"] == "40301001"

    proc_links = [l for l in result["links"] if l["relation"] == "contem_procedimento"]
    assert len(proc_links) == 2
    assert {l["target"] for l in proc_links} == {"PROC-10101012", "PROC-40301001"}


def test_build_graph_from_claims_shared_entities_and_degrees():
    """Verifica conexão de múltiplos sinistros compartilhando médico, paciente e clínica, testando contagem de grau."""
    engine = GraphEngine()
    claims = [
        {
            "document_id": "DOC-A",
            "paciente_id": "PAC-SHARED",
            "crm_profissional": "CRM-SHARED",
            "clinica_id": "CLIN-SHARED",
        },
        {
            "document_id": "DOC-B",
            "paciente_id": "PAC-SHARED",
            "crm_profissional": "CRM-SHARED",
            "clinica_id": "CLIN-SHARED",
        },
    ]

    result = engine.build_graph_from_claims(claims)

    nodes_by_id = {n["id"]: n for n in result["nodes"]}

    # 2 documentos + 1 paciente + 1 profissional + 1 clínica = 5 nós
    assert len(result["nodes"]) == 5
    # Cada documento tem 3 arestas -> 6 arestas total
    assert len(result["links"]) == 6

    # O paciente e profissional compartilhados se conectam a ambos os documentos (degree = 2)
    assert nodes_by_id["PAC-SHARED"]["degree"] == 2
    assert nodes_by_id["CRM-SHARED"]["degree"] == 2
    assert nodes_by_id["CLIN-SHARED"]["degree"] == 2

    # Cada documento conecta-se ao paciente, profissional e clínica (degree = 3)
    assert nodes_by_id["DOC-A"]["degree"] == 3
    assert nodes_by_id["DOC-B"]["degree"] == 3
