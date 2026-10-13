import os
import sys
import pytest
from PIL import Image

# Garante que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.leitor import LeitorAgent


def test_leitor_agent_mock_explicit():
    # 1. Cria uma imagem temporária simulada
    test_img_path = "backend/tests/test_guia.jpg"
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    img.save(test_img_path)

    try:
        agent = LeitorAgent(api_base="http://localhost:8000/v1")

        # Modo de contingência com mock opt-in explícito
        cabecalho, itens, telemetria = agent.processar_guia(test_img_path, allow_mock_fallback=True)

        assert cabecalho.crm == "142857"
        assert cabecalho.uf_crm == "SP"
        assert len(itens) >= 2

        item_1 = itens[0]
        assert len(item_1.hipoteses) == 3
        assert item_1.box == [320, 110, 410, 890]
        assert item_1.nivel_incerteza == "alto"
        assert any("Losartana" in h.nome for h in item_1.hipoteses)
        assert any("Lorazepam" in h.nome for h in item_1.hipoteses)

        assert "documento_sha256" in telemetria
        assert len(telemetria["documento_sha256"]) == 64
        assert "tempo_inferencia_ms" in telemetria
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)


def test_leitor_agent_fails_without_fallback_when_offline():
    test_img_path = "backend/tests/test_guia_offline.jpg"
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    img.save(test_img_path)

    try:
        # Aponta para porta inexistente sem mock fallback
        agent = LeitorAgent(api_base="http://127.0.0.1:59999/v1", timeout=1)

        # allow_mock_fallback=False por padrão deve lançar RuntimeError sem mascarar erro
        with pytest.raises(RuntimeError) as exc_info:
            agent.processar_guia(test_img_path, allow_mock_fallback=False)

        assert "Falha na inferência VLM" in str(exc_info.value)
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)
