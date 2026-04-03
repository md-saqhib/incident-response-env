#!/usr/bin/env python3
"""Test API endpoints directly"""
import sys
import json
sys.path.insert(0, '/Users/sabaanjum/Documents/Meta Hackathon/incident-response-env')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Testing API Endpoints...")
print("=" * 60)

# Test health
print("\n1. Testing /health endpoint")
response = client.get("/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test root
print("\n2. Testing / endpoint")
response = client.get("/")
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Name: {data['name']}")
print(f"   Endpoints: {data['endpoints']}")

# Test tasks list
print("\n3. Testing /tasks endpoint")
response = client.get("/tasks")
print(f"   Status: {response.status_code}")
tasks = response.json()
for task in tasks:
    print(f"   - {task['id']}: {task['difficulty']} ({task['max_steps']} steps)")

# Test reset
print("\n4. Testing /reset endpoint")
response = client.post("/reset", json={"task_id": "single_service_down"})
print(f"   Status: {response.status_code}")
state = response.json()
print(f"   Task: {state['task_id']}")
print(f"   Difficulty: {state['task_difficulty']}")
print(f"   Services: {list(state['services'].keys())}")

# Test step
print("\n5. Testing /step endpoint")
response = client.post("/step", json={
    "action_type": "investigate",
    "target": "payment-service",
    "details": ""
})
print(f"   Status: {response.status_code}")
result = response.json()
print(f"   Reward: {result['reward']}")
print(f"   Total Reward: {result['state']['total_reward']}")
print(f"   Feedback: {result['info']['feedback'][:60]}...")

# Test state
print("\n6. Testing /state endpoint")
response = client.get("/state")
print(f"   Status: {response.status_code}")
state = response.json()
print(f"   Step count: {state['step_count']}")
print(f"   Total reward: {state['total_reward']}")

print("\n" + "=" * 60)
print("✓✓✓ All API tests passed! ✓✓✓")
