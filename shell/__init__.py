"""
AI Operating Shell

CodeLlama 기반 자연어 쉘 프로그램

주요 구성요소:
- core: 핵심 쉘 엔진과 처리 파이프라인
- ai_integration: CodeLlama 모델 통합
- utils: 설정 및 로깅 유틸리티
"""

from .core.shell_engine import AIShellEngine, create_shell
from .utils.config import Config
from .utils.logging import setup_logging, get_logger

__version__ = "0.1.0"
__author__ = "AI Shell Team"
__description__ = "CodeLlama 기반 자연어 운영체제 쉘"

__all__ = [
    'AIShellEngine',
    'create_shell',
    'Config',
    'setup_logging',
    'get_logger'
] 