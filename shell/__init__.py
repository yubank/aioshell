"""
AI Operating Shell

CodeLlama 기반 자연어 쉘 프로그램

주요 구성요소:
- core: 핵심 쉘 엔진과 처리 파이프라인
- ai_integration: CodeLlama 모델 통합
- utils: 설정 및 로깅 유틸리티

무거운 하위 모듈(AIShellEngine 등)은 import 시점이 아니라
속성 접근 시 로드합니다(torch 미설치 환경의 스모크·테스트용).
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

__version__ = "0.1.0"
__author__ = "AI Shell Team"
__description__ = "CodeLlama 기반 자연어 운영체제 쉘"

__all__ = [
    "AIShellEngine",
    "create_shell",
    "Config",
    "setup_logging",
    "get_logger",
]

_LAZY = {
    "AIShellEngine": (".core.shell_engine", "AIShellEngine"),
    "create_shell": (".core.shell_engine", "create_shell"),
    "Config": (".utils.config", "Config"),
    "setup_logging": (".utils.logging", "setup_logging"),
    "get_logger": (".utils.logging", "get_logger"),
}

if TYPE_CHECKING:
    from .core.shell_engine import AIShellEngine, create_shell
    from .utils.config import Config
    from .utils.logging import get_logger, setup_logging


def __getattr__(name: str) -> Any:
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        mod = importlib.import_module(module_name, __name__)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(list(globals()) + __all__))
