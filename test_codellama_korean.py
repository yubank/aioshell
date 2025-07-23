#!/usr/bin/env python3
"""
CodeLlama 한국어 테스트 스크립트

CodeLlama 모델의 한국어 자연어 처리 능력을 테스트합니다.
"""

import asyncio
import time
import torch
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM, 
        BitsAndBytesConfig,
        pipeline
    )
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요:")
    print("pip install transformers torch rich")
    sys.exit(1)


console = Console()


def display_system_info():
    """시스템 정보 출력"""
    table = Table(title="🤖 시스템 정보")
    table.add_column("항목", style="cyan")
    table.add_column("값", style="green")
    
    table.add_row("Python 버전", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    table.add_row("PyTorch 버전", torch.__version__)
    table.add_row("CUDA 사용 가능", "예" if torch.cuda.is_available() else "아니오")
    
    if torch.cuda.is_available():
        table.add_row("GPU 이름", torch.cuda.get_device_name(0))
        table.add_row("GPU 메모리", f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
    
    console.print(table)
    console.print()


def get_model_info():
    """사용할 모델 정보"""
    models = [
        {
            "name": "CodeLlama-7B-Instruct",
            "path": "codellama/CodeLlama-7b-Instruct-hf",
            "size": "~13GB",
            "description": "가장 작은 CodeLlama 모델 (추천)"
        },
        {
            "name": "CodeLlama-13B-Instruct", 
            "path": "codellama/CodeLlama-13b-Instruct-hf",
            "size": "~26GB",
            "description": "중간 크기 모델 (더 좋은 성능)"
        },
        {
            "name": "CodeLlama-34B-Instruct",
            "path": "codellama/CodeLlama-34b-Instruct-hf", 
            "size": "~68GB",
            "description": "가장 큰 모델 (최고 성능)"
        }
    ]
    
    table = Table(title="📚 사용 가능한 CodeLlama 모델들")
    table.add_column("모델명", style="cyan")
    table.add_column("크기", style="yellow")
    table.add_column("설명", style="green")
    
    for model in models:
        table.add_row(model["name"], model["size"], model["description"])
    
    console.print(table)
    console.print()
    
    return models


async def load_model(model_path: str):
    """CodeLlama 모델 로드"""
    console.print(f"[blue]CodeLlama 모델을 로딩중입니다: {model_path}[/blue]")
    
    try:
        # 양자화 설정 (메모리 절약)
        if torch.cuda.is_available():
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                bnb_8bit_compute_dtype=torch.float16,
                bnb_8bit_use_double_quant=True
            )
        else:
            quantization_config = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # 토크나이저 로드
            task1 = progress.add_task("[cyan]토크나이저 로딩...", total=None)
            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            progress.update(task1, completed=True)
            
            # 모델 로드
            task2 = progress.add_task("[cyan]모델 로딩...", total=None)
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=quantization_config,
                device_map="auto" if torch.cuda.is_available() else None,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True
            )
            
            progress.update(task2, completed=True)
            
            # 파이프라인 생성
            task3 = progress.add_task("[cyan]파이프라인 생성...", total=None)
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device_map="auto" if torch.cuda.is_available() else None,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                max_length=512,
                temperature=0.1,
                do_sample=True,
                return_full_text=False
            )
            
            progress.update(task3, completed=True)
        
        console.print("[green]✓ 모델 로딩 완료![/green]")
        return pipe
        
    except Exception as e:
        console.print(f"[red]모델 로딩 실패: {e}[/red]")
        return None


def get_korean_test_prompts():
    """한국어 테스트 프롬프트들"""
    return [
        {
            "prompt": "현재 디렉토리의 파일 목록을 보고 싶어요",
            "expected": "ls 명령어 관련",
            "category": "파일 관리"
        },
        {
            "prompt": "큰 파일들을 찾아주세요",
            "expected": "find 명령어 관련",
            "category": "파일 검색"
        },
        {
            "prompt": "디스크 사용량을 확인하고 싶습니다",
            "expected": "df, du 명령어 관련",
            "category": "시스템 정보"
        },
        {
            "prompt": "실행중인 프로세스를 보여주세요",
            "expected": "ps 명령어 관련", 
            "category": "프로세스 관리"
        },
        {
            "prompt": "새 폴더를 만들고 싶어요",
            "expected": "mkdir 명령어 관련",
            "category": "디렉토리 관리"
        }
    ]


