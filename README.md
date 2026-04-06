# AI Operating Shell

AI 기반 운영 체제 쉘 - 자연어로 시스템을 제어하고 자동화하는 지능형 쉘

## 🚀 프로젝트 개요

AI Operating Shell은 자연어 처리와 머신러닝을 활용하여 사용자가 일반적인 명령어 대신 자연어로 시스템과 상호작용할 수 있게 해주는 혁신적인 쉘입니다.

## ✨ 주요 기능

- 🤖 **자연어 명령 처리**: "내 파일들을 날짜별로 정리해줘"와 같은 자연어 명령 지원
- 🧠 **AI 기반 작업 자동화**: 복잡한 시스템 작업을 AI가 자동으로 처리
- 📚 **학습 기능**: 사용자의 패턴을 학습하여 맞춤형 제안 제공
- 🔧 **확장 가능한 플러그인 시스템**: 다양한 AI 모델 및 도구 통합
- 🛡️ **안전한 실행**: 위험한 명령어 실행 전 확인 및 검증

## 📁 프로젝트 구조

```
ai-operating-shell/
├── docs/                    # 문서 및 사용법
├── examples/                # 사용 예시
├── models/                  # 로컬 AI 모델 저장 또는 설정
├── scripts/                 # 실행 스크립트
├── shell/                   # AI 쉘 코어 코드
├── tests/                   # 테스트 코드
├── .gitignore
├── LICENSE                  # MIT 라이센스
├── README.md                # 프로젝트 소개
└── requirements.txt         # Python 라이브러리 의존성
```

## 🛠️ 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/yubank/aioshell.git
cd aioshell
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 초기 설정

프로젝트 루트에 `.config` 또는 `config.yaml`을 두고 AI 백엔드(Ollama 등)를 지정합니다. 자세한 내용은 [설정 방법](docs/configuration.md)과 [설치 가이드](docs/installation.md)를 참고하세요.

## 🚀 사용법

### 기본 실행
```bash
python scripts/start.py
```

### 예시 명령어들
```bash
AI Shell> 오늘 수정된 파일들을 보여줘
AI Shell> Python 파일들을 백업해줘
AI Shell> 디스크 용량을 확인하고 큰 파일들을 찾아줘
AI Shell> 로그 파일들을 압축해서 정리해줘
```

## 📖 문서

자세한 사용법과 설정 방법은 `docs/` 디렉토리의 문서를 참조하세요:

- [설치 가이드](docs/installation.md)
- [사용법](docs/usage.md)
- [API 문서](docs/api.md)
- [설정 방법](docs/configuration.md)

## 🧪 테스트

```bash
pytest tests/
```

## 🤝 기여하기

1. 이 저장소를 포크하세요
2. 기능 브랜치를 생성하세요 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성하세요

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사인사

- OpenAI GPT 모델
- Hugging Face Transformers
- 오픈소스 커뮤니티

## 📞 연락처

- 이슈: [GitHub Issues](https://github.com/yourusername/ai-operating-shell/issues)
- 이메일: your.email@example.com

---

⭐ 이 프로젝트가 유용하다면 별표를 눌러주세요! 