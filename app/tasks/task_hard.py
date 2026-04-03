"""
HARD TASK: Silent Memory Leak
Scenario: analytics-service has been slowly leaking memory for 6 hours.
No CRITICAL alert — just WARNING. Latency spikes are intermittent.
Root cause: analytics-service memory leak.
Fix: rolling restart analytics-service.
Agent must correlate memory trend + latency spikes to find the right service.
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from app.models import Action, SystemState, Alert, Metric, LogEntry, Severity
from app.tasks.base import BaseTask


class MemoryLeakTask(BaseTask):
    difficulty = "hard"
    description = "A silent memory leak is slowly degrading a service. No obvious CRITICAL alert. Correlate metrics and logs to find it."
    max_steps = 20
    time_budget = 300

    def _setup(self):
        now = datetime.utcnow()
        self.services_status = {
            "analytics-service": "degraded",
            "data-pipeline":     "healthy",
            "ml-service":        "healthy",
            "api-gateway":       "healthy",
            "redis-cache":       "healthy",
        }
        self.alerts = [
            Alert(id="ALT-001", severity=Severity.WARNING, service="analytics-service", message="analytics-service P99 latency intermittently spiking above 3000ms (normal: 200ms).", timestamp=(now - timedelta(hours=1)).isoformat()),
            Alert(id="ALT-002", severity=Severity.INFO,    service="analytics-service", message="analytics-service GC pause time increasing: avg 800ms (baseline: 50ms).", timestamp=(now - timedelta(minutes=30)).isoformat()),
        ]
        self.metrics = [
            Metric(service="analytics-service", cpu_percent=35.0, memory_percent=84.7, error_rate=2.1,  latency_ms=3200.0, timestamp=now.isoformat()),
            Metric(service="data-pipeline",     cpu_percent=42.0, memory_percent=48.0, error_rate=0.0,  latency_ms=150.0,  timestamp=now.isoformat()),
            Metric(service="ml-service",        cpu_percent=78.0, memory_percent=61.0, error_rate=0.5,  latency_ms=890.0,  timestamp=now.isoformat()),
            Metric(service="api-gateway",       cpu_percent=28.0, memory_percent=44.0, error_rate=0.8,  latency_ms=240.0,  timestamp=now.isoformat()),
            Metric(service="redis-cache",       cpu_percent=9.0,  memory_percent=22.0, error_rate=0.0,  latency_ms=1.5,    timestamp=now.isoformat()),
        ]
        # Memory trend data — key evidence
        self.memory_trend = {
            "analytics-service": [40.1, 45.3, 51.8, 58.2, 63.7, 69.1, 74.5, 79.8, 84.7],  # 6 hours, climbing
            "data-pipeline":     [47.2, 48.1, 47.9, 48.3, 48.0, 47.8, 48.2, 48.1, 48.0],  # stable
            "ml-service":        [60.1, 61.3, 60.8, 61.2, 60.9, 61.1, 61.3, 60.7, 61.0],  # stable
        }
        self.base_logs = [
            LogEntry(timestamp=(now - timedelta(hours=6)).isoformat(), level="INFO",  service="analytics-service", message="Application started. Heap: 2048MB allocated."),
            LogEntry(timestamp=(now - timedelta(hours=3)).isoformat(), level="INFO",  service="analytics-service", message="Processed 1.2M analytics events today. All nominal."),
            LogEntry(timestamp=(now - timedelta(hours=1)).isoformat(), level="WARN",  service="analytics-service", message="GC pause 820ms during analytics report generation. Latency spike observed."),
            LogEntry(timestamp=(now - timedelta(minutes=45)).isoformat(), level="WARN",  service="analytics-service", message="Heap utilization 79%. Full GC triggered but only freed 3% heap."),
            LogEntry(timestamp=(now - timedelta(minutes=20)).isoformat(), level="WARN",  service="analytics-service", message="GC pause 1100ms. P99 latency spike to 3200ms for 45 seconds."),
        ]
        self.detailed_logs = {
            "analytics-service": [
                LogEntry(timestamp=(now - timedelta(hours=6)).isoformat(), level="INFO",  service="analytics-service", message="JVM started. Heap: 2048MB max, 512MB initial. GC: G1GC."),
                LogEntry(timestamp=(now - timedelta(hours=5)).isoformat(), level="INFO",  service="analytics-service", message="Heap: 820MB / 2048MB (40%). Normal operation."),
                LogEntry(timestamp=(now - timedelta(hours=4)).isoformat(), level="INFO",  service="analytics-service", message="Heap: 1058MB / 2048MB (51.7%). Minor GC pause: 12ms."),
                LogEntry(timestamp=(now - timedelta(hours=3)).isoformat(), level="WARN",  service="analytics-service", message="Heap: 1302MB / 2048MB (63.6%). GC unable to reclaim significant space — possible leak."),
                LogEntry(timestamp=(now - timedelta(hours=2)).isoformat(), level="WARN",  service="analytics-service", message="Heap: 1537MB / 2048MB (75%). Live objects growing. Suspected unreleased cache references."),
                LogEntry(timestamp=(now - timedelta(hours=1)).isoformat(), level="WARN",  service="analytics-service", message="Heap: 1634MB / 2048MB (79.8%). Full GC triggered. Only 3% freed — objects held in static cache."),
                LogEntry(timestamp=(now - timedelta(minutes=30)).isoformat(), level="ERROR", service="analytics-service", message="Heap: 1734MB / 2048MB (84.7%). GC pause time: 1100ms. Service latency severely impacted."),
                LogEntry(timestamp=(now - timedelta(minutes=20)).isoformat(), level="ERROR", service="analytics-service", message="Memory leak suspected: AnalyticsReportCache holding 890MB of unreleased report objects."),
                LogEntry(timestamp=(now - timedelta(minutes=10)).isoformat(), level="ERROR", service="analytics-service", message="At current growth rate, OOM expected in ~35 minutes. Recommend rolling restart."),
            ],
            "data-pipeline": [
                LogEntry(timestamp=(now - timedelta(hours=2)).isoformat(), level="INFO", service="data-pipeline", message="Pipeline health check: all stages nominal. Throughput: 12k events/sec."),
                LogEntry(timestamp=(now - timedelta(hours=1)).isoformat(), level="INFO", service="data-pipeline", message="Memory stable at 48%. No anomalies detected."),
            ],
            "ml-service": [
                LogEntry(timestamp=(now - timedelta(hours=2)).isoformat(), level="INFO", service="ml-service", message="Model inference latency: avg 890ms. GPU utilization: 78%. Normal."),
                LogEntry(timestamp=(now - timedelta(hours=1)).isoformat(), level="INFO", service="ml-service", message="Memory stable at 61%. Routine checkpoint saved."),
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
            task_id="memory_leak",
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
            message="Intermittent latency spikes detected. No obvious CRITICAL alert. Investigate metrics trends carefully.",
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
                self.wrong_actions += 1
                reward = -0.02
                info["feedback"] = f"No detailed logs for {target}."

        elif act == "check_metrics":
            if target in self.memory_trend:
                trend = self.memory_trend[target]
                hours = list(range(-len(trend) + 1, 1))
                trend_str = ", ".join([f"{h}h:{v}%" for h, v in zip(hours, trend)])
                reward = 0.03
                matching = [m for m in self.metrics if m.service == target]
                if matching:
                    m = matching[0]
                    info["feedback"] = f"{target} current: CPU={m.cpu_percent}% MEM={m.memory_percent}% ERR={m.error_rate}% LAT={m.latency_ms}ms | Memory trend (6h): {trend_str}"
                else:
                    info["feedback"] = f"{target} memory trend (6h): {trend_str}"
            elif any(m.service == target for m in self.metrics):
                matching = [m for m in self.metrics if m.service == target]
                m = matching[0]
                reward = 0.02
                info["feedback"] = f"{target}: CPU={m.cpu_percent}% MEM={m.memory_percent}% ERR={m.error_rate}% LAT={m.latency_ms}ms (no trend data available)"
            else:
                self.wrong_actions += 1
                reward = -0.02
                info["feedback"] = f"Service {target} not found."

        elif act == "diagnose":
            if not self.diagnosis_correct:
                is_correct = (
                    "analytics" in target and
                    any(k in details for k in ["memory", "leak", "heap", "gc", "oom", "cache", "ram"])
                )
                if is_correct:
                    self.diagnosis_correct = True
                    reward = 0.40
                    info["feedback"] = "CORRECT DIAGNOSIS: analytics-service has a memory leak. AnalyticsReportCache is holding 890MB of unreleased objects. Memory has grown from 40% → 84.7% over 6 hours. OOM imminent in ~35 minutes."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = "WRONG DIAGNOSIS. Hint: Look at memory TRENDS over 6 hours, not just current snapshot. Which service shows continuous memory growth while others are stable?"
            else:
                info["feedback"] = "Diagnosis confirmed. Apply the fix."

        elif act == "fix":
            if not self.fix_applied:
                is_correct = (
                    "analytics" in target and
                    any(k in details for k in ["restart", "rolling", "redeploy", "kill", "recycle", "bounce"])
                )
                if is_correct:
                    if self.diagnosis_correct:
                        self.fix_applied = True
                        self.solved = True
                        self.services_status["analytics-service"] = "healthy"
                        reward = self._step_reward(time_remaining)
                        info["feedback"] = "SUCCESS: analytics-service rolling restart complete. Heap cleared from 84.7% → 41%. GC pauses normalised. Latency spikes resolved. Memory growth halted."
                    else:
                        reward = -0.05
                        info["feedback"] = "Diagnose the root cause before fixing."
                else:
                    self.wrong_actions += 1
                    reward = -0.10
                    info["feedback"] = "WRONG FIX. Hint: which specific service has the memory leak? And what fix resolves a memory leak?"
            else:
                info["feedback"] = "Incident resolved."

        elif act == "escalate":
            reward = -0.05
            self.solved = True
            info["feedback"] = "Escalated. Episode ended."

        return round(reward, 4), info
