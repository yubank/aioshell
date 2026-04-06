"""
AI Shell Core Module

핵심 쉘 엔진과 처리 파이프라인을 포함합니다.
AIShellEngine은 속성 접근 시 로드합니다(무거운 UI 의존성 분리).
"""

from __future__ import annotations

import importlib
from typing import Any

from .processors import CommandExecutionProcessor, InputProcessor, ProcessorChain

__all__ = [
    "AIShellEngine",
    "ProcessorChain",
    "InputProcessor",
    "CommandExecutionProcessor",
]

_LAZY = {
    "AIShellEngine": (".shell_engine", "AIShellEngine"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        mod = importlib.import_module(module_name, __name__)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(list(globals()) + __all__))
