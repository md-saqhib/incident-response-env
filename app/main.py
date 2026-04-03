from fastapi import FastAPI, HTTPException
from app.env import IncidentResponseEnv
from app.models import Action, ResetRequest, SystemState, StepResult

app = FastAPI(
    title="IncidentResponseEnv",
    description="OpenEnv-compliant production incident response RL environment.",
    version="1.0.0",
)

env = IncidentResponseEnv()


@app.get("/")
def root():
    return {
        "name": "IncidentResponseEnv",
        "version": "1.0.0",
        "description": "LLM agent learns to diagnose and fix production incidents.",
        "endpoints": ["/reset", "/step", "/state", "/tasks"],
    }


@app.post("/reset", response_model=SystemState)
def reset(request: ResetRequest = ResetRequest()):
    try:
        return env.reset(request.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(action: Action):
    try:
        return env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=SystemState)
def state():
    try:
        return env.get_state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
def tasks():
    return env.list_tasks()


@app.get("/health")
def health():
    return {"status": "ok"}
