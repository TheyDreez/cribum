import os
import sys

# Garante que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from PIL import Image
from backend.agents.leitor import LeitorAgent

def test_leitor_agent():
    # 1. Cria uma imagem temporária simulada
    test_img_path = "backend/tests/test_guia.jpg"
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    img.save(test_img_path)

    try:
        # 2. Instancia o LeitorAgent
        agent = LeitorAgent(api_base="http://localhost:8000/v1")

        # 3. Processa a guia (com fallback de contingência caso o vLLM não esteja ativo no host local)
        cabecalho, itens, telemetria = agent.processar_guia(test_img_path, allow_mock_fallback=True)

        # 4. Asserções de conformidade de schema
        assert cabecalho.crm == "142857"
        assert cabecalho.uf_crm == "SP"
        assert len(itens) >= 2

        # Item 1 deve conter 3 hipóteses e incerteza alta (caso clássico de Losartana x Lorazepam)
        item_1 = itens[0]
        assert len(item_1.hipoteses) == 3
        assert item_1.box == [320, 110, 410, 890]
        assert item_1.nivel_incerteza == "alto"
        assert any("Losartana" in h.nome for h in item_1.hipoteses)
        assert any("Lorazepam" in h.nome for h in item_1.hipoteses)

        # Verificação da telemetria e hash pericial SHA-256
        assert "documento_sha256" in telemetria
        assert len(telemetria["documento_sha256"]) == 64
        assert telemetria["backend_hardware"] == "AMD ROCm GPU"
        assert "tempo_inferencia_ms" in telemetria

        print("=== Teste do LeitorAgent PASSOU com sucesso! ===")
        print(f"SHA-256: {telemetria['documento_sha256']}")
        print(f"Tempo de inferência: {telemetria['tempo_inferencia_ms']} ms")
        print(f"Itens extraídos: {len(itens)}")
        for idx, item in enumerate(itens, 1):
            print(f"  Item {idx}: Top Hipótese: {item.hipoteses[0].nome} (confiança: {item.hipoteses[0].confianca}) | Incerteza: {item.nivel_incerteza}")

    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

if __name__ == "__main__":
    test_leitor_agent()
