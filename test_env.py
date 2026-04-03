#!/usr/bin/env python3
"""Quick test of the IncidentResponseEnv"""
import sys
sys.path.insert(0, '/Users/sabaanjum/Documents/Meta Hackathon/incident-response-env')

from app.env import IncidentResponseEnv
from app.models import Action, ActionType

# Test reset
env = IncidentResponseEnv()
state = env.reset("single_service_down")
print(f"✓ Reset successful. Task: {state.task_id}, Difficulty: {state.task_difficulty}")
print(f"  Max steps: {state.max_steps}, Time budget: {state.time_budget}s")
print(f"  Services: {list(state.services.keys())}")
print(f"  Alerts: {len(state.alerts)}")

# Test step
action = Action(
    action_type=ActionType.CHECK_METRICS,
    target="payment-service",
    details=""
)
result = env.step(action)
print(f"\n✓ Step successful. Reward: {result.reward}, Total: {result.state.total_reward}")
print(f"  Feedback: {result.info.get('feedback', '')[:80]}")

# Test state retrieval
state = env.get_state()
print(f"\n✓ Get state successful. Step count: {state.step_count}")

# Test cascading failure task
state = env.reset("cascading_failure")
print(f"\n✓ Cascading failure task reset. Services: {list(state.services.keys())}")

# Test memory leak task
state = env.reset("memory_leak")
print(f"\n✓ Memory leak task reset. Alerts: {[a.service for a in state.alerts]}")

print("\n✓✓✓ All basic tests passed! ✓✓✓")
