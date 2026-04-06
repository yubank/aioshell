# 설치 가이드

AI Operating Shell(aioshell)을 로컬에 설치하는 절차입니다.

## 요구 사항

- Python 3.8 이상 (3.10+ 권장)
- Windows, Linux, macOS
- **로컬 CodeLlama(Hugging Face) 사용 시**: 충분한 디스크·RAM/GPU(모델 크기에 따름)
- **Ollama 사용 시**: [Ollama](https://ollama.com/) 설치 후 원하는 모델 `ollama pull` 로 받기

## 1. 저장소 받기

```bash
git clone https://github.com/yubank/aioshell.git
cd aioshell
```

## 2. 가상 환경(권장)

```bash
python -m venv .venv
```

**Windows**

```text
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

## 3. 의존성 설치

```bash
pip install -r requirements.txt
```

일부 기능(로컬 대형 모델)은 PyTorch·CUDA 환경에 따라 별도 설치가 필요할 수 있습니다.

## 4. 초기 설정

프로젝트 루트에 **`.config`** 또는 **`config.yaml`** 을 두어 AI 백엔드 등을 지정합니다. 자세한 항목은 [설정 방법](configuration.md)을 참고하세요.

Ollama만 쓸 경우 예시:

1. Ollama 실행 후 `ollama pull <모델명>` 으로 모델 준비
2. `.config` 에서 `ai.provider: ollama` 및 `ai.ollama.model` 을 위 모델명과 맞추기

로컬 Hugging Face(CodeLlama)를 쓸 경우 `python scripts/model_cli.py` 로 모델을 받을 수 있습니다. 요약은 [모델 관리](MODEL_MANAGEMENT.md)를 참고하세요.

> 참고: 저장소에 `scripts/setup.py` 가 없을 수 있습니다. 위 단계와 `pip`·설정 파일로 충분합니다.

## 5. 동작 확인

```bash
python scripts/start.py --smoke
```

성공 시 파이프라인 스모크만 수행하고 종료합니다(대형 모델 불필요).

```bash
pytest tests/
```

## 다음 단계

- [사용법](usage.md)
- [설정 방법](configuration.md)
