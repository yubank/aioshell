#!/usr/bin/env python3
"""
AOSH - AI Operating Shell

자연어와 리눅스 명령어를 모두 처리할 수 있는 AI 기반 쉘
"""

import sys
import os
import subprocess
import re
import shlex
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

console = Console()

try:
    import psutil as _psutil
except ImportError:
    _psutil = None


def _detect_invoking_shell() -> dict:
    """
    AOSH를 실행한 상위 쉘 종류를 최대한 추정합니다.
    `python aosh.py`처럼 부모가 python이면 조상 프로세스를 따라갑니다.
    """
    ctx = {
        "kind": "unknown",
        "label": "알 수 없음",
        "parent_name": None,
        "parent_exe": None,
        "posix_shell_env": os.environ.get("SHELL"),
        "comspec": os.environ.get("COMSPEC"),
    }

    if _psutil is None:
        if os.name == "nt":
            if os.environ.get("PSModulePath"):
                ctx["kind"] = "powershell"
                ctx["label"] = "PowerShell (환경 변수 추정)"
            else:
                ctx["kind"] = "cmd"
                ctx["label"] = "cmd (추정, psutil 없음)"
        elif ctx["posix_shell_env"]:
            ctx["kind"] = "posix"
            ctx["label"] = ctx["posix_shell_env"]
        return ctx

    skip_names = (
        "python.exe",
        "python3.exe",
        "pythonw.exe",
        "py.exe",
        "conda.exe",
        "conda-run.exe",
    )

    try:
        proc = _psutil.Process(os.getpid())
    except Exception:
        return ctx

    for _ in range(12):
        try:
            proc = proc.parent()
        except Exception:
            break
        if proc is None:
            break
        try:
            pname = (proc.name() or "").lower()
            exe = proc.exe()
        except Exception:
            continue

        if any(pname == s or pname.startswith("python") for s in skip_names):
            continue

        ctx["parent_name"] = proc.name()
        ctx["parent_exe"] = exe

        if "pwsh" in pname or "powershell" in pname:
            ctx["kind"] = "powershell"
            ctx["label"] = "PowerShell"
            return ctx
        if pname == "cmd.exe":
            ctx["kind"] = "cmd"
            ctx["label"] = "명령 프롬프트 (cmd.exe)"
            return ctx
        if "bash" in pname or "git-bash" in pname:
            ctx["kind"] = "bash"
            ctx["label"] = "Bash"
            return ctx
        if "zsh" in pname:
            ctx["kind"] = "zsh"
            ctx["label"] = "zsh"
            return ctx
        if "fish" in pname:
            ctx["kind"] = "fish"
            ctx["label"] = "fish"
            return ctx
        if pname in ("sh", "dash") or pname.endswith("/sh"):
            ctx["kind"] = "sh"
            ctx["label"] = "sh"
            return ctx
        if "windowsterminal" in pname or "wt.exe" in pname:
            continue
        if "cursor" in pname or "code.exe" in pname:
            ctx["kind"] = "ide_terminal"
            ctx["label"] = f"IDE/에디터에서 실행 ({proc.name()})"
            return ctx

    if os.name != "nt" and ctx["posix_shell_env"]:
        ctx["kind"] = "posix"
        ctx["label"] = ctx["posix_shell_env"]
    elif os.name == "nt" and os.environ.get("PSModulePath"):
        ctx["kind"] = "powershell"
        ctx["label"] = "PowerShell (환경 변수 추정)"
    return ctx


