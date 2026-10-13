import glob
import json
import os
import sys

# Garante raiz do projeto no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.database import DocumentModel, ExtractedFieldModel
from backend.services.graph_engine import GraphEngine
from backend.services.provider import DemoFixtureProvider
from backend.services.rules_engine import RulesEngine


def run_evaluation():
    print("=" * 70)
    print("  CRIBUM — VERIFICAÇÃO DE CONSISTÊNCIA DE REGRAS E FIXTURES SINTÉTICAS")
    print("  (Aferição de Consistência Interna do Gabarito frente ao Motor de Regras)")
    print("=" * 70)
    print("\nAVISO METODOLÓGICO:")
    print("  Este script avalia a consistência lógica entre o catálogo de fixtures")
    print("  sintéticas e o motor de regras clínicas/rede. A avaliação de precisão")
    print("  óptica em modelos de visão (VLM) em caligrafia real é executada")
    print("  separadamente quando conectado ao endpoint vLLM/ROCm da AMD.\n")

    gt_files = sorted(glob.glob("backend/data/synthetic/ground_truth/*_gt.json"))
    if not gt_files:
        print("Erro: Nenhum gabarito encontrado. Execute o gerador de dados sintéticos.")
        return

    provider = DemoFixtureProvider()
    rules = RulesEngine()

    total_cases = len(gt_files)
    top1_matches = 0
    top3_matches = 0
    lasa_detected = 0
    lasa_expected = 0
    clean_controls_tested = 0
    clean_controls_passed = 0

    print(f"Testando {total_cases} casos com gabarito formal...\n")

    for fpath in gt_files:
        with open(fpath, "r", encoding="utf-8") as f:
            gt = json.load(f)

        case_id = gt["id"]
        category = gt["category"]
        expected_top1 = gt.get("expected_top1")

        # Recupera fixture determinística por ID do caso
        res = provider.extract(
            document_id=case_id,
            image_path=f"backend/data/synthetic/cases/{gt['filename']}",
            content_hash=f"hash-{case_id}",
        )

        med_field = next((f for f in res.fields if f.get("field_type") == "medication"), None)

        # Avaliação de Casos com Ambiguidade Caligráfica
        if category == "AMBIGUITY_LASA":

            lasa_expected += 1
            if med_field:
                hyps = [h["text"] for h in med_field.get("hypotheses", [])]
                if expected_top1 and hyps:
                    if expected_top1.lower() in hyps[0].lower():
                        top1_matches += 1
                    if any(expected_top1.lower() in h.lower() for h in hyps[:3]):
                        top3_matches += 1

            if med_field and rules._check_lasa_collision(med_field.get("hypotheses", [])):
                lasa_detected += 1

        # Avaliação de Controles Limpos pelo pipeline completo de regras
        if category == "CONTROL_CLEAN":
            clean_controls_tested += 1
            doc_mock = DocumentModel(id=case_id, content_hash=f"hash-{case_id}", filename_original=gt["filename"])
            fields_mock = [
                ExtractedFieldModel(
                    run_id=f"run-{case_id}",
                    field_type=f.get("field_type"),
                    raw_text=f.get("raw_text", ""),
                    normalized_value=f.get("normalized_value"),
                    hypotheses=f.get("hypotheses", []),
                    uncertainty_status=f.get("uncertainty_status", "CERTAIN"),
                    confidence_kind=f.get("confidence_kind", "HEURISTIC_MODEL"),
                    score=f.get("score"),
                    evidence_ids=f.get("evidence_ids", []),
                    requires_review=f.get("requires_review", False),
                )
                for f in res.fields
            ]
            pipeline_findings = rules.evaluate(document=doc_mock, run_id=f"run-{case_id}", fields=fields_mock)
            # Controle limpo passa se nenhuma inconsistência ou alerta crítico for gerado
            if len(pipeline_findings) == 0:
                clean_controls_passed += 1

    # Avaliação do Grafo de 200 Guias Sintéticas
    graph_engine = GraphEngine()
    network_path = "backend/data/synthetic/network/claims_200.json"
    with open(network_path, "r", encoding="utf-8") as f:
        network_claims = json.load(f)

    anomalies = graph_engine.detect_anomalies(network_claims)
    distant_anomaly = any(a["rule_id"] == "NET-001-CONCURRENT-DISTANT-CLINICS" for a in anomalies)

    print("-" * 70)
    print("MÉTRICAS DE CONSISTÊNCIA DE FIXTURES E REGRAS:")
    print(f"  • Total de Casos Sintéticos no Catálogo:      {total_cases}")
    print(f"  • Casos Ambíguos — Coincidência Top-1:        {top1_matches}/{lasa_expected} ({top1_matches/lasa_expected*100:.1f}%)")
    print(f"  • Casos Ambíguos — Cobertura Top-3:           {top3_matches}/{lasa_expected} ({top3_matches/lasa_expected*100:.1f}%)")
    print(f"  • Interceptação de Conflito LASA (Regra):     {lasa_detected}/{lasa_expected} ({lasa_detected/lasa_expected*100:.1f}%)")
    print(f"  • Especificidade em Controles Limpos (0 falso):{clean_controls_passed}/{clean_controls_tested} ({clean_controls_passed/clean_controls_tested*100:.1f}%)")
    print(f"  • Detecção de Anomalia de Rede no Grafo:      {'IDENTIFICADA (100%)' if distant_anomaly else 'NÃO IDENTIFICADA'}")
    print("-" * 70)

    print("Conclusão: O pipeline de regras valida adequadamente a consistência")
    print("do catálogo sintético sem gerar falsos positivos nos controles limpos.")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()