async def test_korean_understanding(pipe, prompts):
    """한국어 이해력 테스트"""
    console.print(Panel.fit("🇰🇷 한국어 자연어 처리 테스트", title="테스트 시작", border_style="blue"))
    
    results = []
    
    for i, test_case in enumerate(prompts, 1):
        console.print(f"\n[bold blue]테스트 {i}/{len(prompts)}: {test_case['category']}[/bold blue]")
        console.print(f"[cyan]입력:[/cyan] {test_case['prompt']}")
        
        # 프롬프트 구성
        full_prompt = f"""<s>[INST] 다음 한국어 자연어 입력을 Linux/bash 명령어로 변환해주세요.

사용자 입력: "{test_case['prompt']}"

다음 형식으로 응답해주세요:
INTENT: [의도 유형]
CONFIDENCE: [0.0-1.0 신뢰도]
COMMAND: [추천 명령어]
EXPLANATION: [한국어 설명]

[/INST]"""
        
        try:
            start_time = time.time()
            
            # 모델 추론
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pipe(full_prompt, max_new_tokens=150, num_return_sequences=1)
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            generated_text = result[0]["generated_text"].strip()
            
            console.print(f"[green]응답 시간:[/green] {response_time:.2f}초")
            console.print(f"[green]모델 출력:[/green]")
            console.print(Panel(generated_text, border_style="green"))
            
            # 결과 저장
            results.append({
                "prompt": test_case['prompt'],
                "category": test_case['category'],
                "expected": test_case['expected'],
                "output": generated_text,
                "response_time": response_time
            })
            
        except Exception as e:
            console.print(f"[red]오류 발생: {e}[/red]")
            results.append({
                "prompt": test_case['prompt'],
                "category": test_case['category'],
                "expected": test_case['expected'],
                "output": f"ERROR: {e}",
                "response_time": -1
            })
    
    return results


def analyze_results(results):
    """결과 분석 및 출력"""
    console.print("\n" + "="*50)
    console.print(Panel.fit("📊 테스트 결과 분석", border_style="yellow"))
    
    # 통계 테이블
    stats_table = Table(title="📈 성능 통계")
    stats_table.add_column("항목", style="cyan")
    stats_table.add_column("값", style="green")
    
    success_count = len([r for r in results if not r["output"].startswith("ERROR")])
    avg_response_time = sum([r["response_time"] for r in results if r["response_time"] > 0]) / len(results)
    
    stats_table.add_row("총 테스트", str(len(results)))
    stats_table.add_row("성공", str(success_count))
    stats_table.add_row("성공률", f"{success_count/len(results)*100:.1f}%")
    stats_table.add_row("평균 응답 시간", f"{avg_response_time:.2f}초")
    
    console.print(stats_table)
    
    # 개별 결과
    console.print("\n[bold yellow]개별 테스트 결과:[/bold yellow]")
    for i, result in enumerate(results, 1):
        status = "✅" if not result["output"].startswith("ERROR") else "❌"
        console.print(f"{status} {i}. {result['category']}: {result['prompt']}")
        if result["response_time"] > 0:
            console.print(f"   응답시간: {result['response_time']:.2f}초")


async def main():
    """메인 실행 함수"""
    console.print(Panel.fit("🤖 CodeLlama 한국어 능력 테스트", border_style="blue"))
    
    # 시스템 정보 출력
    display_system_info()
    
    # 모델 정보 출력
    models = get_model_info()
    
    # 사용할 모델 선택 (기본: 7B)
    model_path = "codellama/CodeLlama-7b-Instruct-hf"
    console.print(f"[blue]선택된 모델: {model_path}[/blue]")
    console.print(f"[yellow]참고: 첫 실행 시 모델 다운로드로 인해 시간이 오래 걸릴 수 있습니다.[/yellow]\n")
    
    # 모델 로드
    pipe = await load_model(model_path)
    
    if pipe is None:
        console.print("[red]모델 로딩에 실패했습니다. 프로그램을 종료합니다.[/red]")
        return
    
    # 한국어 테스트 실행
    prompts = get_korean_test_prompts()
    results = await test_korean_understanding(pipe, prompts)
    
    # 결과 분석
    analyze_results(results)
    
    console.print("\n[green]테스트 완료! 🎉[/green]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]예상치 못한 오류: {e}[/red]")
        import traceback
        traceback.print_exc() 