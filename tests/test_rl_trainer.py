"""강화학습 훈련 루프 스모크 (torch 불필요)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shell.learning.rl_trainer import ReinforcementTrainer, run_training_from_config
from shell.utils.config import Config


def test_reinforcement_trainer_writes_jsonl(tmp_path: Path):
    c = Config()
    c.set("training.mode", "reinforcement")
    c.set("training.rl.trajectory_dir", str(tmp_path))
    c.set("training.rl.epochs", 1)
    c.set("training.rl.episodes_per_epoch", 2)

    code = ReinforcementTrainer(c).run()
    assert code == 0
    files = list(tmp_path.glob("rl_episodes_*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert "prompt" in row and "proposed_command" in row and "reward" in row


def test_run_training_from_config_reinforcement(tmp_path: Path):
    c = Config()
    c.set("training.mode", "reinforcement")
    c.set("training.rl.trajectory_dir", str(tmp_path))
    c.set("training.rl.epochs", 1)
    c.set("training.rl.episodes_per_epoch", 1)
    assert run_training_from_config(c) == 0
