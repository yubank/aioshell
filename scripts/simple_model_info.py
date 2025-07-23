#!/usr/bin/env python3
"""
간단한 모델 정보 도구

의존성 없이 CodeLlama 모델 정보를 표시합니다.
"""

import sys
import shutil
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_system_info():
    """기본 시스템 정보 수집"""
    import platform
    import os
    
    info = {
        "OS": platform.system(),
        "Architecture": platform.machine(),
        "Python": platform.python_version(),
    }
    
    # GPU 정보 (torch 없이)
    if shutil.which("nvidia-smi"):
        info["GPU"] = "NVIDIA GPU 감지됨"
    else:
        info["GPU"] = "GPU 없음 또는 감지 안됨"
    
    # 메모리 정보 (psutil 없이)
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal:' in line:
                    total_kb = int(line.split()[1])
                    total_gb = total_kb / 1024 / 1024
                    info["Total RAM"] = f"{total_gb:.1f} GB"
                    break
    except (FileNotFoundError, PermissionError):
        info["Total RAM"] = "알 수 없음"
    
    # 디스크 공간
    total, used, free = shutil.disk_usage(project_root)
    free_gb = free / (1024**3)
    info["Available Disk"] = f"{free_gb:.1f} GB"
    
    return info

def get_supported_models():
    """지원하는 모델 목록"""
    return {
        "codellama-7b": {
            "name": "CodeLlama-7b-Instruct-hf",
            "size": "7B",
            "description": "CodeLlama 7B Instruct 모델 (권장)",
            "memory_requirement": "16GB",
            "download_size": "13GB"
        },
        "codellama-13b": {
            "name": "CodeLlama-13b-Instruct-hf", 
            "size": "13B",
            "description": "CodeLlama 13B Instruct 모델 (고성능)",
            "memory_requirement": "32GB",
            "download_size": "25GB"
        },
        "codellama-34b": {
            "name": "CodeLlama-34b-Instruct-hf",
            "size": "34B", 
            "description": "CodeLlama 34B Instruct 모델 (최고성능)",
            "memory_requirement": "64GB",
            "download_size": "65GB"
        }
    }

def get_recommended_model(system_info):
    """시스템 정보 기반 권장 모델"""
    if "NVIDIA GPU" in system_info.get("GPU", ""):
        if "Total RAM" in system_info:
            try:
                ram_str = system_info["Total RAM"]
                ram_gb = float(ram_str.split()[0])
                
                if ram_gb >= 64:
                    return "codellama-13b"  # GPU 있으면 13B 시도
                elif ram_gb >= 32:
                    return "codellama-13b"
                else:
                    return "codellama-7b"
            except:
                pass
    
    return "codellama-7b"  # 기본 권장

def check_downloaded_models():
    """다운로드된 모델 확인"""
    models_dir = project_root / "models"
    downloaded = []
    
    if models_dir.exists():
        for model_dir in models_dir.iterdir():
            if model_dir.is_dir() and model_dir.name.startswith("codellama"):
                # 기본 파일들 확인
                required_files = ["config.json", "tokenizer.json"]
                has_files = all((model_dir / f).exists() for f in required_files)
                
                if has_files:
                    downloaded.append({
                        "key": model_dir.name,
                        "path": str(model_dir),
                        "size": get_directory_size(model_dir)
                    })
    
    return downloaded

def get_directory_size(path):
    """디렉토리 크기 계산"""
    try:
        total = 0
        for file_path in Path(path).rglob('*'):
            if file_path.is_file():
                total += file_path.stat().st_size
        return f"{total / (1024**3):.1f} GB"
    except:
        return "알 수 없음"

def main():
    print("🤖 AI Operating Shell - 모델 정보")
    print("=" * 50)
    
    # 시스템 정보
    print("\n📊 시스템 정보:")
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    
    # 권장 모델
    recommended = get_recommended_model(system_info)
    print(f"\n🎯 권장 모델: {recommended}")
    
    # 지원 모델 목록
    print("\n📋 지원하는 모델:")
    models = get_supported_models()
    for key, info in models.items():
        status = "✓ 권장" if key == recommended else ""
        print(f"  {key}: {info['description']} {status}")
        print(f"    크기: {info['size']}, 메모리: {info['memory_requirement']}, 다운로드: {info['download_size']}")
    
    # 다운로드된 모델
    print("\n💾 다운로드된 모델:")
    downloaded = check_downloaded_models()
    if downloaded:
        for model in downloaded:
            print(f"  ✓ {model['key']} ({model['size']})")
            print(f"    위치: {model['path']}")
    else:
        print("  없음 - 첫 실행 시 자동으로 다운로드됩니다.")
    
    print("\n💡 사용법:")
    print("  python scripts/start.py  # AI Shell 시작 (자동 모델 다운로드)")
    print("  python -m pip install -r requirements.txt  # 전체 의존성 설치")

if __name__ == "__main__":
    main() 