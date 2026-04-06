# API 개요

이 문서는 **라이브러리 형태로 사용할 때** 주요 진입점과 모듈을 요약합니다. 세부 시그니처는 각 소스 파일의 독스트링을 참고하세요.

## 설정

### `shell.utils.config.Config`

- YAML/JSON 파일, 환경 변수, 기본값을 병합합니다.
- `get("dot.notation.key")`, `set("key", value)`, `get_training_config()` 등을 제공합니다.

```python
from shell.utils.config import Config

cfg = Config("config.yaml")  # 또는 None (기본 파일 검색)
provider = cfg.get("ai.provider", "local_hf")
```

## AI 전략

### `shell.ai_integration.strategy_factory.create_ai_strategy`

`ai.provider`에 따라 로컬 Hugging Face(`CodeLlamaStrategy`) 또는 `OllamaStrategy` 인스턴스를 만듭니다.

```python
from shell.utils.config import Config
from shell.ai_integration.strategy_factory import create_ai_strategy

cfg = Config()
strategy = create_ai_strategy(cfg)
await strategy.initialize()
intent = await strategy.analyze_intent("현재 폴더 파일 목록")
```

### `shell.core.processors.ProcessorChain`

입력 검증 → 자연어 분석 → 명령 매핑 → 안전 검사 → 실행 순으로 처리합니다.

```python
from shell.core.processors import ProcessorChain
from shell.utils.config import Config

cfg = Config()
chain = ProcessorChain(strategy, cfg)
result = await chain.process("사용자 입력")
```

## 쉘 엔진

### `shell.core.shell_engine.AIShellEngine`

`Config`와 위 전략·체인을 묶어 대화형 프롬프트를 실행합니다.

```python
from shell.core.shell_engine import AIShellEngine
from shell.utils.config import Config

engine = AIShellEngine(Config())
await engine.start()
```

편의 함수: `create_shell(config_path=None)`.

## 스모크

### `shell.smoke.run_smoke_pipeline`

모델 없이 체인만 검증할 때 사용합니다.

```python
await run_smoke_pipeline()
```

## 학습(스텁)

### `shell.learning.rl_trainer.run_training_from_config`

`training.mode`에 따라 강화학습 궤적 수집 등을 수행합니다.

```python
from shell.learning.rl_trainer import run_training_from_config
from shell.utils.config import Config

cfg = Config()
cfg.set("training.mode", "reinforcement")
run_training_from_config(cfg)
```

## CLI 스크립트

| 스크립트 | 역할 |
|----------|------|
| `scripts/start.py` | 메인 AI 쉘 |
| `scripts/model_cli.py` | CodeLlama 모델 다운로드·목록 |
| `scripts/train_llm.py` | 학습 모드 진입 |
| `scripts/aosh.py` | 규칙 기반 경량 쉘 |

## 관련 문서

- [설정 방법](configuration.md)
- [사용법](usage.md)
