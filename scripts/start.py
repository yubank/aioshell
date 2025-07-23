#!/usr/bin/env python3
"""
AI Operating Shell - 시작 스크립트

CodeLlama 기반 자연어 쉘을 시작하는 메인 스크립트입니다.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shell.core.shell_engine import AIShellEngine
from shell.utils.config import Config
from shell.utils.logging import setup_logging, get_logger
from shell.ai_integration.model_manager import ModelManager


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="AI Operating Shell - CodeLlama 기반 자연어 쉘",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/start.py                    # 기본 설정으로 시작
  python scripts/start.py -c config.yaml    # 커스텀 설정 파일 사용
  python scripts/start.py --debug           # 디버그 모드로 시작
  python scripts/start.py --model-name "codellama/CodeLlama-13b-Instruct-hf"  # 다른 모델 사용
        """
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="설정 파일 경로 (YAML 또는 JSON)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    parser.add_argument(
        "--model-name",
        type=str,
        help="사용할 CodeLlama 모델 이름"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="로그 레벨 설정"
    )
    
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        default=True,
        help="안전 모드 활성화 (기본값)"
    )
    
    parser.add_argument(
        "--no-safe-mode",
        action="store_true",
        help="안전 모드 비활성화"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="AI Operating Shell 0.1.0"
    )
    
    return parser.parse_args()


def setup_config(args):
    """설정 초기화"""
    # 기본 설정 로드
    config = Config(args.config)
    
    # 명령줄 인자로 오버라이드
    if args.debug:
        config.set("app.debug", True)
        config.set("logging.level", "DEBUG")
    
    if args.model_name:
        config.set("ai.model_name", args.model_name)
    
    if args.log_level:
        config.set("logging.level", args.log_level)
    
    if args.no_safe_mode:
        config.set("shell.safe_mode", False)
        config.set("safety.enabled", False)
    
    return config


def check_requirements():
    """필수 요구사항 확인"""
    missing_packages = []
    
    try:
        import torch
    except ImportError:
        missing_packages.append("torch")
    
    try:
        import transformers
    except ImportError:
        missing_packages.append("transformers")
    
    try:
        from rich.console import Console
    except ImportError:
        missing_packages.append("rich")
    
    try:
        from prompt_toolkit import prompt
    except ImportError:
        missing_packages.append("prompt-toolkit")
    
    if missing_packages:
        print(f"❌ 다음 패키지들이 필요합니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


async def check_and_setup_model(config):
    """모델 확인 및 초기화"""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import torch
    
    console = Console()
    model_manager = ModelManager()
    
    # 설정에서 모델 키 가져오기
    model_key = config.get("ai.model_key", "codellama-7b")
    
    # 모델이 다운로드되어 있는지 확인
    if await model_manager._is_model_downloaded(model_key):
        console.print(f"[green]✓ 모델 '{model_key}' 준비됨[/green]")
        return model_key
    
    # 모델이 없으면 다운로드
    console.print(f"[yellow]모델 '{model_key}'이 없습니다. 다운로드를 시작합니다...[/yellow]")
    
    # 모델 정보 표시
    available_models = model_manager.list_available_models()
    model_info = next((m for m in available_models if m['key'] == model_key), None)
    
    if model_info:
        console.print(f"[blue]모델: {model_info['description']}[/blue]")
        console.print(f"[blue]크기: {model_info['download_size']}[/blue]")
        console.print(f"[blue]메모리 요구사항: {model_info['memory_requirement']}[/blue]")
    
    # 자동 다운로드 (사용자 확인 없이)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"[green]모델 {model_key} 다운로드 중...", total=None)
            
            model_path = await model_manager.download_model(model_key)
            progress.update(task, description=f"[green]완료: {model_path}")
            
            console.print(f"[bold green]✓ 모델 다운로드 완료![/bold green]")
            return model_key
    
    except Exception as e:
        console.print(f"[bold red]✗ 모델 다운로드 실패: {e}[/bold red]")
        
        # 권장 모델로 대체 시도
        recommended = model_manager.get_recommended_model()
        if recommended != model_key:
            console.print(f"[yellow]권장 모델 '{recommended}'로 시도합니다...[/yellow]")
            try:
                model_path = await model_manager.download_model(recommended)
                console.print(f"[green]✓ 권장 모델 다운로드 완료: {model_path}[/green]")
                return recommended
            except Exception as e2:
                console.print(f"[red]권장 모델 다운로드도 실패: {e2}[/red]")
                raise
        else:
            raise


def display_startup_info(config, model_key):
    """시작 정보 출력"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    import torch
    
    console = Console()
    
    # 시스템 정보 테이블
    table = Table(title="🤖 AI Shell 시작 정보")
    table.add_column("항목", style="cyan")
    table.add_column("값", style="green")
    
    table.add_row("모델", model_key)
    table.add_row("디바이스", "CUDA" if torch.cuda.is_available() else "CPU")
    table.add_row("안전 모드", "활성화" if config.get("safety.enabled", True) else "비활성화")
    table.add_row("디버그 모드", "활성화" if config.get("debug", False) else "비활성화")
    table.add_row("로그 레벨", config.get("logging.level", "INFO"))
    
    console.print(table)
    console.print()


async def main():
    """메인 실행 함수"""
    try:
        # 명령줄 인자 파싱
        args = parse_arguments()
        
        # 필수 패키지 확인
        if not check_requirements():
            sys.exit(1)
        
        # 설정 초기화
        config = setup_config(args)
        
        # 로깅 시스템 초기화
        setup_logging(config.get("logging", {}))
        logger = get_logger(__name__)
        
        logger.info("Starting AI Operating Shell")
        
        # 모델 확인 및 설정
        model_key = await check_and_setup_model(config)
        
        # 설정에 모델 키 업데이트
        config.set("ai.model_key", model_key)
        
        # 시작 정보 출력
        display_startup_info(config, model_key)
        
        # AI Shell 엔진 생성 및 시작
        shell = AIShellEngine(config)
        await shell.start()
        
    except KeyboardInterrupt:
        print("\n👋 AI Shell을 종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run():
    """동기 실행 래퍼"""
    # Python 3.7+ 호환성
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main())
        finally:
            loop.close()


if __name__ == "__main__":
    run() 