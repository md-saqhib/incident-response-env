#!/usr/bin/env python3
"""Pytest suite for IncidentResponseEnv core behavior."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.env import IncidentResponseEnv  # type: ignore[reportMissingImports]
from app.models import Action, ActionType  # type: ignore[reportMissingImports]


@pytest.fixture
def env() -> IncidentResponseEnv:
    return IncidentResponseEnv()


def test_reset_known_task(env: IncidentResponseEnv) -> None:
    state = env.reset("single_service_down")
    assert state.task_id == "single_service_down"
    assert state.task_difficulty == "easy"
    assert state.max_steps == 10
    assert state.time_budget == 300
    assert "payment-service" in state.services
    assert len(state.alerts) > 0


def test_reset_unknown_task_raises(env: IncidentResponseEnv) -> None:
    with pytest.raises(ValueError, match="Unknown task_id"):
        env.reset("unknown-task")


def test_step_updates_state_and_reward(env: IncidentResponseEnv) -> None:
    env.reset("single_service_down")
    result = env.step(Action(action_type=ActionType.CHECK_METRICS, target="payment-service", details=""))

    assert isinstance(result.reward, float)
    assert result.state.step_count == 1
    assert result.state.total_reward == pytest.approx(result.reward, abs=1e-4)
    assert "feedback" in result.info


def test_get_state_requires_reset(env: IncidentResponseEnv) -> None:
    with pytest.raises(RuntimeError, match="Call /reset first"):
        env.get_state()


def test_step_requires_reset(env: IncidentResponseEnv) -> None:
    with pytest.raises(RuntimeError, match="Call /reset before /step"):
        env.step(Action(action_type=ActionType.ESCALATE, target="oncall", details=""))


def test_list_tasks_contains_expected_ids(env: IncidentResponseEnv) -> None:
    tasks = env.list_tasks()
    task_ids = {t.id for t in tasks}
    assert task_ids == {"single_service_down", "cascading_failure", "memory_leak"}
