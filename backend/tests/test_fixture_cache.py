from unittest.mock import mock_open, patch

from backend.services.provider import DemoFixtureProvider, _load_fixtures_from_disk


def test_fixture_lru_cache_hits():
    # Limpa cache antes do teste
    _load_fixtures_from_disk.cache_clear()

    provider1 = DemoFixtureProvider()
    cache_info_before = _load_fixtures_from_disk.cache_info()

    # Instancia segundo provider com mesmo caminho de fixtures
    provider2 = DemoFixtureProvider()
    cache_info_after = _load_fixtures_from_disk.cache_info()

    # Verifica se o cache registrou um hit
    assert cache_info_after.hits > cache_info_before.hits
    assert provider1._fixtures == provider2._fixtures


def test_fixture_lru_cache_prevents_repeated_disk_reads():
    _load_fixtures_from_disk.cache_clear()

    sample_json = '{"test_hash": {"fields": [], "evidences": []}}'

    with (
        patch("builtins.open", mock_open(read_data=sample_json)) as mock_file,
        patch("os.path.exists", return_value=True),
    ):
        p1 = DemoFixtureProvider("dummy_path.json")
        p2 = DemoFixtureProvider("dummy_path.json")
        p3 = DemoFixtureProvider("dummy_path.json")

        # Apenas 1 abertura de arquivo no disco
        assert mock_file.call_count == 1
        assert "test_hash" in p1._fixtures
        assert "test_hash" in p2._fixtures
        assert "test_hash" in p3._fixtures


def test_fixture_cache_reload():
    _load_fixtures_from_disk.cache_clear()

    json_v1 = '{"v1": true}'
    json_v2 = '{"v2": true}'

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json_v1)) as m_open:
            p = DemoFixtureProvider("dummy_reload.json")
            assert "v1" in p._fixtures
            assert m_open.call_count == 1

        # Com reload=True
        with patch("builtins.open", mock_open(read_data=json_v2)) as m_open2:
            reloaded = p._load_fixtures(reload=True)
            assert "v2" in reloaded
            assert m_open2.call_count == 1


def test_register_fixture_does_not_corrupt_cache():
    _load_fixtures_from_disk.cache_clear()

    provider = DemoFixtureProvider()
    original_len = len(provider._fixtures)

    provider.register_fixture("custom_hash", {"fields": [], "evidences": []})
    assert len(provider._fixtures) == original_len + 1
    assert "custom_hash" in provider._fixtures

    # Novo provider recarregado da cache não deve ter a fixture customizada
    new_provider = DemoFixtureProvider()
    assert "custom_hash" not in new_provider._fixtures
    assert len(new_provider._fixtures) == original_len
