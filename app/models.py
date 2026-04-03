from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ActionType(str, Enum):
    INVESTIGATE = "investigate"
    DIAGNOSE = "diagnose"
    FIX = "fix"
    CHECK_METRICS = "check_metrics"
    ESCALATE = "escalate"


class Alert(BaseModel):
    id: str
    severity: Severity
    service: str
    message: str
    timestamp: str


class Metric(BaseModel):
    service: str
    cpu_percent: float
    memory_percent: float
    error_rate: float
    latency_ms: float
    timestamp: str


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


class SystemState(BaseModel):
    task_id: str
    task_difficulty: str
    step_count: int
    max_steps: int
    time_budget: int
    time_remaining: int
    alerts: List[Alert]
    metrics: List[Metric]
    recent_logs: List[LogEntry]
    services: Dict[str, str]
    done: bool
    reward: float
    total_reward: float
    message: str


class Action(BaseModel):
    action_type: ActionType
    target: str
    details: Optional[str] = ""


class StepResult(BaseModel):
    state: SystemState
    reward: float
    done: bool
    info: Dict[str, Any]


class ResetRequest(BaseModel):
    task_id: Optional[str] = None


class TaskInfo(BaseModel):
    id: str
    difficulty: str
    description: str
    max_steps: int
    time_budget: int
