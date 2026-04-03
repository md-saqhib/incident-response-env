"""
EASY TASK: Single Service Down
Scenario: payment-service is OOM and throwing 500s.
Root cause: payment-service OutOfMemoryError.
Fix: restart payment-service.
"""
from datetime import datetime, timedelta
import random
from typing import Tuple, Dict, Any
from app.models import Action, SystemState, Alert, Metric, LogEntry, Severity
from app.tasks.base import BaseTask


class SingleServiceDownTask(BaseTask):
    difficulty = "easy"
    description = "A single microservice is down. Investigate alerts and logs to identify and fix it."
    max_steps = 10
    time_budget = 300

    def _setup(self):
        now = datetime.utcnow()
        self.services_status = {
            "api-gateway": "degraded",
            "payment-service": "down",
            "user-service": "healthy",
            "notification-service": "healthy",
        }
        self.alerts = [
            Alert(
                id="ALT-001",
                severity=Severity.CRITICAL,
                service="payment-service",
                message="payment-service is returning HTTP 500 on all endpoints. Error rate: 100%.",
                timestamp=(now - timedelta(minutes=5)).isoformat(),
            ),
            Alert(
                id="ALT-002",
                severity=Severity.WARNING,
                service="api-gateway",
                message="api-gateway experiencing 502 Bad Gateway errors upstream to payment-service.",
                timestamp=(now - timedelta(minutes=4)).isoformat(),
            ),
        ]
        self.metrics = [
            Metric(service="api-gateway",        cpu_percent=45.0, memory_percent=52.0, error_rate=38.0, latency_ms=2400.0, timestamp=now.isoformat()),
            Metric(service="payment-service",    cpu_percent=12.0, memory_percent=98.6, error_rate=100.0, latency_ms=0.0,   timestamp=now.isoformat()),
            Metric(service="user-service",       cpu_percent=22.0, memory_percent=41.0, error_rate=0.2,  latency_ms=120.0,  timestamp=now.isoformat()),
            Metric(service="notification-service",cpu_percent=8.0, memory_percent=30.0, error_rate=0.0,  latency_ms=80.0,   timestamp=now.isoformat()),
        ]
        self.base_logs = [
            LogEntry(timestamp=(now - timedelta(minutes=6)).isoformat(), level="INFO",  service="payment-service",    message="Processing payment batch job started."),
            LogEntry(timestamp=(now - timedelta(minutes=5, seconds=45)).isoformat(), level="WARN",  service="payment-service", message="Heap usage at 87%. GC pressure increasing."),
            LogEntry(timestamp=(now - timedelta(minutes=5, seconds=30)).isoformat(), level="ERROR", service="payment-service", message="java.lang.OutOfMemoryError: Java heap space. Killing process."),
            LogEntry(timestamp=(now - timedelta(minutes=5, seconds=20)).isoformat(), level="ERROR", service="api-gateway",     message="502 Bad Gateway: upstream connection refused from payment-service:8080."),
            LogEntry(timestamp=(now - timedelta(minutes=5, seconds=10)).isoformat(), level="ERROR", service="api-gateway",     message="All retries exhausted for payment-service. Returning 502 to clients."),
        ]
        self.detailed_logs = {
            "payment-service": [
                LogEntry(timestamp=(now - timedelta(minutes=7)).isoformat(), level="INFO",  service="payment-service", message="Application started. Heap size: 512MB."),
                LogEntry(timestamp=(now - timedelta(minutes=6)).isoformat(), level="INFO",  service="payment-service", message="Batch job started: processing 50,000 payment records."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=50)).isoformat(), level="WARN",  service="payment-service", message="Heap usage 87% (445MB / 512MB). Full GC triggered."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=40)).isoformat(), level="WARN",  service="payment-service", message="Full GC unable to free sufficient memory. Heap still at 91%."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=30)).isoformat(), level="ERROR", service="payment-service", message="java.lang.OutOfMemoryError: Java heap space"),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=29)).isoformat(), level="ERROR", service="payment-service", message="Heap dump written to /tmp/payment-heapdump-20260403.hprof"),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=28)).isoformat(), level="ERROR", service="payment-service", message="JVM process terminated abnormally. Exit code: 1."),
            ],
            "api-gateway": [
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=25)).isoformat(), level="WARN",  service="api-gateway", message="Upstream health check failed for payment-service (attempt 1/3)."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=20)).isoformat(), level="WARN",  service="api-gateway", message="Upstream health check failed for payment-service (attempt 2/3)."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=15)).isoformat(), level="ERROR", service="api-gateway", message="Upstream health check failed for payment-service (attempt 3/3). Marking as DOWN."),
                LogEntry(timestamp=(now - timedelta(minutes=5, seconds=10)).isoformat(), level="ERROR", service="api-gateway", message="502 Bad Gateway returned to client for /api/payments endpoint."),
            ],
        }

    def get_initial_state(self) -> SystemState:
        return self.get_state(0, self.time_budget)

    def get_state(self, step_count: int, time_remaining: int) -> SystemState:
        logs = list(self.base_logs)
        for svc_logs in self.revealed_logs.values():
            logs.extend(svc_logs)
        logs.sort(key=lambda x: x.timestamp)
        return SystemState(
            task_id="single_service_down",
            task_difficulty=self.difficulty,
            step_count=step_count,
            max_steps=self.max_steps,
            time_budget=self.time_budget,
            time_remaining=time_remaining,
            alerts=self.alerts,
            metrics=self.metrics,
            recent_logs=logs[-10:],
            services=self.services_status,
            done=self.solved,
            reward=0.0,
            total_reward=0.0,
            message="Incident active. Investigate and fix the root cause." if not self.solved else "Incident resolved!",
        )

    def step(self, action: Action, step_count: int, time_remaining: int) -> Tuple[float, Dict[str, Any]]:
        self.total_actions += 1
        act = action.action_type.value
        target = action.target.lower().strip()
        details = (action.details or "").lower().strip()
        reward = 0.0
        info = {"action": act, "target": target, "feedback": ""}

        if act == "investigate":
            if target in self.detailed_logs:
                self.revealed_logs[target] = self.detailed_logs[target]
                reward = 0.02
                info["feedback"] = f"Retrieved {len(self.detailed_logs[target])} detailed log entries for {target}."
            else:
                reward = -0.02
                self.wrong_actions += 1
                info["feedback"] = f"No detailed logs found for {target}. Try a different service."

        elif act == "check_metrics":
            matching = [m for m in self.metrics if m.service == target]
            if matching:
                m = matching[0]
                reward = 0.02
                info["feedback"] = f"{target} metrics: CPU={m.cpu_percent}% MEM={m.memory_percent}% ERR={m.error_rate}% LAT={m.latency_ms}ms"
            else:
                reward = -0.02
                self.wrong_actions += 1
                info["feedback"] = f"Service {target} not found."

        elif act == "diagnose":
            if not self.diagnosis_correct:
                if "payment" in target and ("memory" in details or "oom" in details or "heap" in details or "outofmemory" in details):
                    self.diagnosis_correct = True
                    reward = 0.40
                    info["feedback"] = "CORRECT DIAGNOSIS: payment-service is OOM. Heap exhausted during batch job. Proceeding to apply fix."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = f"WRONG DIAGNOSIS. Hint: check which service has 98% memory usage and ERROR-level logs."
            else:
                info["feedback"] = "Diagnosis already recorded. Apply the fix now."

        elif act == "fix":
            if not self.fix_applied:
                if "payment" in target and ("restart" in details or "kill" in details or "redeploy" in details):
                    if self.diagnosis_correct:
                        self.fix_applied = True
                        self.solved = True
                        self.services_status["payment-service"] = "healthy"
                        self.services_status["api-gateway"] = "healthy"
                        reward = self._step_reward(time_remaining)
                        info["feedback"] = "SUCCESS: payment-service restarted. Memory cleared. Service back to healthy. API gateway recovering."
                    else:
                        reward = -0.05
                        info["feedback"] = "Fix attempted but diagnosis not confirmed yet. Diagnose first."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = f"WRONG FIX. Hint: which service is actually down and what fix resolves OOM?"
            else:
                info["feedback"] = "Incident already resolved."

        elif act == "escalate":
            reward = -0.05
            self.solved = True
            info["feedback"] = "Escalated to on-call engineer. Episode ended."

        return round(reward, 4), info
