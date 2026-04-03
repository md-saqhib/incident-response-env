"""
MEDIUM TASK: Cascading Failure
Scenario: PostgreSQL connection pool exhausted → API timeouts → order queue backup.
The trick: alerts show api-gateway and order-queue as symptomatic.
Root cause is postgres-db connection pool exhaustion.
Fix: scale postgres-db connection pool.
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from app.models import Action, SystemState, Alert, Metric, LogEntry, Severity
from app.tasks.base import BaseTask


class CascadingFailureTask(BaseTask):
    difficulty = "medium"
    description = "A cascading failure across multiple services. Find the true root cause, not just the symptoms."
    max_steps = 15
    time_budget = 300

    def _setup(self):
        now = datetime.utcnow()
        self.services_status = {
            "api-gateway":    "degraded",
            "postgres-db":    "degraded",
            "redis-cache":    "healthy",
            "order-service":  "degraded",
            "payment-service":"healthy",
        }
        self.alerts = [
            Alert(id="ALT-001", severity=Severity.WARNING,  service="api-gateway",   message="api-gateway P99 latency: 8200ms. SLO breach (threshold: 500ms).", timestamp=(now - timedelta(minutes=12)).isoformat()),
            Alert(id="ALT-002", severity=Severity.WARNING,  service="order-service", message="order-service request queue depth: 4200 (critical threshold: 1000).", timestamp=(now - timedelta(minutes=10)).isoformat()),
            Alert(id="ALT-003", severity=Severity.WARNING,  service="postgres-db",   message="postgres-db active connections: 98/100 (98% pool utilization).", timestamp=(now - timedelta(minutes=15)).isoformat()),
        ]
        self.metrics = [
            Metric(service="api-gateway",    cpu_percent=68.0,  memory_percent=55.0, error_rate=42.0, latency_ms=8200.0, timestamp=now.isoformat()),
            Metric(service="postgres-db",    cpu_percent=94.0,  memory_percent=78.0, error_rate=0.0,  latency_ms=4500.0, timestamp=now.isoformat()),
            Metric(service="redis-cache",    cpu_percent=12.0,  memory_percent=35.0, error_rate=0.0,  latency_ms=2.0,    timestamp=now.isoformat()),
            Metric(service="order-service",  cpu_percent=80.0,  memory_percent=62.0, error_rate=55.0, latency_ms=9100.0, timestamp=now.isoformat()),
            Metric(service="payment-service",cpu_percent=18.0,  memory_percent=40.0, error_rate=0.1,  latency_ms=95.0,   timestamp=now.isoformat()),
        ]
        self.base_logs = [
            LogEntry(timestamp=(now - timedelta(minutes=15)).isoformat(), level="WARN",  service="postgres-db",   message="Connection pool approaching limit: 90/100 connections active."),
            LogEntry(timestamp=(now - timedelta(minutes=14)).isoformat(), level="ERROR", service="postgres-db",   message="Connection pool exhausted: 100/100. New connection requests queuing."),
            LogEntry(timestamp=(now - timedelta(minutes=13)).isoformat(), level="ERROR", service="order-service", message="FATAL: could not connect to database: connection pool timeout after 30000ms."),
            LogEntry(timestamp=(now - timedelta(minutes=12)).isoformat(), level="ERROR", service="api-gateway",   message="Upstream timeout: order-service /api/orders failed after 8200ms."),
            LogEntry(timestamp=(now - timedelta(minutes=10)).isoformat(), level="ERROR", service="order-service", message="Request queue depth: 4200. Workers blocked waiting for DB connections."),
        ]
        self.detailed_logs = {
            "postgres-db": [
                LogEntry(timestamp=(now - timedelta(minutes=20)).isoformat(), level="INFO",  service="postgres-db", message="Routine connection pool stats: 45/100 connections active."),
                LogEntry(timestamp=(now - timedelta(minutes=16)).isoformat(), level="WARN",  service="postgres-db", message="Spike in connection requests from order-service (new deploy at 14:03 UTC)."),
                LogEntry(timestamp=(now - timedelta(minutes=15)).isoformat(), level="WARN",  service="postgres-db", message="Connection pool at 90/100. Throttling new requests."),
                LogEntry(timestamp=(now - timedelta(minutes=14, seconds=30)).isoformat(), level="ERROR", service="postgres-db", message="Connection pool FULL: 100/100. All new requests are queuing."),
                LogEntry(timestamp=(now - timedelta(minutes=14)).isoformat(), level="ERROR", service="postgres-db", message="Connection queue depth: 220. Average wait time: 28 seconds."),
                LogEntry(timestamp=(now - timedelta(minutes=13)).isoformat(), level="ERROR", service="postgres-db", message="Timeout: 48 queued connection requests timed out. Queries failing."),
            ],
            "api-gateway": [
                LogEntry(timestamp=(now - timedelta(minutes=13)).isoformat(), level="WARN",  service="api-gateway", message="order-service response time degrading: P50=2100ms P99=7800ms."),
                LogEntry(timestamp=(now - timedelta(minutes=12)).isoformat(), level="ERROR", service="api-gateway", message="Circuit breaker OPEN for order-service (error rate 55% > threshold 30%)."),
                LogEntry(timestamp=(now - timedelta(minutes=12)).isoformat(), level="ERROR", service="api-gateway", message="Returning 503 Service Unavailable for /api/orders endpoints."),
            ],
            "order-service": [
                LogEntry(timestamp=(now - timedelta(minutes=14)).isoformat(), level="ERROR", service="order-service", message="DB connection timeout: could not acquire connection from pool in 30s."),
                LogEntry(timestamp=(now - timedelta(minutes=13)).isoformat(), level="ERROR", service="order-service", message="Worker thread pool saturated: all 200 workers waiting for DB connections."),
                LogEntry(timestamp=(now - timedelta(minutes=11)).isoformat(), level="ERROR", service="order-service", message="Request queue depth 4200 and growing. Memory pressure from queued requests."),
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
            task_id="cascading_failure",
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
            message="Multiple services degraded. Find the root cause — it may not be obvious from alerts alone.",
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
                info["feedback"] = f"No detailed logs for {target}."

        elif act == "check_metrics":
            matching = [m for m in self.metrics if m.service == target]
            if matching:
                m = matching[0]
                reward = 0.02
                info["feedback"] = f"{target}: CPU={m.cpu_percent}% MEM={m.memory_percent}% ERR={m.error_rate}% LAT={m.latency_ms}ms"
            else:
                self.wrong_actions += 1
                reward = -0.02
                info["feedback"] = f"Service {target} not found."

        elif act == "diagnose":
            if not self.diagnosis_correct:
                is_correct = (
                    "postgres" in target and
                    ("connection" in details or "pool" in details or "db" in details or "database" in details or "exhausted" in details)
                )
                if is_correct:
                    self.diagnosis_correct = True
                    reward = 0.40
                    info["feedback"] = "CORRECT DIAGNOSIS: postgres-db connection pool is exhausted. The cascade: DB full → order-service timeouts → queue backup → api-gateway degraded. The api-gateway and order-service alerts are symptoms, not causes."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = "WRONG DIAGNOSIS. Hint: api-gateway and order-service are symptoms. What are they all waiting for? Check postgres-db logs carefully."
            else:
                info["feedback"] = "Diagnosis confirmed. Apply the fix."

        elif act == "fix":
            if not self.fix_applied:
                is_correct = (
                    "postgres" in target and
                    any(k in details for k in ["connection", "pool", "scale", "increase", "restart", "pgbouncer", "config"])
                )
                if is_correct:
                    if self.diagnosis_correct:
                        self.fix_applied = True
                        self.solved = True
                        self.services_status["postgres-db"] = "healthy"
                        self.services_status["api-gateway"] = "healthy"
                        self.services_status["order-service"] = "healthy"
                        reward = self._step_reward(time_remaining)
                        info["feedback"] = "SUCCESS: postgres-db connection pool scaled. Connections freed. order-service workers unblocked. API gateway recovering. Queue draining."
                    else:
                        reward = -0.05
                        info["feedback"] = "Diagnose the root cause first before applying fixes."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = "WRONG FIX. Restarting api-gateway or order-service will not solve a DB connection pool issue. Fix the source."
            else:
                info["feedback"] = "Incident resolved."

        elif act == "escalate":
            reward = -0.05
            self.solved = True
            info["feedback"] = "Escalated to on-call. Episode ended."

        return round(reward, 4), info
