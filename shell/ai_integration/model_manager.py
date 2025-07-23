"""
CodeLlama 모델 다운로드 및 관리 시스템

Hugging Face에서 CodeLlama 모델을 자동으로 다운로드하고
캐시, 버전 관리, 오프라인 지원 등을 제공합니다.
"""

import os
import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# 선택적 import
try:
    from huggingface_hub import snapshot_download, hf_hub_download, hf_hub_url
    from huggingface_hub.utils import HfHubHTTPError
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from ..utils.logging import get_logger


class ModelManager:
    """
    CodeLlama 모델 다운로드 및 관리 클래스
    
    주요 기능:
    - 모델 자동 다운로드
    - 캐시 관리
    - 버전 제어
    - 오프라인 지원
    """
    
    def __init__(self, models_dir: Optional[str] = None):
        self.logger = get_logger(__name__)
        
        # 의존성 확인
        if not HF_AVAILABLE:
            self.logger.warning("Hugging Face Hub not available. Model download will not work.")
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available. GPU checks will be disabled.")
        
        # 모델 저장 디렉토리 설정
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.models_dir = project_root / "models"
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 메타데이터 파일
        self.metadata_file = self.models_dir / "models_metadata.json"
        
        # 지원하는 CodeLlama 모델들
        self.supported_models = {
            "codellama-7b": {
                "name": "codellama/CodeLlama-7b-Instruct-hf",
                "size": "7B",
                "description": "CodeLlama 7B Instruct 모델 (권장)",
                "memory_requirement": "16GB",
                "download_size": "13GB"
            },
            "codellama-13b": {
                "name": "codellama/CodeLlama-13b-Instruct-hf", 
                "size": "13B",
                "description": "CodeLlama 13B Instruct 모델 (고성능)",
                "memory_requirement": "32GB",
                "download_size": "25GB"
            },
            "codellama-34b": {
                "name": "codellama/CodeLlama-34b-Instruct-hf",
                "size": "34B", 
                "description": "CodeLlama 34B Instruct 모델 (최고성능)",
                "memory_requirement": "64GB",
                "download_size": "65GB"
            }
        }
        
        self.logger.info(f"ModelManager initialized with models directory: {self.models_dir}")
    
    async def download_model(self, model_key: str = "codellama-7b", force_download: bool = False) -> str:
        """
        CodeLlama 모델 다운로드
        
        Args:
            model_key: 다운로드할 모델 키 (codellama-7b, codellama-13b, codellama-34b)
            force_download: 강제 재다운로드 여부
            
        Returns:
            str: 다운로드된 모델의 로컬 경로
        """
        if model_key not in self.supported_models:
            raise ValueError(f"Unsupported model: {model_key}. Supported: {list(self.supported_models.keys())}")
        
        model_info = self.supported_models[model_key]
        model_name = model_info["name"]
        local_path = self.models_dir / model_key
        
        # 이미 다운로드된 모델이 있는지 확인
        if not force_download and await self._is_model_downloaded(model_key):
            self.logger.info(f"Model {model_key} already downloaded at {local_path}")
            return str(local_path)
        
        try:
            self.logger.info(f"Starting download of {model_key} ({model_info['download_size']})")
            self.logger.info(f"Model: {model_name}")
            self.logger.info(f"This may take some time depending on your internet connection...")
            
            # 시스템 요구사항 확인
            await self._check_system_requirements(model_key)
            
            # 디스크 공간 확인
            await self._check_disk_space(model_key)
            
            # 인터넷 연결 확인
            await self._check_internet_connection()
            
            # 모델 다운로드 (비동기)
            await self._download_model_async(model_name, local_path)
            
            # 메타데이터 업데이트
            await self._update_metadata(model_key, local_path)
            
            # 다운로드 검증
            await self._verify_download(model_key)
            
            self.logger.info(f"Successfully downloaded {model_key} to {local_path}")
            return str(local_path)
            
        except Exception as e:
            self.logger.error(f"Failed to download model {model_key}: {e}")
            # 부분 다운로드 정리
            if local_path.exists():
                shutil.rmtree(local_path, ignore_errors=True)
            raise
    
    async def _download_model_async(self, model_name: str, local_path: Path) -> None:
        """비동기로 모델 다운로드"""
        
        def download_func():
            return snapshot_download(
                repo_id=model_name,
                local_dir=str(local_path),
                local_dir_use_symlinks=False,
                resume_download=True,
                ignore_patterns=["*.git*", "README.md", "*.msgpack", "*.h5"]
            )
        
        # 별도 스레드에서 다운로드 실행 (UI 블로킹 방지)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download_func)
    
    async def _check_system_requirements(self, model_key: str) -> None:
        """시스템 요구사항 확인"""
        model_info = self.supported_models[model_key]
        
        # GPU 메모리 확인
        if torch.cuda.is_available():
            total_memory = torch.cuda.get_device_properties(0).total_memory
            total_gb = total_memory / (1024**3)
            
            required_gb = int(model_info["memory_requirement"].replace("GB", ""))
            
            if total_gb < required_gb * 0.8:  # 80% 여유 공간 필요
                self.logger.warning(
                    f"GPU memory ({total_gb:.1f}GB) may be insufficient for {model_key} "
                    f"(requires {required_gb}GB). Consider using CPU or smaller model."
                )
        
        # RAM 확인 (대략적)
        try:
            import psutil
            available_ram = psutil.virtual_memory().available / (1024**3)
            required_gb = int(model_info["memory_requirement"].replace("GB", ""))
            
            if available_ram < required_gb:
                self.logger.warning(
                    f"Available RAM ({available_ram:.1f}GB) may be insufficient for {model_key}"
                )
        except ImportError:
            pass
    
    async def _check_disk_space(self, model_key: str) -> None:
        """디스크 공간 확인"""
        model_info = self.supported_models[model_key]
        required_gb = int(model_info["download_size"].replace("GB", ""))
        
        total, used, free = shutil.disk_usage(self.models_dir)
        free_gb = free / (1024**3)
        
        if free_gb < required_gb * 1.2:  # 20% 여유 공간 필요
            raise RuntimeError(
                f"Insufficient disk space. Required: {required_gb}GB, "
                f"Available: {free_gb:.1f}GB"
            )
    
    async def _check_internet_connection(self) -> None:
        """인터넷 연결 확인"""
        try:
            response = requests.get("https://huggingface.co", timeout=10)
            if response.status_code != 200:
                raise ConnectionError("Cannot reach Hugging Face")
        except Exception as e:
            raise ConnectionError(f"Internet connection required for model download: {e}")
    
    async def _is_model_downloaded(self, model_key: str) -> bool:
        """모델이 이미 다운로드되어 있는지 확인"""
        local_path = self.models_dir / model_key
        
        if not local_path.exists():
            return False
        
        # 필수 파일들 확인
        required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]
        for file_name in required_files:
            if not (local_path / file_name).exists():
                return False
        
        # 메타데이터 확인
        metadata = await self._load_metadata()
        return model_key in metadata.get("downloaded_models", {})
    
    async def _update_metadata(self, model_key: str, local_path: Path) -> None:
        """모델 메타데이터 업데이트"""
        metadata = await self._load_metadata()
        
        if "downloaded_models" not in metadata:
            metadata["downloaded_models"] = {}
        
        metadata["downloaded_models"][model_key] = {
            "local_path": str(local_path),
            "download_date": str(asyncio.get_event_loop().time()),
            "model_info": self.supported_models[model_key],
            "status": "downloaded"
        }
        
        await self._save_metadata(metadata)
    
    async def _load_metadata(self) -> Dict:
        """메타데이터 로드"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load metadata: {e}")
            return {}
    
    async def _save_metadata(self, metadata: Dict) -> None:
        """메타데이터 저장"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")
    
    async def _verify_download(self, model_key: str) -> None:
        """다운로드 검증"""
        local_path = self.models_dir / model_key
        
        # 기본 파일들 존재 확인
        required_files = [
            "config.json",
            "tokenizer.json", 
            "tokenizer_config.json"
        ]
        
        for file_name in required_files:
            file_path = local_path / file_name
            if not file_path.exists():
                raise RuntimeError(f"Download verification failed: {file_name} not found")
        
        # 모델 파일들 확인 (pytorch_model.bin 또는 safetensors)
        model_files = list(local_path.glob("*.bin")) + list(local_path.glob("*.safetensors"))
        if not model_files:
            raise RuntimeError("Download verification failed: No model files found")
        
        self.logger.info(f"Download verification passed for {model_key}")
    
    async def list_downloaded_models(self) -> List[Dict]:
        """다운로드된 모델 목록 반환"""
        metadata = await self._load_metadata()
        downloaded = metadata.get("downloaded_models", {})
        
        result = []
        for model_key, info in downloaded.items():
            result.append({
                "key": model_key,
                "path": info["local_path"],
                "size": info["model_info"]["size"],
                "description": info["model_info"]["description"],
                "download_date": info["download_date"],
                "status": info["status"]
            })
        
        return result
    
    async def delete_model(self, model_key: str) -> bool:
        """다운로드된 모델 삭제"""
        local_path = self.models_dir / model_key
        
        if not local_path.exists():
            self.logger.warning(f"Model {model_key} not found for deletion")
            return False
        
        try:
            shutil.rmtree(local_path)
            
            # 메타데이터에서 제거
            metadata = await self._load_metadata()
            if "downloaded_models" in metadata and model_key in metadata["downloaded_models"]:
                del metadata["downloaded_models"][model_key]
                await self._save_metadata(metadata)
            
            self.logger.info(f"Successfully deleted model {model_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete model {model_key}: {e}")
            return False
    
    async def get_model_path(self, model_key: str) -> Optional[str]:
        """모델의 로컬 경로 반환"""
        if not await self._is_model_downloaded(model_key):
            return None
        
        return str(self.models_dir / model_key)
    
    def get_recommended_model(self) -> str:
        """시스템 사양에 따른 권장 모델 반환"""
        # PyTorch가 있는 경우 GPU 메모리 기반 권장
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                total_memory = torch.cuda.get_device_properties(0).total_memory
                total_gb = total_memory / (1024**3)
                
                if total_gb >= 60:
                    return "codellama-34b"
                elif total_gb >= 24:
                    return "codellama-13b"
                else:
                    return "codellama-7b"
            except Exception:
                pass
        
        # CPU의 경우 또는 GPU 확인 실패 시 7B 모델 권장
        return "codellama-7b"
    
    def list_available_models(self) -> List[Dict]:
        """사용 가능한 모델 목록 반환"""
        result = []
        recommended = self.get_recommended_model()
        
        for key, info in self.supported_models.items():
            result.append({
                "key": key,
                "name": info["name"],
                "size": info["size"],
                "description": info["description"],
                "memory_requirement": info["memory_requirement"],
                "download_size": info["download_size"],
                "recommended": key == recommended
            })
        
        return result 