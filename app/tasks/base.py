from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from app.models import Action, SystemState


class BaseTask(ABC):
    difficulty: str = "easy"
    description: str = ""
    max_steps: int = 10
    time_budget: int = 300  # seconds

    def __init__(self):
        self.solved = False
        self.diagnosis_correct = False
        self.fix_applied = False
        self.wrong_actions = 0
        self.total_actions = 0
        self.revealed_logs: Dict[str, list] = {}
        self._setup()

    @abstractmethod
    def _setup(self):
        """Generate synthetic scenario: alerts, logs, metrics, services."""
        pass

    @abstractmethod
    def get_initial_state(self) -> SystemState:
        pass

    @abstractmethod
    def get_state(self, step_count: int, time_remaining: int) -> SystemState:
        pass

    @abstractmethod
    def step(self, action: Action, step_count: int, time_remaining: int) -> Tuple[float, Dict[str, Any]]:
        pass

    def is_solved(self) -> bool:
        return self.solved

    def _step_reward(self, time_remaining: int) -> float:
        """Full reward only awarded once fix is applied."""
        reward = 0.0
        if self.diagnosis_correct:
            reward += 0.40
        if self.fix_applied:
            reward += 0.35
            reward += 0.15 * (time_remaining / self.time_budget)
            if self.total_actions > 0:
                efficiency = 1.0 - (self.wrong_actions / max(self.total_actions, 1))
                reward += 0.10 * max(efficiency, 0.0)
        return round(min(reward, 1.0), 4)
