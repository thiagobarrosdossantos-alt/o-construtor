"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from datetime import datetime

router = APIRouter()


@router.get("")
async def health_check():
    """Verifica saúde da API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "o-construtor-api"
    }


@router.get("/detailed")
async def detailed_health():
    """Health check detalhado com status de componentes"""
    from api.main import get_orchestrator, get_event_bus, get_memory_store

    orchestrator = get_orchestrator()
    event_bus = get_event_bus()
    memory_store = get_memory_store()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "orchestrator": {
                "status": "healthy" if orchestrator else "unavailable",
                "agents_count": len(orchestrator._agents) if orchestrator else 0
            },
            "event_bus": {
                "status": "healthy" if event_bus else "unavailable",
                "subscribers_count": len(event_bus._subscribers) if event_bus else 0
            },
            "memory_store": {
                "status": "healthy" if memory_store else "unavailable",
                "items_count": len(memory_store._store) if memory_store else 0
            }
        }
    }
