"""Startup preload of the search models (see application/preload.py)."""

from unittest.mock import patch

import pytest

from apps.search_engine.application import preload

SERVICE = "apps.search_engine.application.services.llm_search_service.LLMSearchService"


@pytest.mark.parametrize("value", ["0", "false", "False", "no"])
def test_disabled_by_environment(monkeypatch, value):
    monkeypatch.setenv("SEARCH_PRELOAD_MODELS", value)

    with patch(SERVICE) as service:
        assert preload.preload_models() is False

    service.assert_not_called()


@pytest.mark.parametrize("value", [None, "True", "1", "yes"])
def test_enabled_by_default_and_by_truthy_values(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("SEARCH_PRELOAD_MODELS", raising=False)
    else:
        monkeypatch.setenv("SEARCH_PRELOAD_MODELS", value)

    with patch(SERVICE) as service:
        assert preload.preload_models() is True

    service.assert_called_once_with()


def test_failure_is_logged_and_does_not_raise(monkeypatch, caplog):
    monkeypatch.delenv("SEARCH_PRELOAD_MODELS", raising=False)

    with patch(SERVICE, side_effect=RuntimeError("Path resources/models not found")):
        with caplog.at_level("ERROR"):
            assert preload.preload_models() is False

    assert "No se pudieron precargar los modelos" in caplog.text


def test_background_preload_runs_in_a_daemon_thread(monkeypatch):
    monkeypatch.delenv("SEARCH_PRELOAD_MODELS", raising=False)

    with patch(SERVICE) as service:
        thread = preload.preload_models_in_background()
        thread.join(timeout=5)

    assert thread.daemon is True
    assert thread.name == "model-preload"
    service.assert_called_once_with()


def test_background_preload_is_skipped_when_disabled(monkeypatch):
    monkeypatch.setenv("SEARCH_PRELOAD_MODELS", "false")

    with patch(SERVICE) as service:
        assert preload.preload_models_in_background() is None

    service.assert_not_called()


def test_gunicorn_post_fork_starts_the_background_preload():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "config" / "gunicorn.conf.py"
    spec = importlib.util.spec_from_file_location("gunicorn_conf", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with patch.object(preload, "preload_models_in_background") as start:
        module.post_fork(server=None, worker=None)

    start.assert_called_once_with()


def test_concurrent_first_use_loads_the_models_once():
    import threading
    import time

    from apps.search_engine.application.services.llm_search_service import (
        LLMSearchService,
    )

    calls = []

    def slow_initialize(self):
        calls.append(1)
        time.sleep(0.2)

    LLMSearchService._instance = None
    LLMSearchService._initialized = False
    try:
        with patch.object(LLMSearchService, "initialize_components", slow_initialize):
            start = threading.Barrier(4)

            def use():
                start.wait()
                LLMSearchService()

            threads = [threading.Thread(target=use) for _ in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
    finally:
        LLMSearchService._instance = None
        LLMSearchService._initialized = False

    assert len(calls) == 1


def test_import_heavy_modules_imports_the_urlconf_and_spacy():
    with patch.object(preload.importlib, "import_module") as import_module:
        preload.import_heavy_modules()

    imported = [call.args[0] for call in import_module.call_args_list]
    assert imported[0] == "config.urls"
    assert "spacy" in imported


def test_import_heavy_modules_failure_is_logged_and_does_not_raise(caplog):
    with patch.object(preload.importlib, "import_module", side_effect=ImportError("x")):
        with caplog.at_level("ERROR"):
            preload.import_heavy_modules()

    assert "No se pudieron importar los módulos pesados" in caplog.text
