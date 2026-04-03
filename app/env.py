import time
import random
from typing import Optional
from app.models import SystemState, Action, StepResult, ResetRequest, TaskInfo
from app.tasks.task_easy import SingleServiceDownTask
from app.tasks.task_medium import CascadingFailureTask
from app.tasks.task_hard import MemoryLeakTask

TASKS = {
    "single_service_down": SingleServiceDownTask,
    "cascading_failure":   CascadingFailureTask,
    "memory_leak":         MemoryLeakTask,
}


class IncidentResponseEnv:
    def __init__(self):
        self.current_task = None
        self.task_id: Optional[str] = None
        self.step_count: int = 0
        self.total_reward: float = 0.0
        self.start_time: Optional[float] = None
        self.done: bool = False

    def reset(self, task_id: Optional[str] = None) -> SystemState:
        if task_id is None:
            task_id = random.choice(list(TASKS.keys()))
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}. Valid: {list(TASKS.keys())}")
        self.task_id = task_id
        self.current_task = TASKS[task_id]()
        self.step_count = 0
        self.total_reward = 0.0
        self.start_time = time.time()
        self.done = False
        state = self.current_task.get_initial_state()
        state.total_reward = 0.0
        return state

    def step(self, action: Action) -> StepResult:
        if self.current_task is None:
            raise RuntimeError("Call /reset before /step")
        if self.done:
            raise RuntimeError("Episode done. Call /reset to start a new episode.")
        self.step_count += 1
        elapsed = int(time.time() - self.start_time)
        time_remaining = max(0, self.current_task.time_budget - elapsed)
        if time_remaining == 0:
            self.done = True
            state = self.current_task.get_state(self.step_count, 0)
            state.done = True
            state.total_reward = self.total_reward
            state.message = "Time budget exhausted. Incident not resolved."
            return StepResult(state=state, reward=0.0, done=True, info={"reason": "timeout"})
        reward, info = self.current_task.step(action, self.step_count, time_remaining)
        self.total_reward = round(self.total_reward + reward, 4)
        if self.current_task.is_solved() or self.step_count >= self.current_task.max_steps:
            self.done = True
        state = self.current_task.get_state(self.step_count, time_remaining)
        state.done = self.done
        state.reward = reward
        state.total_reward = self.total_reward
        state.step_count = self.step_count
        return StepResult(state=state, reward=reward, done=self.done, info=info)

    def get_state(self) -> SystemState:
        if self.current_task is None:
            raise RuntimeError("Call /reset first")
        elapsed = int(time.time() - self.start_time)
        time_remaining = max(0, self.current_task.time_budget - elapsed)
        state = self.current_task.get_state(self.step_count, time_remaining)
        state.total_reward = self.total_reward
        return state

    def list_tasks(self):
        return [
            TaskInfo(
                id=tid,
                difficulty=TASKS[tid].difficulty,
                description=TASKS[tid].description,
                max_steps=TASKS[tid].max_steps,
                time_budget=TASKS[tid].time_budget,
            )
            for tid in TASKS
        ]
