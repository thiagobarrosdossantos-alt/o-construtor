"""
Task management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class TaskCreate(BaseModel):
    """Request para criar tarefa"""
    title: str
    description: str
    task_type: str
    priority: Optional[str] = "medium"
    context: Optional[dict] = None


class TaskResponse(BaseModel):
    """Response de tarefa"""
    task_id: str
    title: str
    description: str
    status: str
    created_at: str
    assigned_agents: List[str]


@router.post("", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Cria nova tarefa"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    # Cria tarefa
    task_id = await orchestrator.create_task(
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        priority=task.priority,
        context=task.context or {}
    )

    # Busca tarefa criada
    task_data = await orchestrator.get_task(task_id)

    return TaskResponse(
        task_id=task_id,
        title=task_data["title"],
        description=task_data["description"],
        status=task_data["status"],
        created_at=task_data["created_at"],
        assigned_agents=task_data.get("assigned_agents", [])
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Busca tarefa por ID"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    task_data = await orchestrator.get_task(task_id)

    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        task_id=task_id,
        title=task_data["title"],
        description=task_data["description"],
        status=task_data["status"],
        created_at=task_data["created_at"],
        assigned_agents=task_data.get("assigned_agents", [])
    )


@router.get("")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """Lista tarefas"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    tasks = await orchestrator.list_tasks(status=status, limit=limit)

    return {
        "tasks": tasks,
        "total": len(tasks)
    }


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancela tarefa"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    success = await orchestrator.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

    return {"status": "cancelled", "task_id": task_id}
