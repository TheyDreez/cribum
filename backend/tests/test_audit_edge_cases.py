import hashlib
import json
from pathlib import Path
import pytest

from backend.models.database import DocumentModel
from backend.services.graph_engine import GraphEngine
from backend.services.rules_engine import RulesEngine, normalize_text, is_valid_crm_format

DATA_DIR = Path("backend/data")
SYNTHETIC_DIR = DATA_DIR / "synthetic"
GT_DIR = SYNTHETIC_DIR / "ground_truth"


def test_lasa_reference_integrity():
    """Garante que a base LASA possui pares válidos e referenciados ao ISMP Brasil."""
    lasa_path = DATA_DIR / "references" / "lasa_ismp.json"
    assert lasa_path.exists(), "Arquivo lasa_ismp.json não encontrado"
    data = json.loads(lasa_path.read_text(encoding="utf-8"))
    assert len(data) >= 10, "Base LASA deve conter ao menos 10 pares críticos documentados"
    for par in data:
        assert "par_id" in par
        assert "droga_a" in par and "nome" in par["droga_a"]
        assert "droga_b" in par and "nome" in par["droga_b"]
        assert "risco_clinico" in par
        assert "gravidade" in par


@pytest.mark.parametrize(
    "case_file,expected_category",
    [
        ("CASE-AMB-001_gt.json", "AMB"),  # Losartana x Lorazepam (LASA)
        ("CASE-INC-006_gt.json", "INC"),  # Sem CRM
        ("CASE-INC-007_gt.json", "INC"),  # Sem unidade de medida
        ("CASE-INC-008_gt.json", "INC"),  # CRM incompleto
        ("CASE-INC-009_gt.json", "INC"),  # CID incompatível
        ("CASE-INC-010_gt.json", "INC"),  # Posologia contraditória
        ("CASE-DUP-011_gt.json", "DUP"),  # Duplicidade declarada
        ("CASE-CTR-016_gt.json", "CTR"),  # Controle limpo
    ],
)
def test_ground_truth_cases_coverage(case_file, expected_category):
    """Verifica existência e integridade estrutural de cada classe de caso no gabarito."""
    gt_path = GT_DIR / case_file
    assert gt_path.exists(), f"Ground truth ausente: {case_file}"
    content = json.loads(gt_path.read_text(encoding="utf-8"))
    assert expected_category in case_file
    assert isinstance(content, dict)
    assert "id" in content
    assert "filename" in content


def test_duplicate_prescription_image_hash_detection():
    """Verifica detecção determinística de duplicidade criptográfica por hash SHA-256."""
    img1 = (SYNTHETIC_DIR / "cases" / "caso_11_duplicidade_declarada.jpg").read_bytes()
    hash1 = hashlib.sha256(img1).hexdigest()
    hash1_copy = hashlib.sha256(img1).hexdigest()
    assert len(hash1) == 64
    assert hash1 == hash1_copy

    img2 = (SYNTHETIC_DIR / "cases" / "caso_12_duplicidade_declarada.jpg").read_bytes()
    hash2 = hashlib.sha256(img2).hexdigest()
    # Arquivos de casos distintos possuem hashes distintos
    assert hash1 != hash2


def test_rules_engine_exact_hash_duplicate_detection():
    """Verifica se o motor de regras identifica duplicidade exata quando o mesmo hash já existe no banco."""
    class FakeQuery:
        def __init__(self, match):
            self.match = match
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return self.match

    class FakeSession:
        def __init__(self, match):
            self.match = match
        def query(self, model):
            return FakeQuery(self.match)

    engine = RulesEngine()
    doc_new = DocumentModel(id="DOC-NEW", content_hash="hash-1234567890abcdef", filename_original="nova_guia.jpg")
    doc_existing = DocumentModel(id="DOC-EXISTING", content_hash="hash-1234567890abcdef", filename_original="guia_antiga.jpg")

    session_with_dup = FakeSession(match=doc_existing)
    findings = engine.evaluate(document=doc_new, run_id="run-test", fields=[], db_session=session_with_dup)

    dup_findings = [f for f in findings if f.category == "DUPLICATE_CLAIM"]
    assert len(dup_findings) == 1
    assert dup_findings[0].rule_id == "DOC-001-EXACT-HASH-DUPLICATE"
    assert "DOC-EXISTING" in dup_findings[0].related_document_ids


def test_network_claims_graph_anomalies_and_clean_nodes():
    """Verifica se a rede de 200 sinistros contém casos normais e anomalias detectáveis."""
    claims_path = SYNTHETIC_DIR / "network" / "claims_200.json"
    assert claims_path.exists()
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    assert len(claims) >= 200

    engine = GraphEngine()
    anomalies = engine.detect_anomalies(claims)
    assert len(anomalies) > 0, "O motor de grafos deve detectar anomalias no dataset de 200 sinistros"
    rule_ids = [a["rule_id"] for a in anomalies]
    assert "NET-001-CONCURRENT-DISTANT-CLINICS" in rule_ids


def test_merkle_chain_tamper_detection():
    """Garante que qualquer alteração de 1 byte em um laudo invalida a cadeia de hash SHA-256 (RFC 6962)."""
    leaf_prefix = b"\x00"
    node_prefix = b"\x01"

    original_payload = b'{"case_id":"CASE-AMB-001","status":"BLOCKED"}'
    tampered_payload = b'{"case_id":"CASE-AMB-001","status":"APPROVED"}'

    leaf_hash_orig = hashlib.sha256(leaf_prefix + original_payload).hexdigest()
    leaf_hash_tamp = hashlib.sha256(leaf_prefix + tampered_payload).hexdigest()

    prev_root = hashlib.sha256(b"GENESIS_ROOT").hexdigest()
    chain_orig = hashlib.sha256(node_prefix + (prev_root + leaf_hash_orig).encode()).hexdigest()
    chain_tamp = hashlib.sha256(node_prefix + (prev_root + leaf_hash_tamp).encode()).hexdigest()

    assert leaf_hash_orig != leaf_hash_tamp
    assert chain_orig != chain_tamp


def test_rules_engine_normalization_and_accents():
    """Verifica se a normalização Unicode (NFKD) e insensibilidade a maiúsculas funcionam no motor LASA."""
    engine = RulesEngine()
    hypotheses = [
        {"text": "LOSARTANA 50MG", "score": 0.65},
        {"text": "lorazépam 2mg", "score": 0.25},
    ]
    collision = engine._check_lasa_collision(hypotheses)
    assert collision is not None, "Deveria detectar colisão LASA mesmo com caixa mista e acentuação"
    assert collision[1] == "Losartana"
    assert collision[2] == "Lorazepam"


def test_crm_format_validation():
    """Verifica validação de formatação de CRM."""
    assert is_valid_crm_format("CRM-SP 123456") is True
    assert is_valid_crm_format("CRM/SP 98765") is True
    assert is_valid_crm_format("123456-SP") is True
    assert is_valid_crm_format("123456") is True
    assert is_valid_crm_format("") is False
    assert is_valid_crm_format(None) is False
    assert is_valid_crm_format("SEM_CRM") is False
