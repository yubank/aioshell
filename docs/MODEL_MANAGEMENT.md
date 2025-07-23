# CodeLlama 모델 관리 가이드

이 문서는 AI Operating Shell에서 CodeLlama 모델을 다운로드, 관리, 사용하는 방법을 설명합니다.

## 개요

AI Operating Shell은 CodeLlama 모델을 사용하여 자연어를 쉘 명령어로 변환합니다. 시스템은 다음과 같은 모델 관리 기능을 제공합니다:

- **자동 다운로드**: 첫 실행 시 자동으로 적절한 모델을 다운로드
- **캐시 관리**: 다운로드된 모델을 로컬에 저장하여 재사용
- **오프라인 지원**: 인터넷 연결 없이도 다운로드된 모델 사용 가능
- **시스템 최적화**: 하드웨어 사양에 따른 권장 모델 제시

## 지원하는 모델

| 모델 키 | 모델명 | 크기 | 메모리 요구사항 | 다운로드 크기 | 권장 사용처 |
|---------|--------|------|----------------|---------------|-------------|
| `codellama-7b` | CodeLlama-7b-Instruct-hf | 7B | 16GB | 13GB | 일반 사용자 (권장) |
| `codellama-13b` | CodeLlama-13b-Instruct-hf | 13B | 32GB | 25GB | 고성능 필요 시 |
| `codellama-34b` | CodeLlama-34b-Instruct-hf | 34B | 64GB | 65GB | 최고 성능 (서버용) |

## 모델 CLI 도구 사용법

### 기본 명령어

```bash
# 모델 CLI 도구 도움말
python scripts/model_cli.py --help

# 사용 가능한 모델 목록 보기
python scripts/model_cli.py list

# 시스템 정보 및 권장 모델 확인
python scripts/model_cli.py info
```

### 모델 다운로드

```bash
# 기본 모델 (codellama-7b) 다운로드
python scripts/model_cli.py download

# 특정 모델 다운로드
python scripts/model_cli.py download --model codellama-13b

# 강제 재다운로드
python scripts/model_cli.py download --model codellama-7b --force
```

### 모델 관리

```bash
# 다운로드된 모델 삭제
python scripts/model_cli.py delete codellama-13b

# 확인 없이 삭제
python scripts/model_cli.py delete codellama-13b --yes
```

## 자동 모델 설정

### 첫 실행 시

AI Shell을 처음 실행할 때 모델이 없으면 자동으로 다운로드됩니다:

```bash
python scripts/start.py
```

시스템이 자동으로:
1. 하드웨어 사양을 확인
2. 권장 모델을 선택
3. 모델을 다운로드
4. 초기화 후 실행

### 수동 모델 선택

설정 파일을 통해 특정 모델을 지정할 수 있습니다:

```yaml
# config.yaml
ai:
  model_key: "codellama-13b"  # 사용할 모델 지정
```

```bash
python scripts/start.py --config config.yaml
```

## 시스템 요구사항

### GPU 사용 시

| GPU 메모리 | 권장 모델 | 양자화 |
|------------|-----------|---------|
| 8GB 이하 | codellama-7b | 8-bit |
| 16GB | codellama-7b | 16-bit |
| 24GB | codellama-13b | 8-bit |
| 32GB 이상 | codellama-13b | 16-bit |
| 64GB 이상 | codellama-34b | 16-bit |

### CPU 사용 시

- **RAM**: 모델 크기의 2배 이상 권장
- **저장 공간**: 다운로드 크기의 1.2배 이상
- **처리 속도**: GPU 대비 10-50배 느림

## 고급 설정

### 모델 디렉토리 변경

```python
from shell.ai_integration import ModelManager

# 사용자 정의 모델 디렉토리
model_manager = ModelManager(models_dir="/custom/path/models")
```

### 캐시 관리

```bash
# 모델 캐시 위치
ls -la models/

# 메타데이터 확인
cat models/models_metadata.json

# 디스크 사용량 확인
du -sh models/*/
```

### 오프라인 사용

다운로드된 모델은 인터넷 연결 없이 사용 가능합니다:

```python
# 오프라인 모드에서 모델 로드
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    local_files_only=True  # 오프라인 사용
)
```

## 문제 해결

### 다운로드 실패

**증상**: 모델 다운로드가 중단되거나 실패

**해결책**:
```bash
# 1. 인터넷 연결 확인
curl -I https://huggingface.co

# 2. 디스크 공간 확인
df -h

# 3. 부분 다운로드 정리 후 재시도
python scripts/model_cli.py delete codellama-7b --yes
python scripts/model_cli.py download --model codellama-7b
```

### 메모리 부족

**증상**: "CUDA out of memory" 또는 시스템 응답 없음

**해결책**:
```bash
# 1. 더 작은 모델 사용
python scripts/model_cli.py download --model codellama-7b

# 2. CPU 모드로 전환 (설정 파일에서)
ai:
  device: "cpu"

# 3. 양자화 활성화
ai:
  quantization: true
```

### 모델 로딩 실패

**증상**: "Model files not found" 오류

**해결책**:
```bash
# 1. 모델 파일 무결성 확인
python scripts/model_cli.py list

# 2. 모델 재다운로드
python scripts/model_cli.py download --force

# 3. 권한 확인
chmod -R 755 models/
```

## 성능 최적화

### 로딩 시간 단축

1. **SSD 사용**: 모델을 SSD에 저장
2. **충분한 RAM**: 모델 크기의 2배 이상
3. **사전 로딩**: 자주 사용하는 모델 미리 준비

### 추론 속도 향상

1. **GPU 사용**: CUDA 가능한 GPU 활용
2. **양자화**: 8-bit 또는 4-bit 양자화 적용
3. **배치 처리**: 여러 요청을 한 번에 처리

## API 참조

### ModelManager 클래스

```python
from shell.ai_integration import ModelManager

# 인스턴스 생성
manager = ModelManager()

# 모델 다운로드
await manager.download_model("codellama-7b")

# 다운로드된 모델 목록
models = await manager.list_downloaded_models()

# 모델 삭제
await manager.delete_model("codellama-13b")

# 권장 모델 확인
recommended = manager.get_recommended_model()
```

### CodeLlamaStrategy 클래스

```python
from shell.ai_integration import CodeLlamaStrategy

# 전략 인스턴스 생성
config = {"model_key": "codellama-7b"}
strategy = CodeLlamaStrategy(config)

# 초기화 (모델 자동 다운로드)
await strategy.initialize()

# 자연어 분석
intent = await strategy.analyze_intent("파일 목록 보여줘")

# 리소스 정리
strategy.cleanup()
```

## 라이센스 및 사용 제한

- CodeLlama 모델은 Meta의 라이센스를 따릅니다
- 상업적 사용에 대한 제한이 있을 수 있습니다
- 자세한 내용은 [Hugging Face 모델 페이지](https://huggingface.co/codellama)를 참조하세요

## 추가 리소스

- [CodeLlama 공식 문서](https://ai.meta.com/research/publications/code-llama-open-foundation-models-for-code/)
- [Hugging Face Transformers 문서](https://huggingface.co/docs/transformers/)
- [AI Operating Shell 개발 가이드](../README.md) 