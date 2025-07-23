#!/usr/bin/env python3
"""
CodeLlama 모델 관리 CLI

CodeLlama 모델 다운로드, 삭제, 목록 조회 등을 위한 명령줄 도구
"""

import asyncio
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shell.ai_integration.model_manager import ModelManager
from shell.utils.logging import get_logger


console = Console()
logger = get_logger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='자세한 출력')
def cli(verbose):
    """CodeLlama 모델 관리 도구"""
    if verbose:
        logger.info("Verbose mode enabled")


@cli.command()
@click.option('--model', '-m', default='codellama-7b', 
              type=click.Choice(['codellama-7b', 'codellama-13b', 'codellama-34b']),
              help='다운로드할 모델 (기본값: codellama-7b)')
@click.option('--force', '-f', is_flag=True, help='강제 재다운로드')
def download(model, force):
    """CodeLlama 모델 다운로드"""
    console.print(f"\n[bold blue]CodeLlama 모델 다운로드: {model}[/bold blue]")
    
    if force:
        console.print("[yellow]강제 재다운로드 모드[/yellow]")
    
    async def download_model():
        model_manager = ModelManager()
        
        try:
            # 모델 정보 표시
            available_models = model_manager.list_available_models()
            model_info = next((m for m in available_models if m['key'] == model), None)
            
            if model_info:
                console.print(Panel.fit(
                    f"[bold]{model_info['description']}[/bold]\n"
                    f"크기: {model_info['size']}\n"
                    f"메모리 요구사항: {model_info['memory_requirement']}\n"
                    f"다운로드 크기: {model_info['download_size']}\n"
                    f"권장 모델: {'예' if model_info['recommended'] else '아니오'}",
                    title="모델 정보"
                ))
            
            # 확인
            if not force and not click.confirm(f"\n{model} 모델을 다운로드하시겠습니까?"):
                console.print("[yellow]다운로드가 취소되었습니다.[/yellow]")
                return
            
            # 다운로드 진행
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                
                task = progress.add_task(f"[green]모델 {model} 다운로드 중...", total=None)
                
                try:
                    model_path = await model_manager.download_model(model, force)
                    progress.update(task, description=f"[green]완료: {model_path}")
                    
                    console.print(f"\n[bold green]✓ 모델 다운로드 완료![/bold green]")
                    console.print(f"위치: {model_path}")
                    
                except Exception as e:
                    progress.update(task, description=f"[red]오류: {str(e)}")
                    console.print(f"\n[bold red]✗ 다운로드 실패: {e}[/bold red]")
                    sys.exit(1)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
            sys.exit(1)
    
    # 비동기 실행
    try:
        asyncio.run(download_model())
    except Exception as e:
        console.print(f"[bold red]오류: {e}[/bold red]")
        sys.exit(1)


@cli.command()
def list():
    """사용 가능한 모델 목록 표시"""
    console.print("\n[bold blue]CodeLlama 모델 목록[/bold blue]")
    
    async def list_models():
        model_manager = ModelManager()
        
        # 사용 가능한 모델들
        table = Table(title="사용 가능한 모델")
        table.add_column("키", style="cyan", no_wrap=True)
        table.add_column("크기", style="magenta")
        table.add_column("설명", style="white")
        table.add_column("메모리", style="yellow")
        table.add_column("다운로드 크기", style="green")
        table.add_column("권장", style="red", justify="center")
        
        available_models = model_manager.list_available_models()
        for model in available_models:
            table.add_row(
                model['key'],
                model['size'],
                model['description'],
                model['memory_requirement'],
                model['download_size'],
                "✓" if model['recommended'] else ""
            )
        
        console.print(table)
        
        # 다운로드된 모델들
        downloaded_models = await model_manager.list_downloaded_models()
        
        if downloaded_models:
            console.print("\n")
            downloaded_table = Table(title="다운로드된 모델")
            downloaded_table.add_column("키", style="cyan", no_wrap=True)
            downloaded_table.add_column("크기", style="magenta")
            downloaded_table.add_column("상태", style="green")
            downloaded_table.add_column("경로", style="white")
            
            for model in downloaded_models:
                downloaded_table.add_row(
                    model['key'],
                    model['size'],
                    model['status'],
                    model['path']
                )
            
            console.print(downloaded_table)
        else:
            console.print("\n[yellow]다운로드된 모델이 없습니다.[/yellow]")
    
    asyncio.run(list_models())


@cli.command()
@click.argument('model_key')
@click.option('--yes', '-y', is_flag=True, help='확인 없이 삭제')
def delete(model_key, yes):
    """다운로드된 모델 삭제"""
    console.print(f"\n[bold red]모델 삭제: {model_key}[/bold red]")
    
    async def delete_model():
        model_manager = ModelManager()
        
        # 모델 존재 확인
        downloaded_models = await model_manager.list_downloaded_models()
        model_exists = any(m['key'] == model_key for m in downloaded_models)
        
        if not model_exists:
            console.print(f"[red]모델 '{model_key}'을 찾을 수 없습니다.[/red]")
            return
        
        # 확인
        if not yes and not click.confirm(f"모델 '{model_key}'을 삭제하시겠습니까?"):
            console.print("[yellow]삭제가 취소되었습니다.[/yellow]")
            return
        
        # 삭제 실행
        try:
            success = await model_manager.delete_model(model_key)
            if success:
                console.print(f"[bold green]✓ 모델 '{model_key}' 삭제 완료[/bold green]")
            else:
                console.print(f"[red]모델 '{model_key}' 삭제 실패[/red]")
        except Exception as e:
            console.print(f"[bold red]삭제 중 오류: {e}[/bold red]")
    
    asyncio.run(delete_model())


@cli.command()
def info():
    """시스템 정보 및 권장 모델 표시"""
    console.print("\n[bold blue]시스템 정보[/bold blue]")
    
    model_manager = ModelManager()
    
    # 시스템 정보
    import torch
    import psutil
    
    info_table = Table(title="시스템 사양")
    info_table.add_column("항목", style="cyan")
    info_table.add_column("값", style="white")
    
    # GPU 정보
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        info_table.add_row("GPU", f"{gpu_name}")
        info_table.add_row("GPU 메모리", f"{gpu_memory:.1f} GB")
    else:
        info_table.add_row("GPU", "사용 불가")
    
    # RAM 정보
    ram_total = psutil.virtual_memory().total / (1024**3)
    ram_available = psutil.virtual_memory().available / (1024**3)
    info_table.add_row("총 RAM", f"{ram_total:.1f} GB")
    info_table.add_row("사용 가능 RAM", f"{ram_available:.1f} GB")
    
    console.print(info_table)
    
    # 권장 모델
    recommended = model_manager.get_recommended_model()
    console.print(f"\n[bold green]권장 모델: {recommended}[/bold green]")


if __name__ == "__main__":
    cli() 