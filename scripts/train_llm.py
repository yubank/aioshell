#!/usr/bin/env python3
"""
LLM 학습 진입점 (강화학습 모드 등).

  python scripts/train_llm.py --mode reinforcement --epochs 3
  python scripts/train_llm.py --mode supervised   # 아직 스텁

환경 변수: TRAINING_MODE, RL_EPOCHS (config.py 매핑)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shell.learning.rl_trainer import run_training_from_config
from shell.utils.config import Config
from shell.utils.logging import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Shell — LLM 학습 (강화학습 옵션)")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="설정 파일 (YAML/JSON)",
    )
    parser.add_argument(
        "--mode",
        choices=["reinforcement", "supervised", "preference"],
        required=True,
        help="학습 종류 (강화학습이 필요할 때는 reinforcement)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="RL 에폭 수 (training.rl.epochs)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="에폭당 에피소드 수 (training.rl.episodes_per_epoch)",
    )
    args = parser.parse_args()

    config = Config(args.config)
    config.set("training.mode", args.mode)
    config.set("training.rl.enabled", True)
    if args.epochs is not None:
        config.set("training.rl.epochs", args.epochs)
    if args.episodes is not None:
        config.set("training.rl.episodes_per_epoch", args.episodes)

    setup_logging(config.get("logging", {}))
    code = run_training_from_config(config)
    sys.exit(code)


if __name__ == "__main__":
    main()
