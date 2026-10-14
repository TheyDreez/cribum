import hashlib
import io
import json
import os
import random
from typing import Any, Dict, List, Optional
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


def load_font(candidates: List[str], size: int) -> ImageFont.FreeTypeFont:
    """
    Busca fontes TrueType no sistema (Windows/Linux/macOS) e também no pacote matplotlib
    (já instalado no requirements.txt) para garantir 100% de suporte a UTF-8 e acentuação.
    """
    font_dirs = [
        "C:/Windows/Fonts",
        "/mnt/c/Windows/Fonts",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/System/Library/Fonts",
    ]
    try:
        import matplotlib
        mpl_fonts = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
        if os.path.exists(mpl_fonts):
            font_dirs.append(mpl_fonts)
    except Exception:
        pass

    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                pass
        for d in font_dirs:
            full_path = os.path.join(d, candidate)
            if os.path.exists(full_path):
                try:
                    return ImageFont.truetype(full_path, size)
                except Exception:
                    pass

    return ImageFont.load_default()


def create_synthetic_image(
    filename: str,
    title: str,
    lines: List[str],
    box_coords: List[int],
    crm: Optional[str] = None,
    ambiguous: bool = False,
    banner: str = "SYNTHETIC / DEMO DATASET",
) -> str:
    """Renderiza uma guia médica / receituário clínico de alta definição (800x1050) sem glifos corrompidos."""
    width, height = 800, 1050
    image = Image.new("RGB", (width, height), color=(252, 252, 250))
    draw = ImageDraw.Draw(image)

    # Fontes TrueType com fallback garantido via DejaVu (matplotlib) ou Windows Fonts
    font_banner = load_font(["consolab.ttf", "consola.ttf", "DejaVuSansMono-Bold.ttf", "DejaVuSans-Bold.ttf"], 11)
    font_clinic = load_font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 18)
    font_sub = load_font(["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"], 11)
    font_label = load_font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 12)
    font_body = load_font(["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"], 14)
    font_mono = load_font(["consola.ttf", "DejaVuSansMono.ttf", "DejaVuSans.ttf"], 13)
    font_handwriting = load_font(
        ["segoesc.ttf", "georgiai.ttf", "timesi.ttf", "DejaVuSerif-Italic.ttf", "DejaVuSans-Oblique.ttf"],
        20 if ambiguous else 18,
    )

    # 1. Tarja institucional superior (Dataset Sintético)
    draw.rectangle([0, 0, width, 34], fill=(15, 23, 42))
    draw.text(
        (24, 10),
        f"DOCUMENTO SINTÉTICO PARA AUDITORIA ({banner}) — NÃO CONTÉM DADOS DE PACIENTES REAIS",
        fill=(226, 232, 240),
        font=font_banner,
    )

    # 2. Moldura dupla de formulário médico oficial
    draw.rectangle([36, 52, width - 36, height - 48], outline=(148, 163, 184), width=2)
    draw.rectangle([42, 58, width - 42, height - 54], outline=(226, 232, 240), width=1)

    # 3. Cabeçalho da Instituição de Saúde
    draw.rectangle([42, 58, width - 42, 142], fill=(241, 245, 249))
    draw.line([(42, 142), (width - 42, 142)], fill=(203, 213, 225), width=2)

    # Símbolo da Cruz Clínica
    draw.rectangle([62, 76, 106, 120], fill=(15, 23, 42))
    draw.rectangle([79, 84, 89, 112], fill=(255, 255, 255))
    draw.rectangle([70, 93, 98, 103], fill=(255, 255, 255))

    draw.text((122, 75), title, fill=(15, 23, 42), font=font_clinic)
    draw.text(
        (122, 103),
        "GUIA DE AUDITORIA E PRESCRIÇÃO ASSISTENCIAL — CONFORMIDADE TISS / FARMACOVIGILÂNCIA",
        fill=(71, 85, 105),
        font=font_sub,
    )

    # 4. Grade Cadastral: Paciente, Data, CRM e CID-10
    draw.rectangle([58, 154, width - 58, 222], fill=(255, 255, 255), outline=(203, 213, 225), width=1)
    draw.line([(58, 188), (width - 58, 188)], fill=(226, 232, 240), width=1)

    header_line = lines[0] if lines else ""
    diag_line = next(
        (l for l in lines[1:] if "Diagnóstico" in l or "CID" in l),
        "Diagnóstico Clínico: Não declarado no cabeçalho da guia",
    )

    draw.text((72, 164), header_line, fill=(15, 23, 42), font=font_mono)
    draw.text((72, 197), diag_line, fill=(30, 41, 59), font=font_body)

    # 5. Seção de Prescrição (Rx) e Box Ancorado nas Coordenadas Exatas
    box_ymin, box_xmin, box_ymax, box_xmax = box_coords
    section_label = next(
        (l for l in lines if "PRESCRI" in l.upper() or "PROCEDIMENTO" in l.upper()),
        "PRESCRIÇÃO MÉDICA:",
    )
    draw.text((75, box_ymin - 24), f"Rx   {section_label}", fill=(15, 23, 42), font=font_label)

    draw.rectangle(
        [box_xmin, box_ymin, box_xmax, box_ymax],
        fill=(254, 252, 232) if ambiguous else (248, 250, 252),
        outline=(148, 163, 184),
        width=2,
    )
    draw.line([(box_xmin + 14, box_ymax - 9), (box_xmax - 14, box_ymax - 9)], fill=(203, 213, 225), width=1)

    box_text = next((l.replace("[BOX]", "").strip() for l in lines if l.startswith("[BOX]")), "")
    draw.text(
        (box_xmin + 18, box_ymin + 12),
        box_text,
        fill=(15, 23, 42),
        font=font_handwriting,
    )

    # 6. Posologia e Orientações Médicas
    y_cursor = box_ymax + 26
    box_idx = next((i for i, l in enumerate(lines) if l.startswith("[BOX]")), 3)
    for line in lines[box_idx + 1 :]:
        if line.startswith("---"):
            draw.line([(62, y_cursor), (width - 62, y_cursor)], fill=(226, 232, 240), width=1)
            y_cursor += 20
        else:
            draw.text((75, y_cursor), f"•  {line}", fill=(30, 41, 59), font=font_body)
            y_cursor += 30

    # 7. Quadro de Carimbo Médico e Protocolo Pericial (y = 770 a 880)
    stamp_rect = [490, 770, 730, 880]
    if crm:
        draw.rectangle(stamp_rect, fill=(248, 250, 252), outline=(51, 65, 85), width=2)
        draw.text((508, 785), "CONSELHO REGIONAL DE MEDICINA", fill=(71, 85, 105), font=font_banner)
        draw.text((508, 808), f"CRM {crm}", fill=(15, 23, 42), font=font_clinic)
        draw.text((508, 840), "Carimbo e Rubrica do Prescritor", fill=(100, 116, 139), font=font_sub)
    else:
        draw.rectangle(stamp_rect, fill=(254, 242, 242), outline=(220, 38, 38), width=2)
        draw.text((508, 795), "CARIMBO AUSENTE / ILEGÍVEL", fill=(185, 28, 28), font=font_label)
        draw.text((508, 822), "Sem identificação válida de CRM", fill=(153, 27, 27), font=font_sub)

    draw.rectangle([62, 770, 460, 880], fill=(248, 250, 252), outline=(203, 213, 225), width=1)
    draw.text((78, 785), "METADADOS DE CUSTÓDIA DOCUMENTAL", fill=(51, 65, 85), font=font_label)
    draw.text((78, 810), f"Arquivo: {filename}", fill=(30, 41, 59), font=font_mono)
    draw.text((78, 834), "Padrão: CRIBUM FORENSIC WORKSTATION", fill=(100, 116, 139), font=font_mono)

    # 8. Rodapé com Código de Barras Simulado
    draw.line([(58, height - 115), (width - 58, height - 115)], fill=(203, 213, 225), width=1)
    for bx in range(62, 270, 4):
        bar_w = 2 if (bx % 8 == 0) else 1
        draw.rectangle([bx, height - 100, bx + bar_w, height - 70], fill=(15, 23, 42))

    draw.text(
        (290, height - 96),
        "Hash de Verificação: [CRIBUM-SYNTHETIC-HASH-REPRODUCIBLE]",
        fill=(71, 85, 105),
        font=font_mono,
    )
    draw.text(
        (290, height - 76),
        "Governança: Decisão assistida com revisão humana obrigatória (HITL)",
        fill=(100, 116, 139),
        font=font_sub,
    )

    file_path = os.path.join(CASES_DIR, filename)
    image.save(file_path, "JPEG", quality=95)
    return file_path


