"""Config 기본값 및 dot notation."""

from __future__ import annotations

import json
from pathlib import Path

from shell.utils.config import Config


def test_config_defaults():
    c = Config()
    assert c.get("app.name") == "AI Operating Shell"
    assert c.get("ai.model_name")
    assert c.get("safety.enabled") is True


def test_config_set_and_get_nested():
    c = Config()
    c.set("ai.temperature", 0.42)
    assert c.get("ai.temperature") == 0.42


def test_config_load_json_file(tmp_path: Path):
    path = tmp_path / "t.json"
    path.write_text(
        json.dumps({"ai": {"temperature": 0.99}, "shell": {"safe_mode": False}}),
        encoding="utf-8",
    )
    c = Config(str(path))
    assert c.get("ai.temperature") == 0.99
    assert c.get("shell.safe_mode") is False
