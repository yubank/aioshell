"""
CodeLlama 전략 구현

Hugging Face Transformers를 사용하여 CodeLlama 모델을 로드하고
자연어를 쉘 명령어로 변환하는 AI 전략 클래스
"""

import asyncio
import re
from typing import Dict, List, Optional, Any

# 선택적 import
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM, 
        BitsAndBytesConfig,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from ..core.processors import CommandIntent
from ..utils.logging import get_logger
from .model_manager import ModelManager


class CodeLlamaStrategy:
    """
    CodeLlama 모델을 사용한 자연어 처리 전략
    
    Hugging Face의 CodeLlama 모델을 로드하여 한국어 자연어를 
    리눅스/bash 명령어로 변환합니다.
    """
    
    def __init__(self, config):
        self.logger = get_logger(__name__)
        self.config = config
        
        # 의존성 확인
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available. AI features will be limited.")
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available. Model loading will not work.")
        
        # 모델 매니저 초기화
        self.model_manager = ModelManager()
        
        # 모델 설정
        self.model_key = config.get("model_key", "codellama-7b")
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.max_length = config.get("max_length", 512)
        self.temperature = config.get("temperature", 0.1)
        
        # 모델 컴포넌트 (지연 로딩)
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.initialized = False
        self.model_path = None
        
        # 명령어 패턴 매핑
        self.intent_patterns = self._build_intent_patterns()
        
        self.logger.info(f"CodeLlama strategy initialized for device: {self.device}")
        self.logger.info(f"Model key: {self.model_key}")
    
    async def initialize(self) -> None:
        """모델 로드 및 초기화"""
        if self.initialized:
            self.logger.warning("Model already initialized")
            return
        
        try:
            self.logger.info(f"Initializing CodeLlama model: {self.model_key}")
            
            # 1. 모델 다운로드 (필요한 경우)
            self.model_path = await self.model_manager.download_model(self.model_key)
            self.logger.info(f"Model available at: {self.model_path}")
            
            # 2. 8-bit 양자화 설정 (메모리 절약)
            quantization_config = None
            if self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    bnb_8bit_compute_dtype=torch.float16,
                    bnb_8bit_use_double_quant=True
                )
            
            # 3. 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                local_files_only=True  # 오프라인 사용
            )
            
            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 4. 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                local_files_only=True  # 오프라인 사용
            )
            
            # 5. 파이프라인 생성
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                max_length=self.max_length,
                temperature=self.temperature,
                do_sample=True,
                return_full_text=False
            )
            
            self.initialized = True
            self.logger.info(f"CodeLlama model '{self.model_key}' loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CodeLlama model: {e}")
            # 상세한 오류 정보 제공
            if "No such file or directory" in str(e):
                self.logger.error("Model files not found. Please ensure the model is properly downloaded.")
            elif "CUDA out of memory" in str(e):
                self.logger.error("GPU memory insufficient. Consider using CPU or smaller model.")
            raise
    
    async def analyze_intent(self, user_input: str) -> CommandIntent:
        """
        자연어 입력을 분석하여 명령어 의도를 파악
        
        Args:
            user_input: 사용자의 자연어 입력
            
        Returns:
            CommandIntent: 분석된 명령어 의도
        """
        if not self.initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        try:
            self.logger.debug(f"Analyzing intent for: {user_input}")
            
            # 1차: 패턴 매칭으로 빠른 분류
            quick_intent = self._quick_pattern_match(user_input)
            if quick_intent:
                self.logger.debug(f"Quick pattern match: {quick_intent.intent_type}")
                return quick_intent
            
            # 2차: CodeLlama 모델을 사용한 정교한 분석
            model_intent = await self._analyze_with_model(user_input)
            
            return model_intent
            
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            # 실패 시 기본 의도 반환
            return CommandIntent(
                intent_type="unknown",
                confidence=0.0,
                parameters={},
                raw_command=user_input
            )
    
    def _quick_pattern_match(self, user_input: str) -> Optional[CommandIntent]:
        """패턴 매칭을 통한 빠른 의도 분류"""
        text = user_input.lower().strip()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern_data in patterns:
                if re.search(pattern_data["pattern"], text, re.IGNORECASE):
                    # 매개변수 추출
                    params = self._extract_parameters(text, pattern_data.get("param_extractors", {}))
                    
                    return CommandIntent(
                        intent_type=intent_type,
                        confidence=0.9,  # 패턴 매칭은 높은 신뢰도
                        parameters=params,
                        raw_command=user_input
                    )
        
        return None
    
    async def _analyze_with_model(self, user_input: str) -> CommandIntent:
        """CodeLlama 모델을 사용한 정교한 의도 분석"""
        
        # 프롬프트 구성
        prompt = self._build_analysis_prompt(user_input)
        
        try:
            # 모델 추론 (비동기)
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.pipeline(prompt, max_new_tokens=100, num_return_sequences=1)
            )
            
            # 결과 파싱
            generated_text = result[0]["generated_text"].strip()
            intent = self._parse_model_output(generated_text, user_input)
            
            self.logger.debug(f"Model analysis result: {intent.intent_type} (confidence: {intent.confidence})")
            return intent
            
        except Exception as e:
            self.logger.error(f"Model analysis failed: {e}")
            return CommandIntent(
                intent_type="unknown",
                confidence=0.0,
                parameters={},
                raw_command=user_input
            )
    
    def _build_analysis_prompt(self, user_input: str) -> str:
        """CodeLlama를 위한 분석 프롬프트 구성"""
        
        prompt = f"""<s>[INST] 다음 한국어 자연어 입력을 Linux/bash 명령어 의도로 분석해주세요.

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

        return prompt
    
    def _parse_model_output(self, model_output: str, original_input: str) -> CommandIntent:
        """모델 출력을 CommandIntent로 파싱"""
        
        try:
            # 기본값
            intent_type = "unknown"
            confidence = 0.5
            parameters = {}
            raw_command = None
            
            # 정규식으로 파싱
            intent_match = re.search(r'INTENT:\s*(\w+)', model_output)
            if intent_match:
                intent_type = intent_match.group(1)
            
            confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', model_output)
            if confidence_match:
                confidence = float(confidence_match.group(1))
            
            params_match = re.search(r'PARAMETERS:\s*(.+?)(?=COMMAND|$)', model_output, re.DOTALL)
            if params_match:
                params_str = params_match.group(1).strip()
                parameters = self._parse_parameters(params_str)
            
            command_match = re.search(r'COMMAND:\s*(.+)', model_output)
            if command_match:
                raw_command = command_match.group(1).strip()
            
            return CommandIntent(
                intent_type=intent_type,
                confidence=confidence,
                parameters=parameters,
                raw_command=raw_command
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse model output: {e}")
            return CommandIntent(
                intent_type="unknown",
                confidence=0.0,
                parameters={},
                raw_command=original_input
            )
    
    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """매개변수 문자열을 딕셔너리로 파싱"""
        parameters = {}
        
        try:
            # key=value 형태 파싱
            param_pairs = re.findall(r'(\w+)=([^,\n]+)', params_str)
            for key, value in param_pairs:
                # 타입 변환
                value = value.strip()
                if value.lower() in ['true', 'false']:
                    parameters[key] = value.lower() == 'true'
                elif value.isdigit():
                    parameters[key] = int(value)
                else:
                    parameters[key] = value
                    
        except Exception as e:
            self.logger.warning(f"Failed to parse parameters: {e}")
        
        return parameters
    
    def _extract_parameters(self, text: str, extractors: Dict[str, str]) -> Dict[str, Any]:
        """패턴 매칭에서 매개변수 추출"""
        parameters = {}
        
        for param_name, extractor_pattern in extractors.items():
            match = re.search(extractor_pattern, text, re.IGNORECASE)
            if match:
                parameters[param_name] = match.group(1)
        
        return parameters
    
    def _build_intent_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """의도 분류를 위한 패턴 매핑 구성"""
        
        return {
            "list_files": [
                {
                    "pattern": r"(파일|목록|리스트|보여|표시|ls).*(폴더|디렉터리|현재)",
                    "param_extractors": {
                        "detailed": r"(자세히|세부|상세)",
                        "path": r"([/\w.-]+)\s*폴더"
                    }
                },
                {
                    "pattern": r"(현재|이곳|여기).*(파일|목록|뭐)",
                    "param_extractors": {}
                }
            ],
            
            "find_files": [
                {
                    "pattern": r"(찾아|검색|find).*(파일|확장자)",
                    "param_extractors": {
                        "name": r"['\"]([^'\"]+)['\"]",
                        "path": r"([/\w.-]+)\s*에서"
                    }
                },
                {
                    "pattern": r"(큰|대용량|사이즈).*(파일)",
                    "param_extractors": {}
                }
            ],
            
            "show_disk_usage": [
                {
                    "pattern": r"(디스크|용량|공간|저장).*(사용|남은|확인)",
                    "param_extractors": {}
                },
                {
                    "pattern": r"(du|df|용량).*(체크|확인)",
                    "param_extractors": {}
                }
            ],
            
            "show_processes": [
                {
                    "pattern": r"(프로세스|실행중|ps).*(목록|보기|확인)",
                    "param_extractors": {}
                },
                {
                    "pattern": r"(실행|돌아가는).*(프로그램|작업)",
                    "param_extractors": {}
                }
            ],
            
            "create_directory": [
                {
                    "pattern": r"(만들어|생성|mkdir).*(폴더|디렉터리)",
                    "param_extractors": {
                        "path": r"['\"]([^'\"]+)['\"]|(\w+)\s*폴더"
                    }
                }
            ],
            
            "delete_file": [
                {
                    "pattern": r"(삭제|지워|제거|rm).*(파일|폴더)",
                    "param_extractors": {
                        "path": r"['\"]([^'\"]+)['\"]"
                    }
                }
            ],
            
            "copy_file": [
                {
                    "pattern": r"(복사|copy|cp).*(파일|폴더)",
                    "param_extractors": {
                        "source": r"['\"]([^'\"]+)['\"]",
                        "destination": r"에서\s+['\"]([^'\"]+)['\"]"
                    }
                }
            ],
            
            "move_file": [
                {
                    "pattern": r"(이동|move|mv).*(파일|폴더)",
                    "param_extractors": {
                        "source": r"['\"]([^'\"]+)['\"]",
                        "destination": r"에서\s+['\"]([^'\"]+)['\"]"
                    }
                }
            ],
            
            "show_system_info": [
                {
                    "pattern": r"(시스템|정보|환경|스펙).*(확인|보기|정보)",
                    "param_extractors": {
                        "type": r"(메모리|CPU|디스크|일반)"
                    }
                }
            ]
        }
    
    async def get_available_models(self) -> List[Dict]:
        """사용 가능한 모델 목록 반환"""
        return self.model_manager.list_available_models()
    
    async def get_downloaded_models(self) -> List[Dict]:
        """다운로드된 모델 목록 반환"""
        return await self.model_manager.list_downloaded_models()
    
    async def download_specific_model(self, model_key: str, force_download: bool = False) -> str:
        """특정 모델 다운로드"""
        return await self.model_manager.download_model(model_key, force_download)
    
    async def delete_model(self, model_key: str) -> bool:
        """모델 삭제"""
        return await self.model_manager.delete_model(model_key)
    
    def get_recommended_model(self) -> str:
        """권장 모델 반환"""
        return self.model_manager.get_recommended_model()
    
    def cleanup(self) -> None:
        """리소스 정리"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if self.pipeline:
            del self.pipeline
        
        # GPU 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.initialized = False
        self.model_path = None
        self.logger.info("CodeLlama resources cleaned up") 