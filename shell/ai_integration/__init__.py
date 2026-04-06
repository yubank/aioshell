"""
AI Integration Module

CodeLlama 등 무거운 통합은 속성 접근 시 로드합니다.
IntentParser 등 가벼운 모듈은 즉시 import 합니다.
"""

from __future__ import annotations

import importlib
from typing import Any

from .intent_parser import IntentParser

__all__ = [
    "CodeLlamaStrategy",
    "IntentParser",
    "ModelManager",
]

_LAZY = {
    "CodeLlamaStrategy": (".codellama_strategy", "CodeLlamaStrategy"),
    "ModelManager": (".model_manager", "ModelManager"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        mod = importlib.import_module(module_name, __name__)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(list(globals()) + __all__))
