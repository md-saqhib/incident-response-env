---
title: IncidentResponseEnv
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: docker
app_file: app/main.py
pinned: false
---

# 🎯 IncidentResponseEnv

**An OpenEnv-compliant RL environment for production incident response training**

Train LLM agents to diagnose and fix production incidents in a safe, simulated environment. No broken production needed. 🚀

### ⚡ Quick Links
- 🌐 **[Live Demo on HuggingFace Spaces](#live-demo)** ← Test it now!
- 📖 **[Quickstart Guide](QUICK_START.md)** ← Get running in 5 min
- 📚 **[Full Build Summary](BUILD_SUMMARY.md)** ← Complete overview

---

## 🎮 What It Does

An LLM agent operates in a simulated production system:
- Receives **real-time alerts** (system degradation notifications)
- Accesses **live metrics** (CPU, memory, error rate, latency per service)
- Can **investigate logs** (searchable by service)
- Must **diagnose the root cause** (not just treat symptoms)
- Applies the **correct fix** to maximize rewards
- Gets **instant feedback** on correctness

**Observation space:** alerts, metrics, logs, service statuses, time remaining  
**Action space:** investigate, check_metrics, diagnose, fix, escalate  
**Reward:** 0.0–1.0 (partial signals at each correct step)

## 📚 3 Graded Difficulty Tasks

| Task | Difficulty | Scenario | Root Cause | Max Steps |
|------|-----------|----------|-----------|-----------|
| **single_service_down** | 🟢 Easy | payment-service crashes | OutOfMemoryError | 10 |
| **cascading_failure** | 🟡 Medium | DB connection pool exhausted | postgres-db pool limit | 15 |
| **memory_leak** | 🔴 Hard | Silent 6-hour memory leak | AnalyticsReportCache leak | 20 |

---

## 🚀 Live Demo

**[Try IncidentResponseEnv on HuggingFace Spaces →](https://huggingface.co/spaces/Saqhibb/incident-response-env)**

Reference source repo: **[GitHub →](https://github.com/md-saqhib/incident-response-env)**

---

## 🏃 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Test It (New Terminal)
```bash
# Option A: Run example walkthrough
python example_agent_interaction.py

# Option B: Use curl
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "single_service_down"}'
```

### 4. Run LLM Agent (Optional)
```bash
export HF_TOKEN=hf_your_token_here
python inference.py
```

For detailed setup, see [QUICK_START.md](QUICK_START.md)

---

## 🔌 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/reset` | Start new episode |
| `POST` | `/step` | Take action |
| `GET` | `/state` | Get current state |
| `GET` | `/tasks` | List all tasks |
| `GET` | `/health` | Health check |

### Example: Solve an Incident

```bash
# 1. Start episode
curl -X POST http://localhost:8000/reset \
  -d '{"task_id": "single_service_down"}'

# 2. Investigate payment-service
curl -X POST http://localhost:8000/step \
  -d '{"action_type": "investigate", "target": "payment-service"}'

# 3. Diagnose the problem
curl -X POST http://localhost:8000/step \
  -d '{"action_type": "diagnose", "target": "OutOfMemoryError"}'

# 4. Fix it
curl -X POST http://localhost:8000/step \
  -d '{"action_type": "fix", "target": "payment-service"}'

# Reward = 1.0 if all steps are correct! ✅
```

---

## 📊 Reward Structure

- **Correct diagnosis**: +0.40 (one-time bonus)
- **Correct fix**: +0.35 (one-time bonus)
- **Time bonus**: +0.15 × (time_remaining / time_budget)
- **Efficiency bonus**: +0.10 × (1 - wrong_actions / total_actions)
- **Wrong action penalty**: -0.10 per mistake
- **Range**: [0.0, 1.0] with clipping

Agents get **partial rewards** as they make progress, encouraging incremental learning.

### Reliability Guarantees (Evaluator-focused)

- ✅ Task output score is forced to strict range $(0, 1)$ via score clamping
- ✅ Structured logging always emits `[START]`, `[STEP]`, and `[END]`
- ✅ Agent performs mandatory LiteLLM/OpenAI proxy calls before task execution
- ✅ Deterministic fallback action playbook recovers from malformed LLM JSON

---

## 🏗️ Architecture

```
LLM Agent (Llama, Mistral, GPT, etc.)
    ↓
REST API (/reset, /step, /state)
    ↓
IncidentResponseEnv (core environment class)
    ↓
Task (SingleServiceDown, CascadingFailure, MemoryLeak)
    ↓
Reward Calculator
    ↓
Agent Feedback (observation + reward)
```

**Type-safe interfaces** using Pydantic models ensure correctness.

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t incident-response-env .

# Run locally
docker run -p 7860:7860 incident-response-env

# Or deploy to HF Spaces (automatic)
git push hf main
```

---

## 📁 File Structure

```
incident-response-env/
├── app/
│   ├── main.py              # FastAPI server (6 endpoints)
│   ├── env.py               # IncidentResponseEnv class
│   ├── models.py            # Pydantic data models
│   └── tasks/               # 3 incident scenarios
│       ├── base.py
│       ├── task_easy.py
│       ├── task_medium.py
│       └── task_hard.py
├── inference.py             # LLM agent (HuggingFace)
├── requirements.txt         # Dependencies
├── Dockerfile               # Docker config
├── openenv.yaml             # OpenEnv spec
└── test_*.py                # Unit tests (all passing)
```

---

## ✅ Tests

All tests pass:

```bash
python -m pytest test_env.py test_api.py test_inference.py -v
```

- ✅ **test_env.py**: Core environment (reset, step, state)
- ✅ **test_api.py**: All 6 endpoints
- ✅ **test_inference.py**: LLM agent script

---

## 🎓 Learn More

- **Want to understand OpenEnv?** → See [OpenEnv Course](https://github.com/raun/openenv-course)
- **Want deployment details?** → See [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
- **Want to submit to hackathon?** → See [HACKATHON_SUBMISSION_ROADMAP.md](HACKATHON_SUBMISSION_ROADMAP.md)