def build_synthetic_20_cases():
    """Gera os 20 casos sintéticos documentais distribuídos nos 4 grupos metodológicos."""
    cases_manifest = []
    fixtures_dict = {}

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
            "box": [320, 75, 370, 725],
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
            "box": [280, 75, 330, 725],
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
            "box": [280, 75, 330, 725],
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
            "box": [280, 75, 330, 725],
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
            "box": [280, 75, 330, 725],
        },
    ]

    grupo_2 = [
        {
            "id": "CASE-INC-006",
            "filename": "caso_06_sem_crm.jpg",
            "title": "CONSULTÓRIO PARTICULAR DEMO",
            "crm": None,
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
            "box": [260, 75, 310, 725],
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
            "box": [260, 75, 310, 725],
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
            "box": [260, 75, 310, 725],
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
            "box": [280, 75, 330, 725],
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
            "box": [260, 75, 310, 725],
        },
    ]

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
            "box": [260, 75, 310, 725],
        }
        for i in range(11, 16)
    ]

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
                "[BOX] Dipirona Monoidratada 500mg/ml gotas",
                "Tomar 30 gotas a cada 6 horas se dor ou febre.",
                "---",
                "Uso por até 3 dias. Repouso e hidratação oral recomendados.",
            ],
            "ambiguous": False,
            "expected_findings": [],
            "category": "CONTROL_CLEAN",
            "box": [280, 75, 330, 725],
        }
        for i in range(16, 21)
    ]

    todos_casos = grupo_1 + grupo_2 + grupo_3 + grupo_4

    for caso in todos_casos:
        raw_b = caso.get("box", [260, 75, 310, 725])
        img_path = create_synthetic_image(
            filename=caso["filename"],
            title=caso["title"],
            lines=caso["lines"],
            box_coords=raw_b,
            crm=caso.get("crm"),
            ambiguous=caso["ambiguous"],
        )

        norm_bbox = {
            "x_min": round(raw_b[1] / 800.0, 4),
            "y_min": round(raw_b[0] / 1050.0, 4),
            "x_max": round(raw_b[3] / 800.0, 4),
            "y_max": round(raw_b[2] / 1050.0, 4),
        }

        ev_id = f"ev-item-{caso['id']}"
        extracted_box_line = next(
            (l.replace("[BOX]", "").strip() for l in caso["lines"] if l.startswith("[BOX]")),
            "",
        )

        if caso["ambiguous"]:
            hypotheses = [
                {
                    "text": caso["expected_top1"],
                    "rank": 1,
                    "score": 0.65,
                    "score_kind": "HEURISTIC_MODEL",
                    "supporting_evidence_ids": [ev_id],
                },
                {
                    "text": caso["expected_top2"],
                    "rank": 2,
                    "score": 0.25,
                    "score_kind": "HEURISTIC_MODEL",
                    "supporting_evidence_ids": [ev_id],
                },
                {
                    "text": "Opção alternativa plausível",
                    "rank": 3,
                    "score": 0.10,
                    "score_kind": "HEURISTIC_MODEL",
                    "supporting_evidence_ids": [ev_id],
                },
            ]
            uncertainty = "AMBIGUOUS"
        else:
            hypotheses = [
                {
                    "text": extracted_box_line,
                    "rank": 1,
                    "score": 0.98,
                    "score_kind": "HEURISTIC_MODEL",
                    "supporting_evidence_ids": [ev_id],
                }
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
                    "excerpt": extracted_box_line,
                }
            ],
        }

        if caso["crm"]:
            ev_crm_id = f"ev-crm-{caso['id']}"
            fixture_data["fields"].append(
                {
                    "id": f"field-crm-{caso['id']}",
                    "run_id": f"run-{caso['id']}",
                    "field_type": "crm",
                    "raw_text": caso["crm"],
                    "normalized_value": caso["crm"],
                    "hypotheses": [
                        {
                            "text": caso["crm"],
                            "rank": 1,
                            "score": None,
                            "score_kind": "HEURISTIC_MODEL",
                            "supporting_evidence_ids": [ev_crm_id],
                        }
                    ],
                    "uncertainty_status": "CERTAIN",
                    "confidence_kind": "HEURISTIC_MODEL",
                    "score": None,
                    "evidence_ids": [ev_crm_id],
                    "requires_review": False,
                }
            )
            fixture_data["evidences"].append(
                {
                    "id": ev_crm_id,
                    "document_id": caso["id"],
                    "page": 1,
                    "bbox": {"x_min": 0.6125, "y_min": 0.7333, "x_max": 0.9125, "y_max": 0.8381},
                    "coordinate_system": "NORMALIZED_0_1",
                    "localization_status": "MANUAL_FIXTURE",
                    "source": "FIXTURE",
                    "excerpt": f"CRM {caso['crm']}",
                }
            )

        with open(img_path, "rb") as f_img:
            raw_bytes = f_img.read()
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()

        img_temp = Image.open(io.BytesIO(raw_bytes))
        out_buf = io.BytesIO()
        img_temp.save(out_buf, format="JPEG", quality=92, optimize=True)
        sanitized_hash = hashlib.sha256(out_buf.getvalue()).hexdigest()

        fixtures_dict[raw_hash] = fixture_data
        fixtures_dict[sanitized_hash] = fixture_data
        fixtures_dict[caso["id"]] = fixture_data

        with open(os.path.join(GROUND_TRUTH_DIR, f"{caso['id']}_gt.json"), "w", encoding="utf-8") as f:
            json.dump(caso, f, indent=2, ensure_ascii=False)

        cases_manifest.append(
            {
                "id": caso["id"],
                "filename": caso["filename"],
                "category": caso["category"],
                "ambiguous": caso["ambiguous"],
                "expected_findings": caso["expected_findings"],
            }
        )

    fixtures_file = os.path.join(BASE_DIR, "fixtures.json")
    with open(fixtures_file, "w", encoding="utf-8") as f:
        json.dump(fixtures_dict, f, indent=2, ensure_ascii=False)

    manifest_file = os.path.join(BASE_DIR, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seed": RANDOM_SEED,
                "total_document_cases": len(cases_manifest),
                "cases": cases_manifest,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    return cases_manifest


def build_synthetic_200_network_claims():
    """Gera o dataset de 200 guias médicas para teste de grafo do agente Investigador."""
    random.seed(RANDOM_SEED)
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
        "Ecocardiograma Transtorácico",
    ]

    claims = []
    data_esquema = "2026-10-14"
    for k in range(1, 4):
        claims.append(
            {
                "id": f"CLAIM-NET-{len(claims)+1:03d}",
                "crm_profissional": "PROF-DEMO-007",
                "paciente_id": f"PACIENTE-DEMO-{k:03d}",
                "clinica_id": "CLINICA-DEMO-001",
                "cidade": "Sorocaba",
                "data": data_esquema,
                "procedimentos": ["Consulta Médica em Atenção Primária", "Eletrocardiograma de Repouso"],
                "valor_centavos": 25000,
                "anomalia_injetada": "DISTANCIA_IMPOSSIVEL",
            }
        )
    for k in range(4, 7):
        claims.append(
            {
                "id": f"CLAIM-NET-{len(claims)+1:03d}",
                "crm_profissional": "PROF-DEMO-007",
                "paciente_id": f"PACIENTE-DEMO-{k:03d}",
                "clinica_id": "CLINICA-DEMO-005",
                "cidade": "Santos",
                "data": data_esquema,
                "procedimentos": ["Endoscopia Digestiva Alta"],
                "valor_centavos": 90000,
                "anomalia_injetada": "DISTANCIA_IMPOSSIVEL",
            }
        )

    datas = [f"2026-10-{d:02d}" for d in range(1, 15)]
    while len(claims) < 200:
        c_info = random.choice(clinicas)
        claims.append(
            {
                "id": f"CLAIM-NET-{len(claims)+1:03d}",
                "crm_profissional": random.choice(profissionais),
                "paciente_id": random.choice(pacientes),
                "clinica_id": c_info["id"],
                "cidade": c_info["cidade"],
                "data": random.choice(datas),
                "procedimentos": [random.choice(procedimentos_lista)],
                "valor_centavos": random.randint(15000, 120000),
                "anomalia_injetada": None,
            }
        )

    network_file = os.path.join(NETWORK_DIR, "claims_200.json")
    with open(network_file, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)

    return len(claims)


if __name__ == "__main__":
    manifest = build_synthetic_20_cases()
    net_count = build_synthetic_200_network_claims()

    manifest_file = os.path.join(BASE_DIR, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "seed": RANDOM_SEED,
                "total_document_cases": len(manifest),
                "total_network_claims": net_count,
                "cases": manifest,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Sucesso! Gerados {len(manifest)} casos documentais sintéticos e {net_count} registros de rede.")
