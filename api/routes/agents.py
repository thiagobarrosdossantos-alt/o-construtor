"""
Agent management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()


@router.get("")
async def list_agents():
    """Lista todos os agentes"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    agents = await orchestrator.list_agents()

    return {
        "agents": agents,
        "total": len(agents)
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Busca agente por ID"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    agent = await orchestrator.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Busca status de um agente"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    status = await orchestrator.get_agent_status(agent_id)

    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")

    return status


@router.get("/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Lista tarefas de um agente"""
    from api.main import get_orchestrator

    orchestrator = get_orchestrator()

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    tasks = await orchestrator.get_agent_tasks(agent_id)

    return {
        "agent_id": agent_id,
        "tasks": tasks,
        "total": len(tasks)
    }
