"""ProcessorChain: 모킹된 AI + 실행 단계 패치."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from shell.core.processors import (
    CommandExecutionProcessor,
    CommandIntent,
    ProcessResult,
    ProcessorChain,
)
from shell.utils.config import Config


@pytest.mark.asyncio
async def test_processor_chain_full_path_with_mocked_ai_and_execution():
    mock_ai = AsyncMock()
    mock_ai.analyze_intent = AsyncMock(
        return_value=CommandIntent(
            intent_type="list_files",
            confidence=0.9,
            parameters={"path": ".", "detailed": False},
            raw_command="test",
            risk_level="safe",
        )
    )

    async def fake_execute(self, command: str) -> ProcessResult:
        return ProcessResult(
            success=True,
            output="mocked_out",
            executed_command=command,
        )

    config = Config()
    with patch.object(CommandExecutionProcessor, "process", fake_execute):
        chain = ProcessorChain(mock_ai, config)
        result = await chain.process("현재 폴더 파일 목록 보여줘")

    assert result.success is True
    assert result.output == "mocked_out"
    assert result.executed_command
    mock_ai.analyze_intent.assert_awaited_once()


@pytest.mark.asyncio
async def test_processor_chain_low_confidence_stops():
    mock_ai = AsyncMock()
    mock_ai.analyze_intent = AsyncMock(
        return_value=CommandIntent(
            intent_type="list_files",
            confidence=0.1,
            parameters={},
            risk_level="safe",
        )
    )
    config = Config()
    chain = ProcessorChain(mock_ai, config)
    result = await chain.process("무슨 말인지 모르겠어")

    assert result.success is False
    assert "이해" in (result.error_message or "")
