from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import ApprovalRequest, TaskRecord, TaskRequest
from backend.task_manager import TaskManager

app = FastAPI(
    title="Nexus Data Platform",
    description="AI-powered multi-agent DataOps automation platform with human approval before deployment.",
    version="1.0.0",
)

# Allow frontend HTML page to call backend APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = TaskManager()


@app.get("/")
def root() -> dict:
    return {
        "project": "Nexus Data Platform",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/tasks", response_model=TaskRecord)
def create_task(request: TaskRequest) -> TaskRecord:
    return manager.create_task(request)


@app.get("/tasks", response_model=list[TaskRecord])
def list_tasks() -> list[TaskRecord]:
    return manager.list_tasks()


@app.get("/tasks/{task_id}", response_model=TaskRecord)
def get_task(task_id: str) -> TaskRecord:
    try:
        return manager.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tasks/{task_id}/run", response_model=TaskRecord)
def run_task(task_id: str) -> TaskRecord:
    try:
        return manager.run_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/tasks/{task_id}/approval", response_model=TaskRecord)
def approve_task(task_id: str, approval: ApprovalRequest) -> TaskRecord:
    try:
        return manager.approve_task(task_id, approval)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tasks/{task_id}/deploy", response_model=TaskRecord)
def deploy_task(task_id: str) -> TaskRecord:
    try:
        return manager.deploy_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc