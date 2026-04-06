"""
AI Shell Engine - 메인 쉘 엔진

CodeLlama 모델을 기반으로 자연어 입력을 처리하고 시스템 명령어로 변환하는 
핵심 엔진입니다.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, List, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .processors import ProcessorChain
from ..ai_integration.strategy_factory import create_ai_strategy
from ..utils.config import Config
from ..utils.logging import get_logger


class AIShellEngine:
    """
    AI Shell의 메인 엔진 클래스
    
    사용자의 자연어 입력을 받아 CodeLlama를 통해 시스템 명령어로 변환하고
    안전하게 실행하는 핵심 엔진입니다.
    """
    
    def __init__(self, config=None):
        """
        AI Shell 엔진 초기화
        
        Args:
            config: Config 객체 또는 설정 파일 경로 (선택사항)
        """
        self.console = Console()
        self.logger = get_logger(__name__)
        self.history = InMemoryHistory()
        
        # 설정 로드
        if isinstance(config, Config):
            self.config = config
        else:
            self.config = Config(config)
        
        # AI 전략 (설정 ai.provider: local_hf | ollama)
        self.ai_strategy = create_ai_strategy(self.config)
        
        # 처리 파이프라인 초기화
        self.processor_chain = ProcessorChain(self.ai_strategy, self.config)
        
        # 실행 상태
        self.is_running = False
        self.exit_requested = False
        
        self.logger.info("AI Shell Engine initialized")
    
    async def start(self) -> None:
        """AI Shell 시작"""
        if self.is_running:
            self.logger.warning("Shell is already running")
            return
        
        self.is_running = True
        self.exit_requested = False
        
        # 환영 메시지 출력
        self._display_welcome()
        
        # CodeLlama 모델 로드
        await self._initialize_ai_model()
        
        try:
            # 메인 루프 시작
            await self._main_loop()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]프로그램을 종료합니다...[/yellow]")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            self.console.print(f"[red]오류가 발생했습니다: {e}[/red]")
        finally:
            self.is_running = False
            self._display_goodbye()
    
    async def _initialize_ai_model(self) -> None:
        """AI 모델 초기화"""
        try:
            self.console.print("[blue]CodeLlama 모델을 로딩중입니다...[/blue]")
            
            await self.ai_strategy.initialize()
            
            self.console.print("[green]✓ CodeLlama 모델이 준비되었습니다![/green]")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI model: {e}")
            self.console.print(f"[red]모델 로딩에 실패했습니다: {e}[/red]")
            raise
    
    async def _main_loop(self) -> None:
        """메인 입력-처리-출력 루프"""
        while not self.exit_requested:
            try:
                # 사용자 입력 받기
                user_input = await self._get_user_input()
                
                if not user_input.strip():
                    continue
                
                # 종료 명령어 체크
                if self._is_exit_command(user_input):
                    self.exit_requested = True
                    break
                
                # 명령어 처리
                await self._process_user_input(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Ctrl+C를 눌러 종료하거나 'exit' 명령을 사용하세요[/yellow]")
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.console.print(f"[red]처리 중 오류가 발생했습니다: {e}[/red]")
    
    async def _get_user_input(self) -> str:
        """사용자 입력 받기"""
        try:
            # 현재 디렉토리 표시
            current_dir = Path.cwd().name
            prompt_text = f"[bold green]AI Shell[/bold green] [blue]{current_dir}[/blue] $ "
            
            # prompt-toolkit를 사용한 고급 입력
            user_input = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: prompt(
                    prompt_text,
                    history=self.history,
                    auto_suggest=AutoSuggestFromHistory()
                )
            )
            
            return user_input.strip()
            
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D 또는 Ctrl+C 처리
            raise KeyboardInterrupt()
    
    async def _process_user_input(self, user_input: str) -> None:
        """사용자 입력 처리"""
        try:
            self.console.print(f"[dim]입력: {user_input}[/dim]")
            
            # 처리 체인을 통해 명령어 처리
            result = await self.processor_chain.process(user_input)
            
            if result.success:
                # 성공적인 처리 결과 출력
                self._display_result(result)
            else:
                # 오류 또는 실패 결과 출력
                self._display_error(result)
                
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            self.console.print(f"[red]명령어 처리 중 오류가 발생했습니다: {e}[/red]")
    
    def _is_exit_command(self, user_input: str) -> bool:
        """종료 명령어인지 확인"""
        exit_commands = ['exit', 'quit', 'bye', '종료', '나가기', '끝']
        return user_input.lower().strip() in exit_commands
    
    def _display_welcome(self) -> None:
        """환영 메시지 출력"""
        welcome_text = Text()
        welcome_text.append("🤖 AI Operating Shell", style="bold blue")
        welcome_text.append("\n")
        welcome_text.append("CodeLlama 기반 자연어 쉘에 오신 것을 환영합니다!", style="green")
        welcome_text.append("\n\n")
        welcome_text.append("사용법:", style="bold")
        welcome_text.append("\n• 자연어로 명령어를 입력하세요")
        welcome_text.append("\n• 예: '현재 폴더 파일 목록 보여줘'")
        welcome_text.append("\n• 예: '큰 파일들을 찾아줘'")
        welcome_text.append("\n• 종료: 'exit' 또는 'quit'")
        
        panel = Panel(
            welcome_text,
            title="🚀 AI Shell 시작",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def _display_goodbye(self) -> None:
        """종료 메시지 출력"""
        goodbye_text = Text()
        goodbye_text.append("👋 AI Shell을 이용해 주셔서 감사합니다!", style="green")
        goodbye_text.append("\n")
        goodbye_text.append("다음에 또 만나요!", style="blue")
        
        panel = Panel(
            goodbye_text,
            title="🎯 종료",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _display_result(self, result) -> None:
        """명령어 실행 결과 출력"""
        if result.output:
            self.console.print("\n[bold green]실행 결과:[/bold green]")
            self.console.print(result.output)
        
        if result.executed_command:
            self.console.print(f"\n[dim]실행된 명령어: {result.executed_command}[/dim]")
        
        self.console.print()
    
    def _display_error(self, result) -> None:
        """오류 결과 출력"""
        self.console.print(f"\n[red]오류: {result.error_message}[/red]")
        
        if result.suggestion:
            self.console.print(f"[yellow]제안: {result.suggestion}[/yellow]")
        
        self.console.print()
    
    def stop(self) -> None:
        """AI Shell 중지"""
        self.exit_requested = True
        self.is_running = False
        self.logger.info("AI Shell Engine stopped")


# 편의를 위한 팩토리 함수
async def create_shell(config_path: Optional[str] = None) -> AIShellEngine:
    """AI Shell 인스턴스 생성 및 초기화"""
    shell = AIShellEngine(config_path)
    return shell


if __name__ == "__main__":
    # 직접 실행 시 테스트
    async def main():
        shell = await create_shell()
        await shell.start()
    
    asyncio.run(main()) 