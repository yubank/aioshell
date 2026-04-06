"""설정의 ai.provider에 따라 전략 인스턴스 생성."""

from __future__ import annotations

from typing import Any

from ..utils.config import Config


def create_ai_strategy(config: Config) -> Any:
    """
    ai.provider:
      - local_hf (기본): 로컬 Hugging Face / ModelManager
      - ollama: Ollama HTTP API
    """
    ai = config.get("ai") or {}
    provider = (ai.get("provider") or "local_hf").strip().lower()

    if provider in ("ollama", "ollama_http"):
        from .ollama_strategy import OllamaStrategy

        return OllamaStrategy(config)
    from .codellama_strategy import CodeLlamaStrategy

    return CodeLlamaStrategy(config)
