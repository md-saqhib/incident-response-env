#!/usr/bin/env python3
"""Unit tests for inference agent reliability helpers."""

import importlib.util
from pathlib import Path

_INFERENCE_PATH = Path(__file__).parent / "inference.py"
_SPEC = importlib.util.spec_from_file_location("inference", _INFERENCE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load inference.py for tests")

inference = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inference)


def test_clamp_score_boundaries() -> None:
    assert inference.clamp_score(0.0) == 0.01
    assert inference.clamp_score(1.0) == 0.99
    assert inference.clamp_score(-4.2) == 0.01
    assert inference.clamp_score(9.7) == 0.99
    assert inference.clamp_score(0.55) == 0.55


def test_extract_json_object_with_code_fence() -> None:
    raw = """```json\n{\"action_type\":\"investigate\",\"target\":\"payment-service\",\"details\":\"\"}\n```"""
    parsed = inference._extract_json_object(raw)
    assert parsed["action_type"] == "investigate"
    assert parsed["target"] == "payment-service"


def test_extract_json_object_with_extra_text() -> None:
    raw = "Use this action: {\"action_type\":\"fix\",\"target\":\"analytics-service\",\"details\":\"rolling restart\"} thanks"
    parsed = inference._extract_json_object(raw)
    assert parsed["action_type"] == "fix"
    assert parsed["target"] == "analytics-service"


def test_normalize_action_valid() -> None:
    normalized = inference.normalize_action(
        {"action_type": "CHECK_METRICS", "target": "postgres-db", "details": None}
    )
    assert normalized == {
        "action_type": "check_metrics",
        "target": "postgres-db",
        "details": "None",
    }


def test_normalize_action_rejects_invalid_action_type() -> None:
    try:
        inference.normalize_action({"action_type": "delete", "target": "svc", "details": ""})
        assert False, "Expected ValueError for invalid action_type"
    except ValueError as exc:
        assert "invalid action_type" in str(exc)


def test_fallback_action_for_all_tasks() -> None:
    easy = inference.fallback_action_for_state({"task_id": "single_service_down"}, 1)
    med = inference.fallback_action_for_state({"task_id": "cascading_failure"}, 3)
    hard = inference.fallback_action_for_state({"task_id": "memory_leak"}, 4)

    assert easy["action_type"] == "check_metrics"
    assert easy["target"] == "payment-service"

    assert med["action_type"] == "diagnose"
    assert med["target"] == "postgres-db"

    assert hard["action_type"] == "fix"
    assert hard["target"] == "analytics-service"


def test_fallback_action_unknown_task() -> None:
    action = inference.fallback_action_for_state({"task_id": "unknown"}, 1)
    assert action["action_type"] == "escalate"
    assert action["target"] == "oncall"
