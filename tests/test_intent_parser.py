"""IntentParser 규칙 매칭."""

from __future__ import annotations

import pytest

from shell.ai_integration.intent_parser import CommandType, IntentParser


@pytest.fixture
def parser() -> IntentParser:
    return IntentParser()


def test_parse_disk_usage_korean(parser: IntentParser):
    r = parser.parse("디스크 용량 알려줘")
    assert r.command_type == CommandType.SYSTEM_INFO
    assert r.action == "disk_usage"
    assert r.confidence > 0


def test_parse_list_files(parser: IntentParser):
    # 패턴 (목록|list|ls).*?(파일|file) — 영어로 안정적으로 매칭
    r = parser.parse("list files in current folder")
    assert r.command_type == CommandType.FILE_OPERATION
    assert r.action == "list_files"


def test_parse_unknown(parser: IntentParser):
    r = parser.parse("asdf qwer zxcv")
    assert r.command_type == CommandType.UNKNOWN
    assert r.confidence == 0.0
