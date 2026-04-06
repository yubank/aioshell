# 활성 컨텍스트 - 현재 작업 상황

> 저장소 실제 상태 기준 (2026-04-06). `progress.md`와 동기화됨.

## 현재 프로젝트 상태

### 구현 완료 (코드 존재)
- `shell/core/shell_engine.py` — 메인 AI 쉘 엔진
- `shell/core/processors.py` — 명령 처리 파이프라인
- `shell/ai_integration/codellama_strategy.py` — CodeLlama 전략
- `shell/ai_integration/model_manager.py` — 모델 다운로드·캐시
- `shell/ai_integration/intent_parser.py` — 규칙 기반 의도 파싱
- `shell/utils/config.py`, `shell/utils/logging.py`
- `scripts/start.py`, `scripts/model_cli.py` 등

### 미구현 또는 부분만 존재
- `shell/commands/`, `shell/safety/`, `shell/learning/` — 디렉터리·모듈 없음 (문서상 설계만)
- `tests/` — `README.md`만 있고 `pytest`용 테스트 파일 없음
- 루트 `README`가 가리키는 일부 `docs/*.md`, `scripts/setup.py` — 저장소와 불일치할 수 있음 (문서 정리 과제)

### 작업 포커스 (최근)
- **모델 관리**: ModelManager, `model_cli.py`, 시작 스크립트 연동 — 코드상 반영됨
- **다음 권장 단계**: 전체 스모크 테스트 → `pytest` 최소 세트 → `commands/`·안전 검증 고도화

## 프로젝트 구조 (요약)

```
aioshell/
├── docs/           # 일부 문서만 존재 (MODEL_MANAGEMENT 등)
├── examples/
├── models/
├── scripts/        # start.py, model_cli.py 등
├── shell/          # core, ai_integration, utils
├── tests/          # README만 — 테스트 모듈 추가 예정
├── memory-bank/
├── README.md
└── requirements.txt
```

## 다음 단계 우선순위

### 즉시
1. 로컬 스모크: 의존성 설치 후 `scripts/start.py` 동작 확인
2. `pytest`용 `tests/test_*.py` 추가 (코어·설정·파서 등)

### 단기
1. `shell/commands/` 도입 및 의도→명령 매핑 정리
2. 실행 직전 안전 검증 (`shell/safety/` 또는 processors 개선)
3. 루트 README / `docs` 링크·설치 절차 정합성

### 중기
- 자연어·매핑 정확도 개선, 학습·플러그인은 로드맵

## 결정 사항 (유지)
- 모듈식 설계, 전략 패턴으로 AI 교체 가능성
- 안전성 우선 — 다만 현재는 입력 단계 검사 위주이며, 전용 안전 모듈은 향후 과제

## 다음 작업자 노트
1. **`shell/core`부터 새로 짜는 단계는 아님** — 이미 구현되어 있음.
2. **`requirements.txt`로 환경 맞춘 뒤** 통합 테스트를 권장.
3. 위험한 작업은 **실행 전 확인** 흐름을 강화하는 방향이 설계와 일치함.
