import json
import os
import random
from typing import Any, Dict, List
from PIL import Image, ImageDraw, ImageFont

# Seed fixa para total reprodutibilidade científica do benchmark
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BASE_DIR = os.path.abspath("backend/data/synthetic")
CASES_DIR = os.path.join(BASE_DIR, "cases")
GROUND_TRUTH_DIR = os.path.join(BASE_DIR, "ground_truth")
NETWORK_DIR = os.path.join(BASE_DIR, "network")

for d in [CASES_DIR, GROUND_TRUTH_DIR, NETWORK_DIR]:
    os.makedirs(d, exist_ok=True)


def create_synthetic_image(filename: str, title: str, lines: List[str], banner: str = "SYNTHETIC / DEMO DATASET") -> str:
    """Renderiza uma imagem sintética nítida imitando formulário de receituário/guia médica."""
    width, height = 800, 1050
    image = Image.new("RGB", (width, height), color=(253, 252, 249))
    draw = ImageDraw.Draw(image)

    # Marca d'água de dado sintético
    draw.rectangle([0, 0, width, 40], fill=(230, 235, 240))
    draw.text((20, 12), f"⚠️ {banner} — NÃO CONTÉM DADOS REAIS", fill=(70, 80, 95))

    # Moldura do formulário
    draw.rectangle([40, 60, width - 40, height - 60], outline=(180, 185, 190), width=2)

    # Cabeçalho da clínica
    draw.rectangle([40, 60, width - 40, 140], fill=(245, 247, 250))
    draw.text((60, 80), title, fill=(20, 30, 45))
    draw.text((60, 105), "AUDITRX / CRIBUM SYNTHETIC HEALTHCARE CORP", fill=(100, 110, 120))

    # Linhas de conteúdo
    y_cursor = 180
    for line in lines:
        if line.startswith("---"):
            draw.line([(60, y_cursor), (width - 60, y_cursor)], fill=(200, 205, 210), width=1)
            y_cursor += 20
        elif line.startswith("[BOX]"):
            # Linha destacada imitando caligrafia ou campo assinado
            box_text = line.replace("[BOX]", "").strip()
            draw.rectangle([60, y_cursor - 5, width - 60, y_cursor + 35], fill=(240, 242, 245), outline=(150, 160, 170))
            draw.text((75, y_cursor + 5), box_text, fill=(10, 20, 30))
            y_cursor += 50
        else:
            draw.text((60, y_cursor), line, fill=(30, 40, 50))
            y_cursor += 28

    # Rodapé de validação e assinatura
    draw.line([(60, height - 120), (width - 60, height - 120)], fill=(200, 205, 210), width=1)
    draw.text((60, height - 100), "Hash de Verificação: [CRIBUM-SYNTHETIC-HASH-REPRODUCIBLE]", fill=(140, 145, 150))
    draw.text((width - 320, height - 100), "Assinatura: Profissional Resp. (Digital)", fill=(140, 145, 150))

    file_path = os.path.join(CASES_DIR, filename)
    image.save(file_path, "JPEG", quality=92)
    return file_path


