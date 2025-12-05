"""
Configuração pytest para testes
"""
import pytest
import asyncio
from typing import Generator

# Fixture para event loop
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Cria event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env(monkeypatch):
    """Mock de variáveis de ambiente"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
