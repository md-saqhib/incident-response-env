# Quick Start Guide — IncidentResponseEnv

## ⚡ 30-Second Setup

```bash
# 1. Navigate to project
cd ~/Documents/Meta\ Hackathon/incident-response-env

# 2. Dependencies already installed? If not:
pip install -r requirements.txt

# 3. Start local server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. In another terminal, test it
python example_agent_interaction.py

# 5. Run baseline agent with HuggingFace LLM
export HF_TOKEN=hf_your_token_here
python inference.py
```

---

## 📝 API Usage Examples

### 1. Reset (Start New Episode)

```bash
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "single_service_down"}'
```

**Response:**
```json
{
  "task_id": "single_service_down",
  "task_difficulty": "easy",
  "step_count": 0,
  "max_steps": 10,
  "time_budget": 300,
  "time_remaining": 300,
  "alerts": [...],
  "metrics": [...],
  "recent_logs": [...],
  "services": {
    "api-gateway": "degraded",
    "payment-service": "down",
    "user-service": "healthy",
    "notification-service": "healthy"
  },
  "done": false,
  "reward": 0.0,
  "total_reward": 0.0,
  "message": "Incident active. Investigate and fix the root cause."
}
```

### 2. Take Action (Step)

```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "investigate",
    "target": "payment-service",
    "details": ""
  }'
```

**Response:**
```json
{
  "state": {...state object...},
  "reward": 0.02,
  "done": false,
  "info": {
    "action": "investigate",
    "target": "payment-service",
    "feedback": "Retrieved 7 detailed log entries for payment-service."
  }
}
```

### 3. Get Current State

```bash
curl http://localhost:8000/state
```

### 4. List All Tasks

```bash
curl http://localhost:8000/tasks
```

**Response:**
```json
[
  {
    "id": "single_service_down",
    "difficulty": "easy",
    "description": "A single microservice is down...",
    "max_steps": 10,
    "time_budget": 300
  },
  {
    "id": "cascading_failure",
    "difficulty": "medium",
    "description": "A cascading failure across...",
    "max_steps": 15,
    "time_budget": 300
  },
  {
    "id": "memory_leak",
    "difficulty": "hard",
    "description": "A silent memory leak...",
    "max_steps": 20,
    "time_budget": 300
  }
]
```

---

## 🤖 Agent Strategy

### For Each Task:

**1. Initial Observation**
```python
action = Action(action_type=ActionType.CHECK_METRICS, target="all_services")
```

**2. Narrow Down Anomalies**
- Look for high CPU, memory, error_rate, latency
- Identify the degraded/down service

**3. Gather Evidence**
```python
action = Action(action_type=ActionType.INVESTIGATE, target="suspect_service")
```

**4. Diagnose Root Cause** (Not just symptoms!)
```python
action = Action(
    action_type=ActionType.DIAGNOSE,
    target="root_cause_service",
    details="specific_problem_keywords"
)
```

**5. Apply Fix**
```python
action = Action(
    action_type=ActionType.FIX,
    target="root_cause_service",
    details="fix_action_description"
)
```

---

## 🎯 Task-Specific Hints

### Task 1: Single Service Down ✓ Easy

| Step | Action | Target | Details |
|------|--------|--------|---------|
| 1 | check_metrics | payment-service | (observe 98% memory) |
| 2 | investigate | payment-service | (read OutOfMemoryError logs) |
| 3 | diagnose | payment-service | "memory oom" |
| 4 | fix | payment-service | "restart" |

### Task 2: Cascading Failure ⭐ Medium

| Step | Insight | Action | Why |
|------|---------|--------|-----|
| 1 | api-gateway and order-service are SYMPTOMS | check_metrics postgres-db | Real root cause is DB |
| 2 | DB shows 98% connection pool | investigate postgres-db | Understand the bottleneck |
| 3 | Connection queue confirms it | diagnose postgres-db | "connection pool exhausted" |
| 4 | Unblock the source | fix postgres-db | "scale pool" |

### Task 3: Silent Memory Leak ⚠️ Hard