class AOSHShell:
    """AI Operating Shell - 자연어와 명령어를 모두 처리하는 쉘"""
    
    def __init__(self):
        self.current_dir = os.getcwd()
        self.history = []
        self.shell_context = _detect_invoking_shell()
        
        # 기본 명령어 완성
        self.command_completer = WordCompleter([
            'ls', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'cat', 'grep',
            'find', 'ps', 'top', 'kill', 'chmod', 'chown', 'tar', 'zip', 'unzip',
            'help', 'exit', 'quit', 'clear', 'history'
        ])
        
        # 자연어 패턴 (위에서부터 우선). dict가 아닌 리스트로 순서 고정.
        # 예전 (파일|목록).*(현재|here|.) 패턴은 '.' 때문에 "파일 찾아줘"까지 잡혀
        # "숫자 … ls -la" 같은 깨진 명령이 나왔음 → 찾기/목록 분리.
        self.natural_patterns = [
            # "숫자 3을 포함한 파일 찾아줘" 등
            (
                r"숫자\s*(\d+)\s*을?\s*포함.*파일.*(찾아|찾기|검색)",
                lambda m: self._find_files_containing(m.group(1)),
            ),
            (
                r"[\"']([^\"']{1,128})[\"']\s*을?\s*포함.*파일.*(찾아|찾기|검색)",
                lambda m: self._find_files_containing(m.group(1)),
            ),
            (r"(큰|large).*(파일|file).*찾", "find . -type f -size +100M"),
            # 이름/글롭으로 파일 찾기 (내용 검색 아님)
            (r"(검색|search)\s*[\"']?([^\"'\s]+)[\"']?", r'find . -name "*\2*"'),
            # 목록: '찾아/검색'이 있으면 여기 오지 않도록 위에서 먼저 처리
            (
                r"(?!.*(?:찾아|검색))(?:(?:현재|이|여기)\s*(?:폴더|디렉터리)\s*)?(?:파일\s*목록|목록\s*보여|목록을?\s*보여|show\s+list|list\s+files)",
                "ls -la",
            ),
            (r"(현재|where).*(위치|디렉터리|directory)", "pwd"),
            (r"(디스크|용량|space).*(확인|check)", "df -h"),
            (r"(프로세스|process).*(목록|list)", "ps aux"),
            (r"(메모리|memory).*(사용량|usage)", "free -h"),
            (r'(폴더|디렉터리).*(만들|create).*"?([^"]+)"?', r'mkdir "\3"'),
            (r'(파일|file).*(삭제|delete|remove).*"?([^"]+)"?', r'rm "\3"'),
            (r'(이동|move|go).*(폴더|디렉터리|directory).*"?([^"]+)"?', r'cd "\3"'),
            (r'(복사|copy).*"?([^"]+)"?.*"?([^"]+)"?', r'cp "\2" "\3"'),
            (r"(도움말|help)", "help"),
            (r"(종료|exit|quit|나가)", "exit"),
            (r"(화면|clear|정리)", "clear"),
            (r"(히스토리|history|기록)", "history"),
        ]
    
    def print_welcome(self):
        """환영 메시지 출력"""
        sc = self.shell_context
        shell_line = (
            f"[dim]실행 환경 쉘(추정): [cyan]{sc['label']}[/cyan] "
            f"([italic]{sc['kind']}[/italic])[/dim]\n"
        )
        if sc.get("parent_exe"):
            shell_line += f"[dim]  부모 프로세스: {sc['parent_name']}[/dim]\n"
        welcome_panel = Panel.fit(
            "[bold blue]🤖 AOSH - AI Operating Shell[/bold blue]\n"
            "[green]자연어와 리눅스 명령어를 모두 사용할 수 있습니다![/green]\n\n"
            f"{shell_line}\n"
            "[yellow]예시:[/yellow]\n"
            "  • 파일 목록 보여줘 → ls -la\n"
            "  • 현재 위치 알려줘 → pwd\n"
            "  • 큰 파일들 찾아줘 → find . -size +100M\n"
            "  • ls -la (직접 명령어도 가능)\n\n"
            "[cyan]종료: exit, quit, 종료[/cyan]",
            title="🚀 Welcome to AOSH",
            title_align="center"
        )
        console.print(welcome_panel)
        print()

    def _find_files_containing(self, needle: str) -> str:
        """파일 '내용'에 문자열이 포함된 파일 찾기 (Windows: findstr, 그 외: grep)."""
        needle = (needle or "").strip()
        if not needle:
            return "echo 검색어가 비어 있습니다."
        if os.name == "nt":
            safe = needle.replace('"', '\\"')
            return f'findstr /s /m /i /c:"{safe}" *.*'
        return f"grep -rIl --fixed-strings {shlex.quote(needle)} ."
    
    def is_natural_language(self, text):
        """자연어인지 판단"""
        # 한글이 포함되어 있거나, 질문 형태이면 자연어로 판단
        has_korean = bool(re.search(r'[가-힣]', text))
        has_question = any(word in text.lower() for word in ['what', 'where', 'how', '어디', '뭐', '어떻게'])
        
        # 명확한 리눅스 명령어 패턴이면 명령어로 판단
        is_command = text.strip().split()[0] in ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep', 'find', 'ps', 'top', 'kill']
        
        return (has_korean or has_question) and not is_command
    
    def translate_natural_language(self, text):
        """자연어를 명령어로 변환"""
        text = text.strip()
        
        for pattern, command in self.natural_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            if callable(command):
                return command(match)
            if match.groups():
                try:
                    return re.sub(pattern, command, text, flags=re.IGNORECASE)
                except re.error:
                    return command
            return command
        
        return text
    
    def execute_command(self, command):
        """명령어 실행"""
        command = command.strip()
        
        if not command:
            return
        
        # 내장 명령어 처리
        if command in ['exit', 'quit', '종료']:
            console.print("[yellow]👋 AOSH를 종료합니다.[/yellow]")
            return False
        
        elif command == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        
        elif command == 'help':
            self.show_help()
            return True
        
        elif command == 'history':
            self.show_history()
            return True
        
        elif command.startswith('cd '):
            # cd 명령어 처리
            path = command[3:].strip().strip('"\'')
            try:
                if path == '..':
                    os.chdir('..')
                elif path == '~':
                    os.chdir(os.path.expanduser('~'))
                else:
                    os.chdir(path)
                self.current_dir = os.getcwd()
                console.print(f"[green]📁 {self.current_dir}[/green]")
            except FileNotFoundError:
                console.print(f"[red]❌ 디렉터리를 찾을 수 없습니다: {path}[/red]")
            except PermissionError:
                console.print(f"[red]❌ 권한이 없습니다: {path}[/red]")
            return True
        
        else:
            # 외부 명령어 실행
            try:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    cwd=self.current_dir
                )
                
                if result.stdout:
                    print(result.stdout.rstrip())
                
                if result.stderr:
                    console.print(f"[red]{result.stderr.rstrip()}[/red]")
                
                if result.returncode != 0:
                    console.print(f"[yellow]⚠️ 명령어가 오류 코드 {result.returncode}로 종료되었습니다.[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ 명령어 실행 오류: {e}[/red]")
        
        return True
    
    def show_help(self):
        """도움말 출력"""
        help_text = """
[bold blue]🤖 AOSH 도움말[/bold blue]

[yellow]자연어 명령어 예시:[/yellow]
  • 파일 목록 보여줘
  • 현재 위치 알려줘  
  • 큰 파일들 찾아줘
  • test 폴더 만들어줘
  • 프로세스 목록 보여줘
  • 메모리 사용량 확인해줘

[yellow]리눅스 명령어:[/yellow]
  • ls, cd, pwd, mkdir, rm, cp, mv
  • ps, top, find, grep, cat
  • 모든 일반적인 리눅스 명령어

[yellow]내장 명령어:[/yellow]
  • help - 도움말
  • history - 명령어 기록
  • clear - 화면 정리
  • exit, quit, 종료 - 쉘 종료
        """
        console.print(Panel(help_text, title="📚 Help", title_align="center"))
    
    def show_history(self):
        """명령어 기록 출력"""
        if not self.history:
            console.print("[yellow]명령어 기록이 없습니다.[/yellow]")
            return
        
        console.print("[bold blue]📜 명령어 기록:[/bold blue]")
        for i, cmd in enumerate(self.history[-10:], 1):  # 최근 10개만
            console.print(f"  {i:2d}. {cmd}")
    
    def get_prompt_text(self):
        """프롬프트 텍스트 생성"""
        current_dir = os.path.basename(self.current_dir) or self.current_dir
        return f"aosh:{current_dir}$ "
    
    def run(self):
        """메인 쉘 루프"""
        self.print_welcome()
        
        try:
            while True:
                try:
                    # 프롬프트 출력 및 입력 받기
                    user_input = prompt(
                        self.get_prompt_text(),
                        completer=self.command_completer
                    ).strip()
                    
                    if not user_input:
                        continue
                    
                    # 기록에 추가
                    self.history.append(user_input)
                    
                    # 자연어인지 확인
                    if self.is_natural_language(user_input):
                        console.print(f"[dim blue]🧠 자연어 감지: {user_input}[/dim blue]")
                        translated = self.translate_natural_language(user_input)
                        if translated != user_input:
                            console.print(f"[dim green]🔄 변환된 명령어: {translated}[/dim green]")
                            user_input = translated
                        else:
                            console.print(f"[dim yellow]⚠️ 자연어를 명령어로 변환할 수 없습니다. 직접 실행합니다.[/dim yellow]")
                    
                    # 명령어 실행
                    should_continue = self.execute_command(user_input)
                    if not should_continue:
                        break
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Ctrl+C 감지. 'exit'로 종료하세요.[/yellow]")
                    continue
                except EOFError:
                    console.print("\n[yellow]👋 AOSH를 종료합니다.[/yellow]")
                    break
                    
        except Exception as e:
            console.print(f"[red]❌ 쉘 오류: {e}[/red]")


def main():
    """메인 함수"""
    # 의존성 확인
    try:
        import prompt_toolkit
        import rich
    except ImportError as e:
        print(f"❌ 필수 라이브러리가 없습니다: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install prompt-toolkit rich")
        sys.exit(1)
    
    # AOSH 시작
    shell = AOSHShell()
    shell.run()


if __name__ == "__main__":
    main() 