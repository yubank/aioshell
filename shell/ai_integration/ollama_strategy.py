"""
Ollama HTTP API를 통한 의도 분석 (로컬 HF 대신 설정으로 선택).

설정 예 (config.yaml 또는 .config):

  ai:
    provider: ollama
    ollama:
      base_url: http://127.0.0.1:11434
      model: llama3.2
      timeout: 120
"""

from __future__ import annotations

from typing import Dict, List

import httpx

from ..core.processors import CommandIntent
from ..utils.logging import get_logger
from .codellama_strategy import CodeLlamaStrategy
from .intent_patterns import default_intent_patterns
from .prompts import build_shell_intent_prompt


class OllamaStrategy(CodeLlamaStrategy):
    """Hugging Face 로드 없이 Ollama `/api/chat`으로 의도 분석."""

    def __init__(self, config):
        self.logger = get_logger(__name__)
        self.config = config
        ai = config.get("ai") or {}
        o = ai.get("ollama") or {}
        self.ollama_base = (o.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = o.get("model", "llama3.2")
        self.timeout = float(o.get("timeout", 120))
        self.initialized = False
        self.intent_patterns = default_intent_patterns()
        self.model_manager = None
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.model_path = None
        self.model_key = ai.get("model_key", "ollama")
        self.device = "ollama"
        self.max_length = int(ai.get("max_length", 512))
        self.temperature = float(ai.get("temperature", 0.1))

    async def initialize(self) -> None:
        if self.initialized:
            self.logger.warning("Ollama already initialized")
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.ollama_base}/api/tags")
                r.raise_for_status()
        except Exception as e:
            self.logger.error("Ollama 서버에 연결할 수 없습니다 (%s): %s", self.ollama_base, e)
            raise RuntimeError(
                f"Ollama가 실행 중인지 확인하세요: {self.ollama_base} (오류: {e})"
            ) from e
        self.initialized = True
        self.logger.info("Ollama 준비됨 model=%s base=%s", self.ollama_model, self.ollama_base)

    async def _analyze_with_model(self, user_input: str) -> CommandIntent:
        prompt = build_shell_intent_prompt(user_input)
        payload = {
            "model": self.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:

            async def _post():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.post(
                        f"{self.ollama_base}/api/chat",
                        json=payload,
                    )
                    r.raise_for_status()
                    return r.json()

            data = await _post()
        except Exception as e:
            self.logger.error("Ollama chat 실패: %s", e)
            return CommandIntent(
                intent_type="unknown",
                confidence=0.0,
                parameters={},
                raw_command=user_input,
            )

        msg = data.get("message") or {}
        text = (msg.get("content") or data.get("response") or "").strip()
        return self._parse_model_output(text, user_input)

    async def get_available_models(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.ollama_base}/api/tags")
                r.raise_for_status()
                data = r.json()
            models = data.get("models") or []
            return [{"name": m.get("name", ""), "source": "ollama"} for m in models]
        except Exception as e:
            self.logger.warning("Ollama 모델 목록 조회 실패: %s", e)
            return []

    async def get_downloaded_models(self) -> List[Dict]:
        return await self.get_available_models()

    async def download_specific_model(self, model_key: str, force_download: bool = False) -> str:
        self.logger.warning("Ollama는 pull을 ollama CLI로 실행하세요: ollama pull %s", model_key)
        return model_key

    async def delete_model(self, model_key: str) -> bool:
        self.logger.warning("Ollama 모델 삭제는 ollama CLI를 사용하세요.")
        return False

    def get_recommended_model(self) -> str:
        return self.ollama_model

    def cleanup(self) -> None:
        self.initialized = False
        self.logger.info("Ollama strategy 정리됨")
