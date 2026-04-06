"""CodeLlama/Ollama 공통 의도 패턴 (빠른 규칙 매칭용)."""

from __future__ import annotations

from typing import Any, Dict, List


def default_intent_patterns() -> Dict[str, List[Dict[str, Any]]]:
    """의도 분류를 위한 패턴 매핑."""
    return {
        "list_files": [
            {
                "pattern": r"(파일|목록|리스트|보여|표시|ls).*(폴더|디렉터리|현재)",
                "param_extractors": {
                    "detailed": r"(자세히|세부|상세)",
                    "path": r"([/\w.-]+)\s*폴더",
                },
            },
            {
                "pattern": r"(현재|이곳|여기).*(파일|목록|뭐)",
                "param_extractors": {},
            },
        ],
        "find_files": [
            {
                "pattern": r"(찾아|검색|find).*(파일|확장자)",
                "param_extractors": {
                    "name": r"['\"]([^'\"]+)['\"]",
                    "path": r"([/\w.-]+)\s*에서",
                },
            },
            {
                "pattern": r"(큰|대용량|사이즈).*(파일)",
                "param_extractors": {},
            },
        ],
        "show_disk_usage": [
            {
                "pattern": r"(디스크|용량|공간|저장).*(사용|남은|확인)",
                "param_extractors": {},
            },
            {
                "pattern": r"(du|df|용량).*(체크|확인)",
                "param_extractors": {},
            },
        ],
        "show_processes": [
            {
                "pattern": r"(프로세스|실행중|ps).*(목록|보기|확인)",
                "param_extractors": {},
            },
            {
                "pattern": r"(실행|돌아가는).*(프로그램|작업)",
                "param_extractors": {},
            },
        ],
        "create_directory": [
            {
                "pattern": r"(만들어|생성|mkdir).*(폴더|디렉터리)",
                "param_extractors": {
                    "path": r"['\"]([^'\"]+)['\"]|(\w+)\s*폴더",
                },
            }
        ],
        "delete_file": [
            {
                "pattern": r"(삭제|지워|제거|rm).*(파일|폴더)",
                "param_extractors": {
                    "path": r"['\"]([^'\"]+)['\"]",
                },
            }
        ],
        "copy_file": [
            {
                "pattern": r"(복사|copy|cp).*(파일|폴더)",
                "param_extractors": {
                    "source": r"['\"]([^'\"]+)['\"]",
                    "destination": r"에서\s+['\"]([^'\"]+)['\"]",
                },
            }
        ],
        "move_file": [
            {
                "pattern": r"(이동|move|mv).*(파일|폴더)",
                "param_extractors": {
                    "source": r"['\"]([^'\"]+)['\"]",
                    "destination": r"에서\s+['\"]([^'\"]+)['\"]",
                },
            }
        ],
        "show_system_info": [
            {
                "pattern": r"(시스템|정보|환경|스펙).*(확인|보기|정보)",
                "param_extractors": {
                    "type": r"(메모리|CPU|디스크|일반)",
                },
            }
        ],
    }
