"""MONGO_SERVER_SELECTION_TIMEOUT_MS (see config/mongo.py)."""

import pytest

from config.mongo import (
    DEFAULT_SERVER_SELECTION_TIMEOUT_MS,
    server_selection_timeout_ms,
)


def test_default_is_much_shorter_than_pymongos_30_seconds():
    assert DEFAULT_SERVER_SELECTION_TIMEOUT_MS == 3000
    assert server_selection_timeout_ms({}) == 3000


def test_the_environment_can_override_it():
    assert (
        server_selection_timeout_ms({"MONGO_SERVER_SELECTION_TIMEOUT_MS": "8000"})
        == 8000
    )


@pytest.mark.parametrize("value", ["", "abc", "0", "-5", "1.5"])
def test_invalid_values_fall_back_to_the_default(value):
    environ = {"MONGO_SERVER_SELECTION_TIMEOUT_MS": value}

    assert server_selection_timeout_ms(environ) == DEFAULT_SERVER_SELECTION_TIMEOUT_MS


def test_reads_the_process_environment_by_default(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "1234")

    assert server_selection_timeout_ms() == 1234
