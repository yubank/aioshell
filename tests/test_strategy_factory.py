"""ai.provider에 따른 전략 팩토리."""

from __future__ import annotations

import pytest

from shell.ai_integration.strategy_factory import create_ai_strategy
from shell.utils.config import Config


def test_factory_local_hf():
    c = Config()
    c.set("ai.provider", "local_hf")
    s = create_ai_strategy(c)
    assert s.__class__.__name__ == "CodeLlamaStrategy"


def test_factory_ollama():
    pytest.importorskip("httpx")
    c = Config()
    c.set("ai.provider", "ollama")
    s = create_ai_strategy(c)
    assert s.__class__.__name__ == "OllamaStrategy"
