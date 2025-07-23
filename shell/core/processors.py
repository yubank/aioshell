"""
명령어 처리 파이프라인

사용자 입력을 단계별로 처리하여 시스템 명령어로 변환하고 실행하는 
체인 오브 리스폰시빌리티 패턴 구현
"""

import asyncio
import subprocess
import shlex
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import get_logger


class ProcessResult:
    """처리 결과를 담는 클래스"""
    
    def __init__(self, 
                 success: bool = True,
                 output: Optional[str] = None,
                 error_message: Optional[str] = None,
                 executed_command: Optional[str] = None,
                 suggestion: Optional[str] = None,
                 should_continue: bool = True):
        self.success = success
        self.output = output
        self.error_message = error_message
        self.executed_command = executed_command
        self.suggestion = suggestion
        self.should_continue = should_continue


class CommandIntent:
    """AI가 분석한 명령어 의도"""
    
    def __init__(self,
                 intent_type: str,
                 confidence: float,
                 parameters: Dict[str, Any],
                 raw_command: Optional[str] = None,
                 risk_level: str = "safe"):
        self.intent_type = intent_type
        self.confidence = confidence
        self.parameters = parameters
        self.raw_command = raw_command
        self.risk_level = risk_level  # safe, caution, dangerous


class BaseProcessor(ABC):
    """처리기 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"processor.{name}")
    
    @abstractmethod
    async def process(self, data: Any) -> ProcessResult:
        """데이터 처리"""
        pass


class InputProcessor(BaseProcessor):
    """사용자 입력 검증 및 전처리"""
    
    def __init__(self):
        super().__init__("input")
    
    async def process(self, user_input: str) -> ProcessResult:
        """사용자 입력 검증 및 정제"""
        try:
            # 기본 검증
            if not user_input or not user_input.strip():
                return ProcessResult(
                    success=False,
                    error_message="입력이 비어있습니다",
                    should_continue=False
                )
            
            # 입력 정제
            cleaned_input = user_input.strip()
            
            # 위험한 패턴 검사
            dangerous_patterns = [
                'rm -rf /', 'del /s /q', 'format', 'fdisk',
                'shutdown', 'reboot', '>', '>>', '|',
                ';', '&&', '||', '`', '$('
            ]
            
            for pattern in dangerous_patterns:
                if pattern.lower() in cleaned_input.lower():
                    return ProcessResult(
                        success=False,
                        error_message=f"위험한 패턴이 감지되었습니다: {pattern}",
                        suggestion="안전한 명령어를 사용해 주세요",
                        should_continue=False
                    )
            
            self.logger.debug(f"Input validated: {cleaned_input}")
            return ProcessResult(success=True, output=cleaned_input)
            
        except Exception as e:
            self.logger.error(f"Input processing error: {e}")
            return ProcessResult(
                success=False,
                error_message=f"입력 처리 중 오류: {e}",
                should_continue=False
            )


class NaturalLanguageProcessor(BaseProcessor):
    """자연어 처리 및 의도 분석"""
    
    def __init__(self, ai_strategy):
        super().__init__("nlp")
        self.ai_strategy = ai_strategy
    
    async def process(self, user_input: str) -> ProcessResult:
        """자연어를 명령어 의도로 변환"""
        try:
            self.logger.debug(f"Processing natural language: {user_input}")
            
            # AI 모델을 통한 의도 분석
            intent = await self.ai_strategy.analyze_intent(user_input)
            
            if intent.confidence < 0.5:
                return ProcessResult(
                    success=False,
                    error_message="명령어를 이해할 수 없습니다",
                    suggestion="더 구체적으로 말씀해 주세요. 예: '현재 폴더의 파일 목록을 보여줘'",
                    should_continue=False
                )
            
            self.logger.debug(f"Intent analyzed: {intent.intent_type} (confidence: {intent.confidence})")
            return ProcessResult(success=True, output=intent)
            
        except Exception as e:
            self.logger.error(f"NLP processing error: {e}")
            return ProcessResult(
                success=False,
                error_message=f"자연어 처리 중 오류: {e}",
                should_continue=False
            )


class CommandMappingProcessor(BaseProcessor):
    """의도를 실제 시스템 명령어로 매핑"""
    
    def __init__(self):
        super().__init__("mapping")
        self.command_mappings = {
            "list_files": self._map_list_files,
            "find_files": self._map_find_files,
            "show_disk_usage": self._map_disk_usage,
            "show_processes": self._map_processes,
            "create_directory": self._map_create_directory,
            "delete_file": self._map_delete_file,
            "copy_file": self._map_copy_file,
            "move_file": self._map_move_file,
            "show_system_info": self._map_system_info,
        }
    
    async def process(self, intent: CommandIntent) -> ProcessResult:
        """의도를 시스템 명령어로 변환"""
        try:
            if intent.intent_type not in self.command_mappings:
                return ProcessResult(
                    success=False,
                    error_message=f"지원하지 않는 명령어 유형: {intent.intent_type}",
                    suggestion="지원되는 명령어: 파일 목록, 파일 찾기, 디스크 사용량, 프로세스 목록 등",
                    should_continue=False
                )
            
            # 매핑 함수 호출
            mapper = self.command_mappings[intent.intent_type]
            command = await mapper(intent.parameters)
            
            if not command:
                return ProcessResult(
                    success=False,
                    error_message="명령어 생성에 실패했습니다",
                    should_continue=False
                )
            
            self.logger.debug(f"Command mapped: {command}")
            return ProcessResult(success=True, output=command)
            
        except Exception as e:
            self.logger.error(f"Command mapping error: {e}")
            return ProcessResult(
                success=False,
                error_message=f"명령어 매핑 중 오류: {e}",
                should_continue=False
            )
    
    async def _map_list_files(self, params: Dict[str, Any]) -> str:
        """파일 목록 명령어 생성"""
        path = params.get("path", ".")
        show_hidden = params.get("show_hidden", False)
        detailed = params.get("detailed", True)
        
        if detailed:
            cmd = f"ls -la {shlex.quote(path)}"
        else:
            cmd = f"ls {'-a ' if show_hidden else ''}{shlex.quote(path)}"
        
        return cmd
    
    async def _map_find_files(self, params: Dict[str, Any]) -> str:
        """파일 찾기 명령어 생성"""
        name_pattern = params.get("name", "*")
        path = params.get("path", ".")
        file_type = params.get("type", "f")  # f: file, d: directory
        
        cmd = f"find {shlex.quote(path)} -type {file_type} -name {shlex.quote(name_pattern)}"
        return cmd
    
    async def _map_disk_usage(self, params: Dict[str, Any]) -> str:
        """디스크 사용량 명령어 생성"""
        path = params.get("path", ".")
        human_readable = params.get("human_readable", True)
        
        cmd = f"du {'-h ' if human_readable else ''}-s {shlex.quote(path)}"
        return cmd
    
    async def _map_processes(self, params: Dict[str, Any]) -> str:
        """프로세스 목록 명령어 생성"""
        user_only = params.get("user_only", False)
        
        if user_only:
            cmd = "ps -u $USER"
        else:
            cmd = "ps aux"
        
        return cmd
    
    async def _map_create_directory(self, params: Dict[str, Any]) -> str:
        """디렉토리 생성 명령어"""
        path = params.get("path")
        if not path:
            raise ValueError("디렉토리 경로가 필요합니다")
        
        cmd = f"mkdir -p {shlex.quote(path)}"
        return cmd
    
    async def _map_delete_file(self, params: Dict[str, Any]) -> str:
        """파일 삭제 명령어"""
        path = params.get("path")
        if not path:
            raise ValueError("파일 경로가 필요합니다")
        
        cmd = f"rm {shlex.quote(path)}"
        return cmd
    
    async def _map_copy_file(self, params: Dict[str, Any]) -> str:
        """파일 복사 명령어"""
        source = params.get("source")
        destination = params.get("destination")
        
        if not source or not destination:
            raise ValueError("원본과 대상 경로가 필요합니다")
        
        cmd = f"cp {shlex.quote(source)} {shlex.quote(destination)}"
        return cmd
    
    async def _map_move_file(self, params: Dict[str, Any]) -> str:
        """파일 이동 명령어"""
        source = params.get("source")
        destination = params.get("destination")
        
        if not source or not destination:
            raise ValueError("원본과 대상 경로가 필요합니다")
        
        cmd = f"mv {shlex.quote(source)} {shlex.quote(destination)}"
        return cmd
    
    async def _map_system_info(self, params: Dict[str, Any]) -> str:
        """시스템 정보 명령어"""
        info_type = params.get("type", "general")
        
        if info_type == "memory":
            return "free -h"
        elif info_type == "cpu":
            return "top -bn1 | head -20"
        elif info_type == "disk":
            return "df -h"
        else:
            return "uname -a && free -h && df -h"


class SafetyValidationProcessor(BaseProcessor):
    """안전성 검증"""
    
    def __init__(self):
        super().__init__("safety")
    
    async def process(self, command: str) -> ProcessResult:
        """명령어 안전성 검증"""
        try:
            # 위험한 명령어 패턴 검사
            high_risk_patterns = [
                r'rm\s+-rf\s+/',
                r'del\s+/s\s+/q',
                r'format\s+',
                r'fdisk\s+',
                r'shutdown\s*',
                r'reboot\s*',
                r'halt\s*',
                r'systemctl\s+stop',
                r'service\s+\w+\s+stop'
            ]
            
            import re
            for pattern in high_risk_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return ProcessResult(
                        success=False,
                        error_message=f"위험한 명령어가 감지되었습니다: {command}",
                        suggestion="이 명령어는 시스템에 심각한 영향을 줄 수 있습니다",
                        should_continue=False
                    )
            
            # 중간 위험도 명령어 (사용자 확인 필요)
            medium_risk_patterns = [
                r'rm\s+',
                r'del\s+',
                r'mv\s+.*\s+/',
                r'chmod\s+',
                r'chown\s+'
            ]
            
            for pattern in medium_risk_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    self.logger.warning(f"Medium risk command detected: {command}")
                    # 실제로는 여기서 사용자 확인을 받아야 함
                    # 지금은 경고만 로그에 남김
            
            self.logger.debug(f"Command safety validated: {command}")
            return ProcessResult(success=True, output=command)
            
        except Exception as e:
            self.logger.error(f"Safety validation error: {e}")
            return ProcessResult(
                success=False,
                error_message=f"안전성 검증 중 오류: {e}",
                should_continue=False
            )


class CommandExecutionProcessor(BaseProcessor):
    """명령어 실행"""
    
    def __init__(self):
        super().__init__("execution")
    
    async def process(self, command: str) -> ProcessResult:
        """시스템 명령어 실행"""
        try:
            self.logger.info(f"Executing command: {command}")
            
            # 비동기 명령어 실행
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 성공
                return ProcessResult(
                    success=True,
                    output=stdout.strip() if stdout else "명령어가 성공적으로 실행되었습니다",
                    executed_command=command
                )
            else:
                # 실행 오류
                return ProcessResult(
                    success=False,
                    error_message=f"명령어 실행 실패 (코드 {process.returncode}): {stderr.strip()}",
                    executed_command=command,
                    should_continue=False
                )
                
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return ProcessResult(
                success=False,
                error_message=f"명령어 실행 중 오류: {e}",
                executed_command=command,
                should_continue=False
            )


class ProcessorChain:
    """처리기 체인 관리"""
    
    def __init__(self, ai_strategy, config):
        self.logger = get_logger("processor_chain")
        self.ai_strategy = ai_strategy
        self.config = config
        
        # 처리기 체인 구성
        self.processors = [
            InputProcessor(),
            NaturalLanguageProcessor(ai_strategy),
            CommandMappingProcessor(),
            SafetyValidationProcessor(),
            CommandExecutionProcessor()
        ]
    
    async def process(self, user_input: str) -> ProcessResult:
        """전체 처리 체인 실행"""
        data = user_input
        
        for processor in self.processors:
            try:
                self.logger.debug(f"Processing with {processor.name}")
                result = await processor.process(data)
                
                if not result.success or not result.should_continue:
                    self.logger.warning(f"Processing stopped at {processor.name}: {result.error_message}")
                    return result
                
                # 다음 단계로 결과 전달
                data = result.output
                
            except Exception as e:
                self.logger.error(f"Error in processor {processor.name}: {e}")
                return ProcessResult(
                    success=False,
                    error_message=f"{processor.name} 처리 중 오류: {e}",
                    should_continue=False
                )
        
        # 모든 처리가 성공적으로 완료됨
        return result 