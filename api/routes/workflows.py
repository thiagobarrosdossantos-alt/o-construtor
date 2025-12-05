"""
Workflow management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class WorkflowCreate(BaseModel):
    """Request para criar workflow"""
    name: str
    description: str
    steps: List[dict]
    trigger: Optional[str] = "manual"


@router.post("")
async def create_workflow(workflow: WorkflowCreate):
    """Cria novo workflow"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    workflow_id = await orchestrator.create_workflow(
        name=workflow.name,
        description=workflow.description,
        steps=workflow.steps,
        trigger=workflow.trigger
    )

    return {
        "workflow_id": workflow_id,
        "status": "created"
    }


@router.get("")
async def list_workflows():
    """Lista workflows"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    workflows = await orchestrator.list_workflows()

    return {
        "workflows": workflows,
        "total": len(workflows)
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Busca workflow por ID"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    workflow = await orchestrator.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, context: Optional[dict] = None):
    """Executa workflow"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    execution_id = await orchestrator.execute_workflow(
        workflow_id=workflow_id,
        context=context or {}
    )

    return {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "started"
    }


@router.get("/{workflow_id}/executions")
async def get_workflow_executions(workflow_id: str):
    """Lista execuções de um workflow"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    executions = await orchestrator.get_workflow_executions(workflow_id)

    return {
        "workflow_id": workflow_id,
        "executions": executions,
        "total": len(executions)
    }
