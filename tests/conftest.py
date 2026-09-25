import pytest


@pytest.fixture(autouse=True)
def _no_live_local_model(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("tests must not call a live Ollama model; inject a stub transport")

    monkeypatch.setattr("personal_wealth_tracker.local_llm.urlopen", refuse)
