"""shell.smoke 스모크 헬퍼."""

from __future__ import annotations

import pytest

from shell.smoke import run_smoke_pipeline


@pytest.mark.asyncio
async def test_run_smoke_pipeline_succeeds():
    result = await run_smoke_pipeline()
    assert result.success is True
    assert result.output == "smoke_ok"
    assert result.executed_command
