#!/usr/bin/env python3
"""
Complete end-to-end example showing how an LLM agent interacts with IncidentResponseEnv
"""
import sys
sys.path.insert(0, '/Users/sabaanjum/Documents/Meta Hackathon/incident-response-env')

from app.env import IncidentResponseEnv
from app.models import Action, ActionType

def simulate_agent_interaction():
    """Simulate a smart agent solving the easy task"""
    
    env = IncidentResponseEnv()
    
    # ─────────────────────────────────────────────────────
    # TASK 1: Single Service Down (Easy)
    # ─────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("SCENARIO 1: Single Service Down (Easy Task)")
    print("="*70)
    
    state = env.reset("single_service_down")
    print(f"\n[RESET] Task: {state.task_id} | Difficulty: {state.task_difficulty}")
    print(f"Time: {state.time_remaining}s | Max steps: {state.max_steps}")
    print(f"\nAlerts ({len(state.alerts)}):")
    for a in state.alerts:
        print(f"  [{a.severity.upper()}] {a.service}: {a.message}")
    
    # Step 1: Check metrics for all services
    print("\n[STEP 1] Check metrics for payment-service")
    action = Action(action_type=ActionType.CHECK_METRICS, target="payment-service")
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    # Step 2: Investigate logs
    print("\n[STEP 2] Investigate payment-service logs")
    action = Action(action_type=ActionType.INVESTIGATE, target="payment-service")
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    print(f"Recent logs reveal:")
    for log in result.state.recent_logs[-3:]:
        if "payment" in log.service.lower():
            print(f"  [{log.level}] {log.message}")
    
    # Step 3: Diagnose
    print("\n[STEP 3] Diagnose the root cause")
    action = Action(
        action_type=ActionType.DIAGNOSE, 
        target="payment-service",
        details="memory oom exhausted heap"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    # Step 4: Fix
    print("\n[STEP 4] Apply fix - restart payment-service")
    action = Action(
        action_type=ActionType.FIX,
        target="payment-service",
        details="restart container"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    print(f"\n✓ EPISODE COMPLETE | Final Score: {result.state.total_reward}/1.0")
    
    # ─────────────────────────────────────────────────────
    # TASK 2: Cascading Failure (Medium)
    # ─────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("SCENARIO 2: Cascading Failure (Medium Task)")
    print("="*70)
    
    state = env.reset("cascading_failure")
    print(f"\n[RESET] Task: {state.task_id} | Difficulty: {state.task_difficulty}")
    print(f"Services in trouble: {[s for s,st in state.services.items() if st != 'healthy']}")
    print(f"\nAlerts ({len(state.alerts)}):")
    for a in state.alerts:
        print(f"  [{a.severity.upper()}] {a.service}: {a.message[:60]}...")
    
    # Smart agent strategy: Check metrics to identify the pattern
    print("\n[STEP 1] Check metrics for postgres-db")
    action = Action(action_type=ActionType.CHECK_METRICS, target="postgres-db")
    result = env.step(action)
    print(f"Reward: +{result.reward} | Feedback: {result.info['feedback']}")
    
    print("\n[STEP 2] Investigate postgres-db logs")
    action = Action(action_type=ActionType.INVESTIGATE, target="postgres-db")
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    print("\n[STEP 3] Diagnose: postgres connection pool exhaustion")
    action = Action(
        action_type=ActionType.DIAGNOSE,
        target="postgres-db",
        details="connection pool exhausted limit 100"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback'][:100]}...")
    
    print("\n[STEP 4] Fix: Scale postgres connection pool")
    action = Action(
        action_type=ActionType.FIX,
        target="postgres-db",
        details="scale connection pool to 200"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"✓ CASCADING FAILURE RESOLVED | Final Score: {result.state.total_reward}/1.0")
    
    # ─────────────────────────────────────────────────────
    # TASK 3: Memory Leak (Hard)
    # ─────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("SCENARIO 3: Silent Memory Leak (Hard Task)")
    print("="*70)
    
    state = env.reset("memory_leak")
    print(f"\n[RESET] Task: {state.task_id} | Difficulty: {state.task_difficulty}")
    print(f"⚠️  No CRITICAL alert! This is subtle. Analyze trends.")
    print(f"\nAlerts ({len(state.alerts)}):")
    for a in state.alerts:
        print(f"  [{a.severity.upper()}] {a.service}: {a.message[:60]}...")
    
    print("\n[STEP 1] Check metrics for analytics-service")
    action = Action(action_type=ActionType.CHECK_METRICS, target="analytics-service")
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    print("\n[STEP 2] Check trends for data-pipeline (baseline)")
    action = Action(action_type=ActionType.CHECK_METRICS, target="data-pipeline")
    result = env.step(action)
    print(f"Reward: +{result.reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    print("\n[STEP 3] Investigate analytics-service detailed logs")
    action = Action(action_type=ActionType.INVESTIGATE, target="analytics-service")
    result = env.step(action)
    print(f"Reward: +{result.reward}")
    print(f"Feedback: {result.info['feedback']}")
    
    print("\n[STEP 4] Diagnose: Memory leak in analytics-service")
    action = Action(
        action_type=ActionType.DIAGNOSE,
        target="analytics-service",
        details="memory leak heap gc cache unreleased"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"Feedback: {result.info['feedback'][:120]}...")
    
    print("\n[STEP 5] Fix: Rolling restart of analytics-service")
    action = Action(
        action_type=ActionType.FIX,
        target="analytics-service",
        details="rolling restart to clear heap"
    )
    result = env.step(action)
    print(f"Reward: +{result.reward} | Total: {result.state.total_reward}")
    print(f"✓ MEMORY LEAK FIXED | Final Score: {result.state.total_reward}/1.0")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
An intelligent agent should:
1. ✓ Observe all metrics and alerts
2. ✓ Investigate logs only when actionable
3. ✓ Identify ROOT CAUSE (not symptoms)
4. ✓ Apply the CORRECT FIX
5. ✓ Minimize wasted steps for efficiency bonus

Reward breakdown:
  - Correct diagnosis: +0.40
  - Correct fix: +0.35
  - Time bonus: +0.15 × (time_remaining / 300)
  - Efficiency: +0.10 × (1 - wrong_actions / total_actions)

Success threshold: ≥ 0.5 points
    """)

if __name__ == "__main__":
    simulate_agent_interaction()
    print("\n✓✓✓ End-to-end walkthrough complete! ✓✓✓\n")
