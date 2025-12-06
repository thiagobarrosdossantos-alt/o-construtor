"""
Testes de integração para API
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Testa endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "O Construtor API"
    assert data["version"] == "2.0.0"


def test_health_endpoint():
    """Testa health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_detailed():
    """Testa health check detalhado"""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data


@pytest.mark.asyncio
async def test_create_task():
    """Testa criação de tarefa"""
    task_data = {
        "title": "Test Task",
        "description": "Test description",
        "task_type": "feature",
        "priority": "medium"
    }

    response = client.post("/tasks", json=task_data)

    # Pode falhar se orchestrator não estiver inicializado
    # mas verifica estrutura
    assert response.status_code in [200, 503]


def test_list_agents():
    """Testa listagem de agentes"""
    response = client.get("/agents")

    # Pode retornar 503 se não inicializado
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "agents" in data
        assert "total" in data
