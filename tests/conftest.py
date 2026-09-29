import shutil
from pathlib import Path

import pytest

PROJECT_CONFIG_DIR = Path(__file__).parents[1] / "config"
EXAMPLE_CONFIG_NAMES = ("settings", "categories", "rules")


@pytest.fixture
def example_config_dir(tmp_path):
    """The committed public sample config, copied under its loadable names."""
    config_dir = tmp_path / "example-config"
    config_dir.mkdir()
    for name in EXAMPLE_CONFIG_NAMES:
        shutil.copy(PROJECT_CONFIG_DIR / f"{name}.example.yaml", config_dir / f"{name}.yaml")
    return config_dir


@pytest.fixture(autouse=True)
def _no_live_local_model(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("tests must not call a live Ollama model; inject a stub transport")

    monkeypatch.setattr("personal_wealth_tracker.local_llm.urlopen", refuse)


@pytest.fixture(autouse=True)
def _project_config_untouched():
    """Tests register leaves in tmp copies; the operator's real config/ must never change."""
    before = _snapshot(PROJECT_CONFIG_DIR)
    yield
    assert _snapshot(PROJECT_CONFIG_DIR) == before, "test wrote to the project config/ directory"


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }
