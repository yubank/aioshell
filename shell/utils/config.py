"""
설정 관리 모듈

YAML, JSON, 환경변수를 통한 설정 관리를 제공합니다.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

from .logging import get_logger


class Config:
    """
    애플리케이션 설정 관리 클래스
    
    YAML 설정 파일, 환경변수, 기본값을 통한 계층적 설정 관리
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        
        # 기본 설정
        self._config = self._get_default_config()
        
        # .env 파일 로드
        self._load_env_file()
        
        # 설정 파일 로드
        if config_path:
            self._load_config_file(config_path)
        else:
            self._load_default_config_files()
        
        # 환경변수로 오버라이드
        self._load_environment_variables()
        
        self.logger.info("Configuration loaded successfully")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 가져오기
        
        Args:
            key: 설정 키 (dot notation 지원, 예: 'ai.model_name')
            default: 기본값
            
        Returns:
            설정값 또는 기본값
        """
        try:
            value = self._config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        설정값 설정
        
        Args:
            key: 설정 키 (dot notation 지원)
            value: 설정값
        """
        config = self._config
        parts = key.split('.')
        
        # 중간 딕셔너리들 생성
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # 마지막 값 설정
        config[parts[-1]] = value
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """
        설정 딕셔너리 업데이트
        
        Args:
            new_config: 새로운 설정 딕셔너리
        """
        self._deep_update(self._config, new_config)
    
    def save(self, config_path: str) -> None:
        """
        현재 설정을 파일에 저장
        
        Args:
            config_path: 저장할 파일 경로
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            else:  # YAML
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 딕셔너리 반환"""
        return {
            "app": {
                "name": "AI Operating Shell",
                "version": "0.1.0",
                "debug": False
            },
            
            "ai": {
                "model_name": "codellama/CodeLlama-7b-Instruct-hf",
                "max_length": 512,
                "temperature": 0.1,
                "confidence_threshold": 0.5,
                "use_quantization": True,
                "cache_enabled": True,
                "cache_size": 1000
            },
            
            "shell": {
                "prompt_style": "default",
                "auto_suggest": True,
                "history_size": 1000,
                "command_timeout": 300,  # 5분
                "safe_mode": True
            },
            
            "safety": {
                "enabled": True,
                "require_confirmation": True,
                "dangerous_patterns": [
                    "rm -rf /",
                    "del /s /q",
                    "format",
                    "fdisk",
                    "shutdown",
                    "reboot"
                ],
                "allowed_commands": [
                    "ls", "dir", "pwd", "cd", "cat", "head", "tail",
                    "grep", "find", "ps", "top", "df", "du", "free",
                    "uname", "whoami", "date", "echo", "mkdir", "cp", "mv"
                ]
            },
            
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/ai_shell.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            
            "paths": {
                "config_dir": "~/.ai-shell",
                "models_dir": "models",
                "cache_dir": "cache",
                "logs_dir": "logs"
            }
        }
    
    def _load_env_file(self) -> None:
        """환경변수 파일(.env) 로드"""
        env_files = ['.env', '.env.local', Path.home() / '.ai-shell' / '.env']
        
        for env_file in env_files:
            if Path(env_file).exists():
                load_dotenv(env_file)
                self.logger.debug(f"Loaded environment file: {env_file}")
    
    def _load_config_file(self, config_path: str) -> None:
        """설정 파일 로드"""
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                self.logger.warning(f"Config file not found: {config_path}")
                return
            
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
            else:  # YAML
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
            
            if file_config:
                self._deep_update(self._config, file_config)
                self.logger.info(f"Loaded config file: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_path}: {e}")
            raise
    
    def _load_default_config_files(self) -> None:
        """기본 설정 파일들 로드"""
        default_paths = [
            "config.yaml",
            "config.yml", 
            "config.json",
            Path.home() / ".ai-shell" / "config.yaml",
            Path.home() / ".ai-shell" / "config.yml",
            Path.home() / ".ai-shell" / "config.json"
        ]
        
        for config_path in default_paths:
            if Path(config_path).exists():
                self._load_config_file(str(config_path))
                break
    
    def _load_environment_variables(self) -> None:
        """환경변수를 통한 설정 오버라이드"""
        env_mappings = {
            # AI 설정
            'AI_MODEL_NAME': 'ai.model_name',
            'AI_MAX_LENGTH': 'ai.max_length',
            'AI_TEMPERATURE': 'ai.temperature',
            'AI_CONFIDENCE_THRESHOLD': 'ai.confidence_threshold',
            
            # 쉘 설정
            'SHELL_SAFE_MODE': 'shell.safe_mode',
            'SHELL_COMMAND_TIMEOUT': 'shell.command_timeout',
            
            # 안전성 설정
            'SAFETY_ENABLED': 'safety.enabled',
            'SAFETY_REQUIRE_CONFIRMATION': 'safety.require_confirmation',
            
            # 로깅 설정
            'LOG_LEVEL': 'logging.level',
            'LOG_FILE': 'logging.file',
            
            # 디버그 모드
            'DEBUG': 'app.debug'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 타입 변환
                converted_value = self._convert_env_value(env_value)
                self.set(config_key, converted_value)
                self.logger.debug(f"Set {config_key} = {converted_value} from {env_var}")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """환경변수 값 타입 변환"""
        # 불린 값
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # 숫자 값
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 문자열 값
        return value
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """딕셔너리 깊은 업데이트"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get_model_config(self) -> Dict[str, Any]:
        """AI 모델 관련 설정 반환"""
        return self.get('ai', {})
    
    def get_shell_config(self) -> Dict[str, Any]:
        """쉘 관련 설정 반환"""
        return self.get('shell', {})
    
    def get_safety_config(self) -> Dict[str, Any]:
        """안전성 관련 설정 반환"""
        return self.get('safety', {})
    
    def is_debug_mode(self) -> bool:
        """디버그 모드 여부"""
        return self.get('app.debug', False)
    
    def is_safe_mode(self) -> bool:
        """안전 모드 여부"""
        return self.get('shell.safe_mode', True)
    
    def __repr__(self) -> str:
        return f"Config({self._config})" 