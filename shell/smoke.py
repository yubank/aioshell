"""
비대화형 스모크: LLM 로드 없이 ProcessorChain 전체 단계를 검증합니다.
실제 셸 명령은 실행하지 않습니다(OS·환경에 무관).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from .core.processors import (
    CommandExecutionProcessor,
    CommandIntent,
    ProcessResult,
    ProcessorChain,
)
from .utils.config import Config


DEFAULT_SMOKE_INPUT = "현재 폴더 파일 목록 보여줘"


async def run_smoke_pipeline(user_input: str | None = None) -> ProcessResult:
    """
    모킹된 AI + 실행 단계 패치로 파이프라인 끝까지 통과하는지 확인합니다.

    Args:
        user_input: 비어 있으면 DEFAULT_SMOKE_INPUT 사용
    """
    text = (user_input or DEFAULT_SMOKE_INPUT).strip()
    config = Config()

    mock_ai = AsyncMock()
    mock_ai.analyze_intent = AsyncMock(
        return_value=CommandIntent(
            intent_type="list_files",
            confidence=0.9,
            parameters={"path": ".", "detailed": False},
            raw_command=text,
            risk_level="safe",
        )
    )

    async def _fake_execute(self, command: str) -> ProcessResult:
        return ProcessResult(
            success=True,
            output="smoke_ok",
            executed_command=command,
        )

    with patch.object(CommandExecutionProcessor, "process", _fake_execute):
        chain = ProcessorChain(mock_ai, config)
        return await chain.process(text)