def build_synthetic_20_cases():
    """Gera os 20 casos sintéticos documentais distribuídos nos 4 grupos metodológicos."""
    cases_manifest = []
    fixtures_dict = {}

    # GRUPO 1: 5 casos com ambiguidade de leitura (LASA e caligrafia dúbia)
    grupo_1 = [
        {
            "id": "CASE-AMB-001",
            "filename": "caso_01_losartana_lorazepam.jpg",
            "title": "CLÍNICA CARDIOLÓGICA MODELO — RECEITUÁRIO",
            "crm": "142857-SP",
            "paciente": "PACIENTE-DEMO-001",
            "lines": [
                "Paciente: PACIENTE-DEMO-001 | Data: 2026-10-12 | CRM: 142857-SP",
                "Diagnóstico Sugerido: CID-10 I10 (Hipertensão Essencial)",
                "---",
                "PRESCRIÇÃO MÉDICA:",
                "[BOX] Losartana 50mg / Lorazepam 2mg (caligrafia ambígua)",
                "Uso Oral: Tomar 1 comprimido pela manhã em jejum",
                "---",
                "Observação: Paciente relata cefaleia matinal frequente.",
            ],
            "ambiguous": True,
            "expected_findings": ["MED-001-AMBIGUOUS-READING", "MED-002-LASA-LASA-001"],
            "expected_top1": "Losartana 50mg",
            "expected_top2": "Lorazepam 2mg",
            "category": "AMBIGUITY_LASA",
            "box": [320, 75, 370, 725]  # raw coordinates in 800x1050
        },
        {
            "id": "CASE-AMB-002",
            "filename": "caso_02_fluoxetina_flunarizina.jpg",
            "title": "INSTITUTO DE SAÚDE MENTAL DEMO",
            "crm": "119988-SP",
            "paciente": "PACIENTE-DEMO-002",
            "lines": [
                "Paciente: PACIENTE-DEMO-002 | Data: 2026-10-10 | CRM: 119988-SP",
                "Diagnóstico: CID-10 F32.1 (Episódio Depressivo Moderado)",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Fluoxetina 20mg / Flunarizina 10mg (traço cursivo duvidoso)",
                "Posologia: 1 cápsula ao dia pela manhã.",
            ],
            "ambiguous": True,
            "expected_findings": ["MED-001-AMBIGUOUS-READING", "MED-002-LASA-LASA-003"],
            "expected_top1": "Fluoxetina 20mg",
            "expected_top2": "Flunarizina 10mg",
            "category": "AMBIGUITY_LASA",
            "box": [280, 75, 330, 725]
        },
        {
            "id": "CASE-AMB-003",
            "filename": "caso_03_digoxina_dipirona.jpg",
            "title": "HOSPITAL REGIONAL DE ENSINO DEMO",
            "crm": "887766-SP",
            "paciente": "PACIENTE-DEMO-003",
            "lines": [
                "Paciente: PACIENTE-DEMO-003 | Data: 2026-10-11 | CRM: 887766-SP",
                "Diagnóstico: CID-10 I50 (Insuficiência Cardíaca)",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Digoxina 0.25mg / Dipirona 500mg",
                "Tomar conforme orientação clínica estrita.",
            ],
            "ambiguous": True,
            "expected_findings": ["MED-001-AMBIGUOUS-READING", "MED-002-LASA-LASA-004"],
            "expected_top1": "Digoxina 0.25mg",
            "expected_top2": "Dipirona 500mg",
            "category": "AMBIGUITY_LASA",
            "box": [280, 75, 330, 725]
        },
        {
            "id": "CASE-AMB-004",
            "filename": "caso_04_citalopram_escitalopram.jpg",
            "title": "CENTRO CLÍNICO INTEGRADO DEMO",
            "crm": "554433-SP",
            "paciente": "PACIENTE-DEMO-004",
            "lines": [
                "Paciente: PACIENTE-DEMO-004 | Data: 2026-10-09 | CRM: 554433-SP",
                "Diagnóstico: CID-10 F41.1 (Ansiedade Generalizada)",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Citalopram 20mg / Escitalopram 10mg",
                "Uso contínuo: 1 cp via oral ao dia.",
            ],
            "ambiguous": True,
            "expected_findings": ["MED-001-AMBIGUOUS-READING", "MED-002-LASA-LASA-002"],
            "expected_top1": "Citalopram 20mg",
            "expected_top2": "Escitalopram 10mg",
            "category": "AMBIGUITY_LASA",
            "box": [280, 75, 330, 725]
        },
        {
            "id": "CASE-AMB-005",
            "filename": "caso_05_tramadol_trazodona.jpg",
            "title": "CLÍNICA DA DOR E CUIDADOS ESPECIAIS DEMO",
            "crm": "332211-SP",
            "paciente": "PACIENTE-DEMO-005",
            "lines": [
                "Paciente: PACIENTE-DEMO-005 | Data: 2026-10-08 | CRM: 332211-SP",
                "Diagnóstico: CID-10 M54.5 (Dor Lombar Baixa)",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Tramadol 50mg / Trazodona 50mg",
                "Tomar 1 comprimido à noite se dor intensa.",
            ],
            "ambiguous": True,
            "expected_findings": ["MED-001-AMBIGUOUS-READING", "MED-002-LASA-LASA-006"],
            "expected_top1": "Tramadol 50mg",
            "expected_top2": "Trazodona 50mg",
            "category": "AMBIGUITY_LASA",
            "box": [280, 75, 330, 725]
        },
    ]

    # GRUPO 2: 5 casos com inconsistências documentais ou campos ausentes
    grupo_2 = [
        {
            "id": "CASE-INC-006",
            "filename": "caso_06_sem_crm.jpg",
            "title": "CONSULTÓRIO PARTICULAR DEMO",
            "crm": None,  # CRM ausente intencionalmente
            "paciente": "PACIENTE-DEMO-006",
            "lines": [
                "Paciente: PACIENTE-DEMO-006 | Data: 2026-10-12 | MÉDICO NÃO IDENTIFICADO",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Amoxicilina + Clavulanato 875mg",
                "Tomar 1 comprimido de 12 em 12 horas por 7 dias.",
            ],
            "ambiguous": False,
            "expected_findings": ["DOC-002-MISSING-CRM"],
            "category": "DOCUMENT_INCONSISTENCY",
            "box": [240, 75, 290, 725]
        },
        {
            "id": "CASE-INC-007",
            "filename": "caso_07_sem_unidade.jpg",
            "title": "POLICLÍNICA CENTRAL DEMO",
            "crm": "224466-SP",
            "paciente": "PACIENTE-DEMO-007",
            "lines": [
                "Paciente: PACIENTE-DEMO-007 | Data: 2026-10-12 | CRM: 224466-SP",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Paracetamol 500 (sem unidade mg ou ml)",
                "Tomar se febre acima de 38°C.",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "DOCUMENT_INCONSISTENCY",
            "box": [240, 75, 290, 725]
        },
        {
            "id": "CASE-INC-008",
            "filename": "caso_08_crm_incompleto.jpg",
            "title": "HOSPITAL GERAL DE RETAGUARDA DEMO",
            "crm": None,
            "paciente": "PACIENTE-DEMO-008",
            "lines": [
                "Paciente: PACIENTE-DEMO-008 | Data: 2026-10-11 | Carimbo ilegível rasurado",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Cefalexina 500mg",
                "Tomar 1 cápsula de 6 em 6 horas.",
            ],
            "ambiguous": False,
            "expected_findings": ["DOC-002-MISSING-CRM"],
            "category": "DOCUMENT_INCONSISTENCY",
            "box": [240, 75, 290, 725]
        },
        {
            "id": "CASE-INC-009",
            "filename": "caso_09_cid_incompativel.jpg",
            "title": "CLÍNICA CIRÚRGICA DEMO",
            "crm": "771122-SP",
            "paciente": "PACIENTE-DEMO-009",
            "lines": [
                "Paciente: PACIENTE-DEMO-009 | Data: 2026-10-10 | CRM: 771122-SP",
                "Diagnóstico Declarado: CID-10 J00 (Nasofaringite aguda - Resfriado comum)",
                "---",
                "PROCEDIMENTO SOLICITADO:",
                "[BOX] Artroplastia Total de Quadril Direito",
                "Justificativa: Procedimento de alta complexidade em regime hospitalar.",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "DOCUMENT_INCONSISTENCY",
            "box": [280, 75, 330, 725]
        },
        {
            "id": "CASE-INC-010",
            "filename": "caso_10_posologia_contraditoria.jpg",
            "title": "AMBULATÓRIO DE ESPECIALIDADES DEMO",
            "crm": "993311-SP",
            "paciente": "PACIENTE-DEMO-010",
            "lines": [
                "Paciente: PACIENTE-DEMO-010 | Data: 2026-10-09 | CRM: 993311-SP",
                "---",
                "PRESCRIÇÃO:",
                "[BOX] Insulina NPH 100 UI",
                "Posologia contraditória: 'Tomar 30 comprimidos via oral ao deitar'",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "DOCUMENT_INCONSISTENCY",
            "box": [240, 75, 290, 725]
        },
    ]

    # GRUPO 3: 5 casos de duplicidade e controle de integridade de arquivo
    grupo_3 = [
        {
            "id": f"CASE-DUP-{i:03d}",
            "filename": f"caso_{i}_duplicidade_declarada.jpg",
            "title": "HOSPITAL SANTA LUZIA DEMO — REENVIO",
            "crm": "665544-SP",
            "paciente": f"PACIENTE-DEMO-{i:03d}",
            "lines": [
                f"Paciente: PACIENTE-DEMO-{i:03d} | Data: 2026-10-12 | CRM: 665544-SP",
                "---",
                "PROCEDIMENTO / PRESCRIÇÃO:",
                "[BOX] Ressonância Magnética de Crânio com Contraste",
                f"Lote de auditoria: LOTE-REPETICAO-00{i-10}",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "DUPLICATE_CLAIM",
            "box": [240, 75, 290, 725]
        }
        for i in range(11, 16)
    ]

    # GRUPO 4: 5 controles normais (sem alertas esperados)
    grupo_4 = [
        {
            "id": f"CASE-CTR-{i:03d}",
            "filename": f"caso_{i}_controle_limpo.jpg",
            "title": "CLÍNICA GERAL DA FAMÍLIA DEMO",
            "crm": f"12345{i}-SP",
            "paciente": f"PACIENTE-DEMO-{i:03d}",
            "lines": [
                f"Paciente: PACIENTE-DEMO-{i:03d} | Data: 2026-10-12 | CRM: 12345{i}-SP",
                "Diagnóstico: CID-10 J06.9 (Infecção aguda das vias aéreas superiores)",
                "---",
                "PRESCRIÇÃO NORMAL:",
                f"[BOX] Dipirona Monoidratada 500mg/ml gotas",
                "Tomar 30 gotas a cada 6 horas se dor ou febre.",
                "---",
                "Uso por até 3 dias. Repouso e hidratação oral recomendados.",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "CONTROL_CLEAN",
            "box": [280, 75, 330, 725]
        }
        for i in range(16, 21)
    ]

    todos_casos = grupo_1 + grupo_2 + grupo_3 + grupo_4

    for caso in todos_casos:
        # Gera a imagem real e salva em backend/data/synthetic/cases/
        img_path = create_synthetic_image(caso["filename"], caso["title"], caso["lines"])

        # Coordenadas normalizadas 0..1
        raw_b = caso.get("box", [250, 75, 300, 725])
        norm_bbox = {
            "x_min": round(raw_b[1] / 800.0, 4),
            "y_min": round(raw_b[0] / 1050.0, 4),
            "x_max": round(raw_b[3] / 800.0, 4),
            "y_max": round(raw_b[2] / 1050.0, 4),
        }

        # Constrói fixture para o DemoFixtureProvider
        ev_id = f"ev-item-{caso['id']}"
        hypotheses = []
        if caso["ambiguous"]:
            hypotheses = [
                {"text": caso["expected_top1"], "rank": 1, "score": 0.65, "score_kind": "HEURISTIC_MODEL", "supporting_evidence_ids": [ev_id]},
                {"text": caso["expected_top2"], "rank": 2, "score": 0.25, "score_kind": "HEURISTIC_MODEL", "supporting_evidence_ids": [ev_id]},
                {"text": "Opção alternativa plausível", "rank": 3, "score": 0.10, "score_kind": "HEURISTIC_MODEL", "supporting_evidence_ids": [ev_id]}
            ]
            uncertainty = "AMBIGUOUS"
        else:
            hypotheses = [
                {"text": caso["lines"][4].replace("[BOX]", "").strip(), "rank": 1, "score": 0.98, "score_kind": "HEURISTIC_MODEL", "supporting_evidence_ids": [ev_id]}
            ]
            uncertainty = "CERTAIN"

        fixture_data = {
            "name": caso["title"],
            "document_id": caso["id"],
            "fields": [
                {
                    "id": f"field-med-{caso['id']}",
                    "run_id": f"run-{caso['id']}",
                    "field_type": "medication",
                    "raw_text": hypotheses[0]["text"],
                    "normalized_value": hypotheses[0]["text"],
                    "hypotheses": hypotheses,
                    "uncertainty_status": uncertainty,
                    "confidence_kind": "HEURISTIC_MODEL",
                    "score": hypotheses[0]["score"],
                    "evidence_ids": [ev_id],
                    "requires_review": (uncertainty != "CERTAIN"),
                }
            ],
            "evidences": [
                {
                    "id": ev_id,
                    "document_id": caso["id"],
                    "page": 1,
                    "bbox": norm_bbox,
                    "coordinate_system": "NORMALIZED_0_1",
                    "localization_status": "MANUAL_FIXTURE",
                    "source": "FIXTURE",
                    "excerpt": caso["lines"][4].replace("[BOX]", "").strip(),
                }
            ]
        }

        if caso["crm"]:
            ev_crm_id = f"ev-crm-{caso['id']}"
            fixture_data["fields"].append({
                "id": f"field-crm-{caso['id']}",
                "run_id": f"run-{caso['id']}",
                "field_type": "crm",
                "raw_text": caso["crm"],
                "normalized_value": caso["crm"],
                "hypotheses": [{"text": caso["crm"], "rank": 1, "score": 0.99, "score_kind": "HEURISTIC_MODEL", "supporting_evidence_ids": [ev_crm_id]}],
                "uncertainty_status": "CERTAIN",
                "confidence_kind": "HEURISTIC_MODEL",
                "score": 0.99,
                "evidence_ids": [ev_crm_id],
                "requires_review": False,
            })
            fixture_data["evidences"].append({
                "id": ev_crm_id,
                "document_id": caso["id"],
                "page": 1,
                "bbox": {"x_min": 0.08, "y_min": 0.16, "x_max": 0.45, "y_max": 0.20},
                "coordinate_system": "NORMALIZED_0_1",
                "localization_status": "MANUAL_FIXTURE",
                "source": "FIXTURE",
                "excerpt": f"CRM {caso['crm']}",
            })

        fixtures_dict[caso["filename"]] = fixture_data
        fixtures_dict[caso["id"]] = fixture_data

        # Salva o gabarito oficial em ground_truth
        with open(os.path.join(GROUND_TRUTH_DIR, f"{caso['id']}_gt.json"), "w", encoding="utf-8") as f:
            json.dump(caso, f, indent=2, ensure_ascii=False)

        cases_manifest.append({
            "id": caso["id"],
            "filename": caso["filename"],
            "category": caso["category"],
            "ambiguous": caso["ambiguous"],
            "expected_findings": caso["expected_findings"],
        })

    # Salva o arquivo de fixtures consolidado
    fixtures_file = os.path.join(BASE_DIR, "fixtures.json")
    with open(fixtures_file, "w", encoding="utf-8") as f:
        json.dump(fixtures_dict, f, indent=2, ensure_ascii=False)

    return cases_manifest


def build_synthetic_200_network_claims():
    """Gera o dataset de 200 guias médicas para teste de grafo do agente Investigador."""
    clinicas = [
        {"id": "CLINICA-DEMO-001", "nome": "Hospital Santa Cruz", "cidade": "Sorocaba"},
        {"id": "CLINICA-DEMO-002", "nome": "Centro Médico Campinas", "cidade": "Campinas"},
        {"id": "CLINICA-DEMO-003", "nome": "Hospital Metropolitano", "cidade": "São Paulo"},
        {"id": "CLINICA-DEMO-004", "nome": "Clínica Vale do Paraíba", "cidade": "São José dos Campos"},
        {"id": "CLINICA-DEMO-005", "nome": "Instituto do Litoral", "cidade": "Santos"},
    ]

    profissionais = [f"PROF-DEMO-{i:03d}" for i in range(1, 25)]
    pacientes = [f"PACIENTE-DEMO-{i:03d}" for i in range(1, 100)]
    procedimentos_lista = [
        "Consulta Médica em Atenção Primária",
        "Eletrocardiograma de Repouso",
        "Hemograma Completo",
        "Ultrassonografia Abdominal",
        "Ressonância Magnética",
        "Endoscopia Digestiva Alta",
        "Sessão de Fisioterapia Motora",
        "Ecocardiograma Transtorácico"
    ]

    claims = []

    # Injeta intencionalmente anomalias de rede para validação de fraude:
    # Esquema 1: Médico PROF-DEM-007 atende em Sorocaba e Santos (distância 180km) no mesmo dia (2026-10-14)
    data_esquema = "2026-10-14"
    for k in range(1, 4):
        claims.append({
            "id": f"CLAIM-NET-{len(claims)+1:03d}",
            "crm_profissional": "PROF-DEMO-007",
            "paciente_id": f"PACIENTE-DEMO-{k:03d}",
            "clinica_id": "CLINICA-DEMO-001",
            "cidade": "Sorocaba",
            "data": data_esquema,
            "procedimentos": ["Consulta Médica em Atenção Primária", "Eletrocardiograma de Repouso"],
            "valor_centavos": 25000,
            "anomalia_injetada": "DISTANCIA_IMPOSSIVEL"
        })
    for k in range(4, 7):
        claims.append({
            "id": f"CLAIM-NET-{len(claims)+1:03d}",
            "crm_profissional": "PROF-DEMO-007",
            "paciente_id": f"PACIENTE-DEMO-{k:03d}",
            "clinica_id": "CLINICA-DEMO-005",
            "cidade": "Santos",
            "data": data_esquema,
            "procedimentos": ["Endoscopia Digestiva Alta"],
            "valor_centavos": 90000,
            "anomalia_injetada": "DISTANCIA_IMPOSSIVEL"
        })

    # Restante das 200 guias: distribuição legítima e variada
    datas = [f"2026-10-{d:02d}" for d in range(1, 15)]
    while len(claims) < 200:
        c_info = random.choice(clinicas)
        claims.append({
            "id": f"CLAIM-NET-{len(claims)+1:03d}",
            "crm_profissional": random.choice(profissionais),
            "paciente_id": random.choice(pacientes),
            "clinica_id": c_info["id"],
            "cidade": c_info["cidade"],
            "data": random.choice(datas),
            "procedimentos": [random.choice(procedimentos_lista)],
            "valor_centavos": random.randint(15000, 120000),
            "anomalia_injetada": None
        })

    network_file = os.path.join(NETWORK_DIR, "claims_200.json")
    with open(network_file, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)

    return len(claims)


if __name__ == "__main__":
    manifest = build_synthetic_20_cases()
    net_count = build_synthetic_200_network_claims()

    manifest_file = os.path.join(BASE_DIR, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({
            "seed": RANDOM_SEED,
            "total_document_cases": len(manifest),
            "total_network_claims": net_count,
            "cases": manifest
        }, f, indent=2, ensure_ascii=False)

    print(f"Sucesso! Gerados {len(manifest)} casos documentais sintéticos e {net_count} registros de rede.")
