"""
강화학습 모드 훈련 진입점.

- 궤적(JSONL): 프롬프트 → 제안 명령 → 보상 (후속 TRL/PPO·DPO 연동용)
- 온디바이스 전체 미세조정은 transformers+trl+GPU가 필요하며 선택 사항입니다.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..utils.config import Config
from ..utils.logging import get_logger


class TrainingMode(str, Enum):
    NONE = "none"
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    PREFERENCE = "preference"


@dataclass
class RLStep:
    """한 스텝 궤적 (저장·분석용)."""

    prompt: str
    proposed_command: str
    reward: float
    done: bool
    meta: Dict[str, Any]


def _default_prompts() -> List[str]:
    return [
        "현재 폴더 파일 목록 보여줘",
        "디스크 용량 확인해줘",
        "list files in current folder",
        "프로세스 목록 보여줘",
    ]


def _heuristic_reward(command: str) -> float:
    """데모용 보상: 안전해 보이는 짧은 쉘 명령에 가산."""
    c = (command or "").strip().lower()
    if not c:
        return -1.0
    risky = ("rm -rf", "format", "fdisk", "mkfs", "del /s", "shutdown")
    if any(x in c for x in risky):
        return -2.0
    if len(c) > 500:
        return -0.5
    safeish = ("ls", "dir", "pwd", "echo", "find", "grep", "df", "du", "ps", "git ")
    if any(c.startswith(p) or f" {p}" in c for p in safeish):
        return 1.0
    return 0.2


def _placeholder_policy(prompt: str) -> str:
    """모델 없이 데모용으로 고정 매핑(실제로는 LLM 샘플링 자리)."""
    p = prompt.lower()
    if "목록" in prompt or "list" in p:
        return "ls -la" if random.random() > 0.3 else "ls"
    if "디스크" in prompt or "disk" in p:
        return "df -h"
    if "프로세스" in prompt or "process" in p:
        return "ps aux"
    return 'echo "noop"'


class ReinforcementTrainer:
    """강화학습 모드: 에피소드 루프 + 궤적 기록."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.rl = config.get("training.rl", {}) or {}
        self.training = config.get("training", {}) or {}

    def run(
        self,
        policy_fn: Optional[Callable[[str], str]] = None,
    ) -> int:
        epochs = int(self.rl.get("epochs", 1))
        episodes_per_epoch = int(self.rl.get("episodes_per_epoch", 4))
        traj_dir = Path(self.rl.get("trajectory_dir", "data/rl_trajectories"))
        traj_dir.mkdir(parents=True, exist_ok=True)

        prompts: List[str] = list(self.rl.get("prompts") or _default_prompts())
        policy = policy_fn or _placeholder_policy

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_file = traj_dir / f"rl_episodes_{ts}.jsonl"

        total_reward = 0.0
        n_steps = 0

        self.logger.info(
            "RL 훈련 시작 mode=%s epochs=%s episodes/epoch=%s out=%s",
            self.training.get("mode", TrainingMode.REINFORCEMENT.value),
            epochs,
            episodes_per_epoch,
            out_file,
        )

        with out_file.open("w", encoding="utf-8") as f:
            for ep in range(epochs):
                for _ in range(episodes_per_epoch):
                    prompt = random.choice(prompts)
                    cmd = policy(prompt)
                    r = float(self.rl.get("reward_success", 1.0)) * _heuristic_reward(cmd)
                    step = RLStep(
                        prompt=prompt,
                        proposed_command=cmd,
                        reward=r,
                        done=True,
                        meta={"epoch": ep, "algorithm": self.rl.get("algorithm", "ppo_placeholder")},
                    )
                    f.write(json.dumps(asdict(step), ensure_ascii=False) + "\n")
                    total_reward += r
                    n_steps += 1

        meta_path = traj_dir / f"rl_run_{ts}.json"
        meta_path.write_text(
            json.dumps(
                {
                    "epochs": epochs,
                    "episodes_per_epoch": episodes_per_epoch,
                    "total_steps": n_steps,
                    "mean_reward": total_reward / max(n_steps, 1),
                    "trajectory_file": str(out_file),
                    "note": "Placeholder RL loop. Plug TRL/PPO or your reward model on this JSONL.",
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.logger.info(
            "RL 훈련 완료 steps=%s mean_reward=%.4f meta=%s",
            n_steps,
            total_reward / max(n_steps, 1),
            meta_path,
        )
        return 0


class SupervisedTrainerStub:
    """자리 표시자: 실제 SFT는 별도 스크립트(예: transformers Trainer)로 두는 것을 권장."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)

    def run(self) -> int:
        self.logger.warning(
            "supervised 모드는 아직 내장 SFT 루프가 없습니다. "
            "datasets + transformers Trainer 또는 외부 스크립트를 사용하세요."
        )
        return 1


def run_training_from_config(config: Config) -> int:
    """training.mode에 따라 분기."""
    mode = (config.get("training.mode") or TrainingMode.NONE.value).lower()
    if mode == TrainingMode.SUPERVISED.value:
        return SupervisedTrainerStub(config).run()
    if mode == TrainingMode.REINFORCEMENT.value:
        return ReinforcementTrainer(config).run()
    if mode == TrainingMode.PREFERENCE.value:
        get_logger(__name__).warning("preference(DPO 등) 모드는 아직 스텁입니다.")
        return 1
    get_logger(__name__).error("알 수 없는 training.mode: %s", mode)
    return 2
