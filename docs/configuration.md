# 설정 방법

설정은 **계층적으로** 병합됩니다: 기본값 → 기본 설정 파일들 → 명시한 `-c` 파일 → 환경 변수.

## 설정 파일 위치(자동 로드)

`Config` 가 다음 순서로 **존재하는 첫 파일만** 읽습니다(이후 파일은 같은 이름에서 건너뜀).

1. `.config` (프로젝트 루트)
2. `.config.yaml`, `.config.yml`
3. `config.yaml`, `config.yml`, `config.json`
4. 사용자 홈: `~/.ai-shell/config.yaml` 등

### `.config` 형식

- 내용이 `{` 로 시작하면 **JSON**으로 파싱합니다.
- 그 외에는 **YAML**로 파싱합니다.

## 주요 항목

### `ai` — AI 백엔드

| 키 | 설명 | 예시 |
|----|------|------|
| `provider` | `local_hf`(기본) 또는 `ollama` | `ollama` |
| `model_key` | 로컬 HF 모델 키 또는 `ollama` 등 식별자 | `codellama-7b` |
| `model_name` | Hugging Face 모델 ID | `codellama/CodeLlama-7b-Instruct-hf` |
| `max_length` | 생성 최대 길이 | `512` |
| `temperature` | 샘플링 온도 | `0.1` |

`provider: ollama` 일 때:

```yaml
ai:
  provider: ollama
  model_key: ollama
  ollama:
    base_url: http://127.0.0.1:11434
    model: llama3.2
    timeout: 180
```

Ollama 서버가 떠 있고, `ollama pull` 로 `model` 과 같은 이름의 모델이 있어야 합니다.

### `shell`

| 키 | 설명 |
|----|------|
| `safe_mode` | 안전 관련 동작(기본 `true`) |
| `command_timeout` | 명령 실행 타임아웃(초) |
| `history_size` | 히스토리 크기 |

### `safety`

| 키 | 설명 |
|----|------|
| `enabled` | 안전 검사 사용 여부 |
| `require_confirmation` | 위험 동작 시 확인(정책에 따라) |

### `logging`

| 키 | 설명 |
|----|------|
| `level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `file` | 로그 파일 경로 |

### `training` (선택)

강화학습 스텁 등: `training.mode`, `training.rl.epochs`, `training.rl.trajectory_dir` 등. 자세한 키는 `shell/utils/config.py` 의 기본값을 참고하세요.

## 환경 변수(일부)

| 환경 변수 | 설정 키 |
|-----------|---------|
| `AI_PROVIDER` | `ai.provider` |
| `AI_MODEL_NAME` | `ai.model_name` |
| `TRAINING_MODE` | `training.mode` |
| `RL_EPOCHS` | `training.rl.epochs` |
| `LOG_LEVEL` | `logging.level` |
| `DEBUG` | `app.debug` |

`.env` 또는 `~/.ai-shell/.env`도 로드됩니다.

## 예시: 프로젝트 루트 `.config`

```yaml
ai:
  provider: ollama
  ollama:
    base_url: http://127.0.0.1:11434
    model: llama3.2
    timeout: 180

shell:
  safe_mode: true

safety:
  enabled: true

logging:
  level: INFO
```

## 관련 문서

- [설치 가이드](installation.md)
- [모델 관리 (CodeLlama)](MODEL_MANAGEMENT.md)
