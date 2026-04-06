"""
학습·강화학습 관련 모듈.

실제 대규모 PPO/GRPO 등은 TRL·전용 GPU 환경이 필요하며,
여기서는 설정·궤적·보상 루프와 확장 훅을 제공합니다.
"""

from .rl_trainer import ReinforcementTrainer, TrainingMode, run_training_from_config

__all__ = [
    "ReinforcementTrainer",
    "TrainingMode",
    "run_training_from_config",
]
