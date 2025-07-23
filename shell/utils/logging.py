"""
로깅 시스템

loguru를 사용한 고급 로깅 기능을 제공합니다.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


# 전역 로거 설정 상태
_logging_configured = False
_loggers: Dict[str, Any] = {}


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    로깅 시스템 초기화
    
    Args:
        config: 로깅 설정 딕셔너리
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # 기본 설정
    default_config = {
        "level": "INFO",
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        "file": "logs/ai_shell.log",
        "max_size": "10 MB",
        "backup_count": 5,
        "colorize": True,
        "backtrace": True,
        "diagnose": True
    }
    
    if config:
        default_config.update(config)
    
    # 기존 핸들러 제거
    logger.remove()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stderr,
        level=default_config["level"],
        format=default_config["format"],
        colorize=default_config["colorize"],
        backtrace=default_config["backtrace"],
        diagnose=default_config["diagnose"]
    )
    
    # 파일 출력 설정
    log_file = Path(default_config["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_file),
        level=default_config["level"],
        format=default_config["format"],
        rotation=default_config["max_size"],
        retention=default_config["backup_count"],
        compression="zip",
        backtrace=default_config["backtrace"],
        diagnose=default_config["diagnose"]
    )
    
    _logging_configured = True
    logger.info("Logging system initialized")


def get_logger(name: str) -> Any:
    """
    이름 기반 로거 가져오기
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        설정된 로거 인스턴스
    """
    if not _logging_configured:
        setup_logging()
    
    if name not in _loggers:
        # 로거 컨텍스트 바인딩
        _loggers[name] = logger.bind(name=name)
    
    return _loggers[name]


def set_log_level(level: str) -> None:
    """
    로그 레벨 변경
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if not _logging_configured:
        setup_logging()
    
    # 기존 핸들러들의 레벨 변경
    for handler_id in logger._core.handlers:
        logger._core.handlers[handler_id].levelno = logger.level(level).no
    
    logger.info(f"Log level changed to {level}")


def add_file_handler(
    file_path: str, 
    level: str = "INFO",
    format_string: Optional[str] = None,
    rotation: str = "10 MB",
    retention: int = 5
) -> None:
    """
    추가 파일 핸들러 등록
    
    Args:
        file_path: 로그 파일 경로
        level: 로그 레벨
        format_string: 포맷 문자열
        rotation: 로테이션 크기
        retention: 보관할 파일 수
    """
    if not _logging_configured:
        setup_logging()
    
    if format_string is None:
        format_string = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
    
    log_file = Path(file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_file),
        level=level,
        format=format_string,
        rotation=rotation,
        retention=retention,
        compression="zip"
    )
    
    logger.info(f"Added file handler: {file_path}")


def configure_from_config(config_dict: Dict[str, Any]) -> None:
    """
    설정 딕셔너리로부터 로깅 구성
    
    Args:
        config_dict: 로깅 설정 딕셔너리
    """
    logging_config = config_dict.get("logging", {})
    setup_logging(logging_config)


class LoggerMixin:
    """
    클래스에 로거를 추가하는 믹스인
    """
    
    @property
    def logger(self):
        """클래스별 로거 반환"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger


# 개발 편의를 위한 단축 함수들
def debug(message: str, **kwargs) -> None:
    """디버그 로그"""
    logger.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """정보 로그"""
    logger.info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """경고 로그"""
    logger.warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """오류 로그"""
    logger.error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """치명적 오류 로그"""
    logger.critical(message, **kwargs)


def exception(message: str, **kwargs) -> None:
    """예외 로그 (스택 트레이스 포함)"""
    logger.exception(message, **kwargs)


# 성능 측정을 위한 데코레이터
def log_execution_time(func):
    """함수 실행 시간을 로그로 기록하는 데코레이터"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    
    return wrapper


# 비동기 함수용 실행 시간 측정 데코레이터
def log_async_execution_time(func):
    """비동기 함수 실행 시간을 로그로 기록하는 데코레이터"""
    import time
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    
    return wrapper


# 컨텍스트 매니저
class LogContext:
    """로깅 컨텍스트 매니저"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.level = level
        self.logger = get_logger(name)
    
    def __enter__(self):
        self.logger.log(self.level, f"Entering {self.name}")
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Exiting {self.name} with exception: {exc_val}")
        else:
            self.logger.log(self.level, f"Exiting {self.name}")


# 초기화 시 기본 설정 적용
if not _logging_configured:
    setup_logging() 