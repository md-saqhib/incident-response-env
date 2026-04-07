#!/usr/bin/env python3
"""
inference.py — IncidentResponseEnv baseline agent
Logs follow the REQUIRED [START]/[STEP]/[END] format strictly.
All LLM calls use OpenAI client pointed at HuggingFace inference API.
"""
import os
import sys
import json
import time
import requests
from openai import OpenAI

# ── Required env vars (checklist compliance) ───────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1/")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")      # NO default — must be injected at runtime

# Optional: for from_docker_image() usage
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")

# ── OpenAI client pointing at HuggingFace ─────────────────────────────────
client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

TASKS = ["single_service_down", "cascading_failure", "memory_leak"]

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) responding to production incidents.
You receive system state: alerts, logs, metrics, and service statuses.
Your goal: diagnose the root cause and apply the correct fix efficiently.

Available actions (respond ONLY with valid JSON — no explanation, no markdown backticks):
- investigate: {"action_type": "investigate", "target": "<service_name>", "details": ""}
- check_metrics: {"action_type": "check_metrics", "target": "<service_name>", "details": ""}
- diagnose: {"action_type": "diagnose", "target": "<service_name>", "details": "<root_cause_description>"}
- fix: {"action_type": "fix", "target": "<service_name>", "details": "<fix_action_description>"}
- escalate: {"action_type": "escalate", "target": "oncall", "details": "<reason>"}

Strategy:
1. Check metrics for all services showing high error rates or latency.
2. Investigate logs for services with anomalies.
3. Identify root cause (not just symptoms).
4. Apply the appropriate fix.
"""


def state_to_prompt(state: dict) -> str:
    lines = [
        "=== PRODUCTION INCIDENT ===",
        f"Task: {state['task_id']} | Difficulty: {state['task_difficulty']}",
        f"Step: {state['step_count']}/{state['max_steps']} | Time remaining: {state['time_remaining']}s",
        f"Current total reward: {state.get('total_reward', 0.0):.4f}",
        "",
        "--- ACTIVE ALERTS ---",
    ]
    for a in state.get("alerts", []):
        lines.append(f"  [{a['severity'].upper()}] {a['service']}: {a['message']}")

    lines += ["", "--- SERVICE STATUS ---"]
    for svc, status in state.get("services", {}).items():
        lines.append(f"  {svc}: {status}")

    lines += ["", "--- METRICS (current) ---"]
    for m in state.get("metrics", []):
        lines.append(f"  {m['service']}: CPU={m['cpu_percent']:.1f}% MEM={m['memory_percent']:.1f}% ERR={m['error_rate']:.1f}% LAT={m['latency_ms']:.0f}ms")

    lines += ["", "--- RECENT LOGS (newest last) ---"]
    for log in state.get("recent_logs", [])[-8:]:
        lines.append(f"  [{log['level']}] {log['service']}: {log['message']}")

    lines += ["", f"Last feedback: {state.get('message', '')}"]
    lines += ["", "What is your next action? Respond with JSON only."]
    return "\n".join(lines)


def get_action(state: dict, history: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": state_to_prompt(state)})
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=200,
        temperature=0.1,
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def run_task(task_id: str) -> float:
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    state = resp.json()

    print(f"[START] task={task_id}", flush=True)

    history = []
    step = 0

    while not state.get("done", False):
        try:
            action = get_action(state, history)
        except Exception as e:
            action = {"action_type": "escalate", "target": "oncall", "details": f"parse_error: {str(e)}"}

        history.append({"role": "assistant", "content": json.dumps(action)})

        try:
            resp = requests.post(f"{ENV_URL}/step", json=action, timeout=30)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            print(f"[STEP] step={step+1} reward=0.0000", flush=True)
            break

        state = result["state"]
        reward = result["reward"]
        step += 1

        print(
            f"[STEP] step={step} reward={reward:.4f}",
            flush=True,
        )

        if state.get("done"):
            break

    final_score = round(state.get("total_reward", 0.0), 4)
    success = final_score >= 0.5
    print(f"[END] task={task_id} score={final_score} steps={step}", flush=True)
    return final_score


def main():
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    all_scores = {}
    for task_id in TASKS:
        try:
            score = run_task(task_id)
            all_scores[task_id] = score
        except Exception as e:
            print(f"[END] task={task_id} score=0.0 steps=0", flush=True)
            all_scores[task_id] = 0.0
        time.sleep(2)

    avg = sum(all_scores.values()) / len(all_scores)
    print(f"\n=== SUMMARY ===", flush=True)
    for tid, score in all_scores.items():
        print(f"  {tid}: {score:.4f}", flush=True)
    print(f"  AVERAGE: {avg:.4f}", flush=True)


if __name__ == "__main__":
    main()
