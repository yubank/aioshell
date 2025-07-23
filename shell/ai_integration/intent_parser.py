"""
자연어 명령 의도 분석기

사용자의 자연어 입력을 분석하여 실행 가능한 명령으로 변환합니다.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import get_logger


class CommandType(Enum):
    """명령어 타입 분류"""
    FILE_OPERATION = "file_operation"
    SYSTEM_INFO = "system_info"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK = "network"
    SEARCH = "search"
    DEVELOPMENT = "development"
    TEXT_PROCESSING = "text_processing"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """파싱된 의도 정보"""
    command_type: CommandType
    action: str
    parameters: Dict[str, str]
    confidence: float
    original_text: str
    suggested_command: Optional[str] = None


class IntentParser:
    """
    자연어 명령을 파싱하여 실행 가능한 명령으로 변환하는 클래스
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._init_patterns()
    
    def _init_patterns(self):
        """명령 패턴 초기화"""
        self.patterns = {
            CommandType.FILE_OPERATION: [
                (r'(파일|file).*?(찾|find|search)', 'find_files'),
                (r'(디렉토리|폴더|directory).*?(만들|create|생성)', 'create_directory'),
                (r'(파일|file).*?(삭제|delete|제거)', 'delete_file'),
                (r'(파일|file).*?(복사|copy)', 'copy_file'),
                (r'(파일|file).*?(이동|move)', 'move_file'),
                (r'(목록|list|ls).*?(파일|file)', 'list_files'),
                (r'(권한|permission).*?(변경|change)', 'change_permission'),
            ],
            CommandType.SYSTEM_INFO: [
                (r'(시스템|system).*?(정보|info)', 'system_info'),
                (r'(디스크|disk).*?(용량|space|사용량)', 'disk_usage'),
                (r'(메모리|memory|ram).*?(사용량|usage)', 'memory_usage'),
                (r'(CPU|cpu|프로세서).*?(사용량|usage)', 'cpu_usage'),
                (r'(프로세스|process).*?(목록|list)', 'process_list'),
            ],
            CommandType.NETWORK: [
                (r'(네트워크|network).*?(연결|connection)', 'network_status'),
                (r'(ping|핑)', 'ping'),
                (r'(포트|port).*?(확인|check)', 'port_check'),
                (r'(다운로드|download)', 'download'),
            ],
            CommandType.SEARCH: [
                (r'(검색|search|grep)', 'search_text'),
                (r'(찾기|find)', 'find_content'),
            ],
            CommandType.DEVELOPMENT: [
                (r'(git|깃).*?(상태|status)', 'git_status'),
                (r'(git|깃).*?(커밋|commit)', 'git_commit'),
                (r'(코드|code).*?(실행|run)', 'run_code'),
                (r'(테스트|test).*?(실행|run)', 'run_tests'),
            ]
        }
    
    def parse(self, user_input: str) -> ParsedIntent:
        """
        사용자 입력을 분석하여 의도를 파악합니다.
        
        Args:
            user_input: 사용자의 자연어 입력
            
        Returns:
            ParsedIntent: 파싱된 의도 정보
        """
        self.logger.debug(f"Parsing user input: {user_input}")
        
        user_input = user_input.strip().lower()
        
        best_match = None
        best_confidence = 0.0
        
        # 각 명령 타입에 대해 패턴 매칭 수행
        for command_type, patterns in self.patterns.items():
            for pattern, action in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    confidence = self._calculate_confidence(pattern, user_input, match)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = (command_type, action, match)
        
        if best_match:
            command_type, action, match = best_match
            parameters = self._extract_parameters(user_input, action, match)
            suggested_command = self._generate_command(command_type, action, parameters)
            
            return ParsedIntent(
                command_type=command_type,
                action=action,
                parameters=parameters,
                confidence=best_confidence,
                original_text=user_input,
                suggested_command=suggested_command
            )
        else:
            # 매칭되지 않은 경우 기본 처리
            return ParsedIntent(
                command_type=CommandType.UNKNOWN,
                action="unknown",
                parameters={},
                confidence=0.0,
                original_text=user_input,
                suggested_command=None
            )
    
    def _calculate_confidence(self, pattern: str, user_input: str, match: re.Match) -> float:
        """매칭 신뢰도 계산"""
        # 간단한 신뢰도 계산 (매칭된 텍스트 길이 기반)
        matched_length = len(match.group(0))
        total_length = len(user_input)
        
        base_confidence = matched_length / total_length
        
        # 정확한 키워드 매칭 보너스
        if '파일' in user_input and 'file' in pattern:
            base_confidence += 0.2
        if '디렉토리' in user_input and 'directory' in pattern:
            base_confidence += 0.2
        if '시스템' in user_input and 'system' in pattern:
            base_confidence += 0.2
            
        return min(base_confidence, 1.0)
    
    def _extract_parameters(self, user_input: str, action: str, match: re.Match) -> Dict[str, str]:
        """명령어 파라미터 추출"""
        parameters = {}
        
        # 파일 이름 추출
        file_patterns = [r'"([^"]+)"', r"'([^']+)'", r'(\S+\.\w+)']
        for pattern in file_patterns:
            files = re.findall(pattern, user_input)
            if files:
                parameters['files'] = files
                break
        
        # 경로 추출
        path_patterns = [r'(/[^\s]+)', r'(~/[^\s]+)', r'(\./[^\s]+)']
        for pattern in path_patterns:
            paths = re.findall(pattern, user_input)
            if paths:
                parameters['paths'] = paths
                break
        
        # 숫자 추출
        numbers = re.findall(r'\b(\d+)\b', user_input)
        if numbers:
            parameters['numbers'] = numbers
        
        return parameters
    
    def _generate_command(self, command_type: CommandType, action: str, parameters: Dict[str, str]) -> Optional[str]:
        """실행 가능한 명령어 생성"""
        command_templates = {
            'find_files': 'find . -name "{filename}" -type f',
            'create_directory': 'mkdir -p "{dirname}"',
            'delete_file': 'rm "{filename}"',
            'copy_file': 'cp "{source}" "{destination}"',
            'move_file': 'mv "{source}" "{destination}"',
            'list_files': 'ls -la',
            'system_info': 'uname -a && df -h && free -h',
            'disk_usage': 'df -h',
            'memory_usage': 'free -h',
            'cpu_usage': 'top -bn1 | head -20',
            'process_list': 'ps aux',
            'network_status': 'ip addr show && netstat -tuln',
            'ping': 'ping -c 4 {target}',
            'git_status': 'git status',
            'git_commit': 'git add . && git commit -m "{message}"',
        }
        
        template = command_templates.get(action)
        if not template:
            return None
        
        # 템플릿에 파라미터 적용
        try:
            if 'files' in parameters and len(parameters['files']) > 0:
                template = template.replace('{filename}', parameters['files'][0])
                template = template.replace('{source}', parameters['files'][0])
                if len(parameters['files']) > 1:
                    template = template.replace('{destination}', parameters['files'][1])
            
            if 'paths' in parameters and len(parameters['paths']) > 0:
                template = template.replace('{dirname}', parameters['paths'][0])
            
            # 기본값 설정
            template = template.replace('{filename}', '*')
            template = template.replace('{dirname}', 'new_directory')
            template = template.replace('{target}', 'google.com')
            template = template.replace('{message}', 'Auto commit')
            
            return template
        except Exception as e:
            self.logger.error(f"Error generating command: {e}")
            return None
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """부분 입력에 대한 제안 목록 반환"""
        suggestions = []
        
        common_patterns = [
            "파일 찾기",
            "디렉토리 만들기", 
            "시스템 정보 보기",
            "디스크 용량 확인",
            "프로세스 목록 보기",
            "네트워크 상태 확인",
            "git 상태 확인",
        ]
        
        for pattern in common_patterns:
            if partial_input.lower() in pattern.lower():
                suggestions.append(pattern)
        
        return suggestions[:5]  # 상위 5개만 반환 