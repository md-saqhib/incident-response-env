#!/usr/bin/env python3
"""Pytest suite for FastAPI endpoints."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.main import app  # type: ignore[reportMissingImports]


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200

    payload = response.json()
    assert payload["name"] == "IncidentResponseEnv"
    assert payload["version"] == "1.0.0"
    assert "/reset" in payload["endpoints"]
    assert "/step" in payload["endpoints"]


def test_tasks_endpoint_contract() -> None:
    response = client.get("/tasks")
    assert response.status_code == 200

    tasks = response.json()
    task_ids = {t["id"] for t in tasks}
    assert {"single_service_down", "cascading_failure", "memory_leak"}.issubset(task_ids)

    for task in tasks:
        assert "difficulty" in task
        assert "max_steps" in task
        assert "time_budget" in task


def test_reset_then_step_then_state_flow() -> None:
    reset_response = client.post("/reset", json={"task_id": "single_service_down"})
    assert reset_response.status_code == 200

    state = reset_response.json()
    assert state["task_id"] == "single_service_down"
    assert state["task_difficulty"] == "easy"
    assert "payment-service" in state["services"]

    step_response = client.post(
        "/step",
        json={"action_type": "investigate", "target": "payment-service", "details": ""},
    )
    assert step_response.status_code == 200

    result = step_response.json()
    assert "reward" in result
    assert "state" in result
    assert "info" in result
    assert isinstance(result["reward"], (int, float))
    assert "feedback" in result["info"]

    current_state_response = client.get("/state")
    assert current_state_response.status_code == 200
    current_state = current_state_response.json()
    assert current_state["step_count"] >= 1


def test_reset_invalid_task_returns_400() -> None:
    response = client.post("/reset", json={"task_id": "not-a-real-task"})
    assert response.status_code == 400
    assert "Unknown task_id" in response.json()["detail"]
