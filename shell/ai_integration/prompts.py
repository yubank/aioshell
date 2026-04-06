"""LLM용 쉘 의도 분석 프롬프트 (로컬 HF / Ollama 공통)."""


def build_shell_intent_prompt(user_input: str) -> str:
    """Linux/bash 의도 분석용 사용자 프롬프트."""
    return f"""<s>[INST] 다음 한국어 자연어 입력을 Linux/bash 명령어 의도로 분석해주세요.

사용자 입력: "{user_input}"

다음 형식으로 응답해주세요:
INTENT: [의도 유형]
CONFIDENCE: [0.0-1.0 신뢰도]
PARAMETERS: [매개변수들]
COMMAND: [추천 명령어]

지원하는 의도 유형:
- list_files: 파일 목록 보기
- find_files: 파일 찾기
- show_disk_usage: 디스크 사용량
- show_processes: 프로세스 목록
- create_directory: 디렉토리 생성
- delete_file: 파일 삭제
- copy_file: 파일 복사
- move_file: 파일 이동
- show_system_info: 시스템 정보

예시:
사용자: "현재 폴더 파일들 보여줘"
INTENT: list_files
CONFIDENCE: 0.95
PARAMETERS: path=., detailed=true
COMMAND: ls -la

[/INST]"""
