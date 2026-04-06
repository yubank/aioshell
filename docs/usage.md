# 사용법

## AI 쉘 엔진 (`scripts/start.py`)

프로젝트 루트에서:

```bash
python scripts/start.py
```

### 자주 쓰는 옵션

| 옵션 | 설명 |
|------|------|
| `-c`, `--config` | 설정 파일 경로(YAML/JSON) |
| `--debug` | 디버그 로그 |
| `--model-name` | Hugging Face 쪽 모델 이름(로컬 HF 사용 시) |
| `--smoke` | 모델 없이 처리 파이프라인만 검증 후 종료 |
| `--ai-provider` | `local_hf` 또는 `ollama` (설정 파일보다 우선) |
| `--rl-train` | 강화학습용 궤적 수집 등 학습 모드(자세한 설정은 `training` 항목) |

설정은 [configuration.md](configuration.md)를 참고하세요.

## 경량 쉘 (`scripts/aosh.py`)

규칙 기반으로 자연어를 쉘 명령으로 바꾸는 **별도** 데모 쉘입니다(CodeLlama 엔진과 무관).

```bash
python scripts/aosh.py
```

의존성: `prompt-toolkit`, `rich` 등(`requirements.txt` 참고).

## 모델 CLI

```bash
python scripts/model_cli.py --help
```

다운로드·목록·시스템 정보 등은 [MODEL_MANAGEMENT.md](MODEL_MANAGEMENT.md) 참고.

## LLM 학습 진입점

```bash
python scripts/train_llm.py --mode reinforcement --epochs 3
```

강화학습 모드는 궤적 JSONL 수집 등 **확장용 스텁**입니다. 실제 가중치 학습은 TRL·별도 파이프라인과 연동하는 것을 전제로 합니다.

## 테스트

```bash
pytest tests/
```

## 사용 시 유의사항

- 자연어에서 생성된 명령은 **실제로 시스템에서 실행**될 수 있습니다. `shell.safe_mode`, `safety` 설정을 확인하세요.
- Windows와 Linux는 명령어 의미가 다를 수 있습니다. 생성된 명령을 실행 전에 검토하는 것이 좋습니다.