| Step | Technique | Action | What to Look For |
|------|-----------|--------|------------------|
| 1 | Check trends | check_metrics analytics-service | Memory growing 40%→84% over 6h |
| 2 | Compare baseline | check_metrics data-pipeline | Other services stable (~48%) |
| 3 | Dig deep | investigate analytics-service | "AnalyticsReportCache" leak |
| 4 | Confirm & fix | diagnose analytics-service "memory leak heap" | Then restart |

---

## 🐳 Docker Deployment

### Build & Test Locally

```bash
# Build image
docker build -t incident-response-env:latest .

# Run with volume mount (for development)
docker run -it --rm \
  -p 7860:7860 \
  -e HF_TOKEN=hf_your_token \
  -v $(pwd):/app \
  incident-response-env:latest

# Test from host
curl http://localhost:7860/health
```

### Push to HuggingFace Spaces

```bash
# 1. Create space on HuggingFace
huggingface-cli repo create incident-response-env --type space --space_sdk docker

# 2. Clone it
git clone https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env
cd incident-response-env

# 3. Copy files
cp -r /path/to/incident-response-env/* .
git add .
git commit -m "Initial commit"
git push

# Space will auto-build and deploy!
```

---

## 📊 Monitoring Inference Performance

```bash
# Run all 3 tasks and track scores
export HF_TOKEN=hf_xxxx
python inference.py 2>&1 | tee inference_log.txt

# Extract summary
grep -E "^\[START\]|^\[END\]" inference_log.txt
```

**Sample Output:**
```
[START] task_id=single_service_down difficulty=easy
[STEP] step=1 action=check_metrics target=payment-service reward=0.0200 total_reward=0.0200
[STEP] step=2 action=investigate target=payment-service reward=0.0200 total_reward=0.0400
[STEP] step=3 action=diagnose target=payment-service reward=0.4000 total_reward=0.4400
[STEP] step=4 action=fix target=payment-service reward=0.5500 total_reward=0.9900
[END] task_id=single_service_down final_score=0.9900 success=true

[START] task_id=cascading_failure difficulty=medium
...
[END] task_id=cascading_failure final_score=0.8500 success=true

[START] task_id=memory_leak difficulty=hard
...
[END] task_id=memory_leak final_score=0.7200 success=true

=== SUMMARY ===
  single_service_down: 0.9900
  cascading_failure: 0.8500
  memory_leak: 0.7200
  AVERAGE: 0.8533
```

---

## 🧪 Run Tests

```bash
# Environment tests
python test_env.py

# API tests (TestClient)
python test_api.py

# Inference validation
python test_inference.py

# Full agent walkthrough
python example_agent_interaction.py
```

---

## 🔍 Debugging

### Q: Server won't start
**A:** Check port is free: `lsof -i :8000` and kill if needed

### Q: Import errors
**A:** Make sure you're in project root: `ls app/main.py` should work

### Q: HF_TOKEN not working
**A:** Validate token at https://huggingface.co/settings/tokens

### Q: Slow inference
**A:** Check HuggingFace API status. Consider caching or batch requests.

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app definition |
| `app/env.py` | IncidentResponseEnv core class |
| `app/models.py` | Pydantic data models |
| `app/tasks/base.py` | Abstract task interface |
| `app/tasks/task_*.py` | 3 concrete task implementations |
| `inference.py` | Baseline LLM agent |
| `openenv.yaml` | OpenEnv specification |
| `Dockerfile` | Container build config |
| `test_*.py` | Unit tests |
| `example_agent_interaction.py` | Walkthrough example |

---

## 💡 Tips for Success

1. **Understand the tasks before coding**: Read the scenario descriptions carefully
2. **Partial rewards matter**: Don't just go for the fix, rack up diagnostic points
3. **Time is precious**: Finish quickly to get the 15% time bonus
4. **Efficiency counts**: Minimize wrong attempts for the 10% efficiency bonus
5. **Inference format**: Always follow `[START]`/`[STEP]`/`[END]` logging

---

## 🎓 Learning Outcomes

After using IncidentResponseEnv, you'll understand:

✓ How LLM agents reason about real-world incidents
✓ Partial reward signals and their design
✓ Root cause analysis (not symptom treatment)
✓ OpenEnv environment standardization
✓ FastAPI for rapid prototyping
✓ Docker for production deployment
✓ HuggingFace Spaces for free inference

---

**Good luck! 🚀**
