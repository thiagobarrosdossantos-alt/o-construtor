"""
Unit tests para Orchestrator
Testa orquestração, workflows, e seleção de modelos
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from core.orchestrator import Orchestrator, Workflow, WorkflowState, AgentRole
from config.models import TaskType


@pytest.mark.asyncio
class TestOrchestrator:
    """Testes do Orchestrator"""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock de variáveis de ambiente"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

    async def test_orchestrator_initialization(self, mock_env):
        """Testa inicialização do orchestrator"""
        orch = Orchestrator()

        assert orch is not None
        assert orch.active_workflows == {}
        assert orch.agents == {}
        assert orch._initialized is False

    async def test_api_clients_initialization(self, mock_env):
        """Testa inicialização dos clientes de API"""
        orch = Orchestrator()

        assert orch.anthropic_client is not None
        assert orch.openai_client is not None
        assert orch.gemini_available is True

    async def test_api_clients_missing_keys(self, monkeypatch):
        """Testa comportamento quando API keys estão ausentes"""
        # Remove todas as keys
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        orch = Orchestrator()

        assert orch.anthropic_client is None
        assert orch.openai_client is None
        assert orch.gemini_available is False

    async def test_orchestrator_initialize(self, mock_env):
        """Testa método initialize"""
        orch = Orchestrator()

        await orch.initialize()

        assert orch._initialized is True
        assert len(orch.agents) > 0

    async def test_initialize_idempotent(self, mock_env):
        """Testa que initialize pode ser chamado múltiplas vezes"""
        orch = Orchestrator()

        await orch.initialize()
        initial_agents = len(orch.agents)

        await orch.initialize()  # Segunda chamada

        assert len(orch.agents) == initial_agents

    async def test_create_feature_workflow(self, mock_env):
        """Testa criação de workflow de feature"""
        orch = Orchestrator()
        await orch.initialize()

        request = {
            "title": "Add Login Feature",
            "description": "Implement user login"
        }

        workflow = orch._create_feature_workflow(request)

        assert workflow is not None
        assert workflow.name == "Feature: Add Login Feature"
        assert len(workflow.steps) > 0
        assert workflow.state == WorkflowState.PENDING

    async def test_create_bugfix_workflow(self, mock_env):
        """Testa criação de workflow de bugfix"""
        orch = Orchestrator()
        await orch.initialize()

        request = {
            "title": "Fix Memory Leak",
            "description": "Fix memory leak in TaskQueue"
        }

        workflow = orch._create_bugfix_workflow(request)

        assert workflow is not None
        assert workflow.name == "Bugfix: Fix Memory Leak"
        assert len(workflow.steps) > 0

    async def test_create_refactor_workflow(self, mock_env):
        """Testa criação de workflow de refactor"""
        orch = Orchestrator()
        await orch.initialize()

        request = {
            "title": "Refactor Authentication",
            "description": "Refactor auth module"
        }

        workflow = orch._create_refactor_workflow(request)

        assert workflow is not None
        assert workflow.name == "Refactor: Refactor Authentication"

    async def test_build_prompt(self, mock_env):
        """Testa construção de prompts"""
        orch = Orchestrator()
        await orch.initialize()

        agent_config = Mock()
        agent_config.name = "Test Agent"
        agent_config.emoji = "🤖"
        agent_config.description = "Test agent description"

        prompt = orch._build_prompt(
            agent_config=agent_config,
            task_type="test",
            input_data={"key": "value"},
            context={"context_key": "context_value"}
        )

        assert "Test Agent" in prompt
        assert "🤖" in prompt
        assert "test" in prompt
        assert "key" in prompt

    async def test_format_dict(self, mock_env):
        """Testa formatação de dicionário para prompt"""
        orch = Orchestrator()

        data = {
            "name": "test",
            "value": 42,
            "nested": {"inner": "value"}
        }

        formatted = orch._format_dict(data)

        assert "name: test" in formatted
        assert "value: 42" in formatted
        assert "nested:" in formatted

    async def test_format_dict_truncates_long_strings(self, mock_env):
        """Testa truncagem de strings longas"""
        orch = Orchestrator()

        long_string = "x" * 300
        data = {"long": long_string}

        formatted = orch._format_dict(data)

        assert len(formatted) < len(long_string)
        assert "..." in formatted

    async def test_get_agent_status(self, mock_env):
        """Testa obtenção de status dos agentes"""
        orch = Orchestrator()
        await orch.initialize()

        status = orch.get_agent_status()

        assert isinstance(status, dict)
        assert len(status) > 0

    @patch('core.orchestrator.Orchestrator._call_model')
    async def test_call_agent_success(self, mock_call_model, mock_env):
        """Testa chamada de agente com sucesso"""
        mock_call_model.return_value = "Test response"

        orch = Orchestrator()
        await orch.initialize()

        agent_config = Mock()
        agent_config.name = "Test Agent"

        model = Mock()
        model.name = "test-model"

        result = await orch._call_agent(
            agent_config=agent_config,
            model=model,
            task_type=TaskType.CODE_IMPLEMENTATION,
            input_data={},
            context={}
        )

        assert result["status"] == "success"
        assert result["agent"] == "Test Agent"
        assert result["model"] == "test-model"

    @patch('core.orchestrator.Orchestrator._call_model')
    async def test_call_agent_error_handling(self, mock_call_model, mock_env):
        """Testa tratamento de erro em chamada de agente"""
        mock_call_model.side_effect = Exception("API Error")

        orch = Orchestrator()
        await orch.initialize()

        agent_config = Mock()
        agent_config.name = "Test Agent"

        model = Mock()
        model.name = "test-model"

        result = await orch._call_agent(
            agent_config=agent_config,
            model=model,
            task_type=TaskType.CODE_IMPLEMENTATION,
            input_data={},
            context={}
        )

        assert result["status"] == "error"
        assert "error" in result
        assert "API Error" in result["error"]

    async def test_workflow_has_required_fields(self, mock_env):
        """Testa que workflow tem campos obrigatórios"""
        orch = Orchestrator()
        await orch.initialize()

        request = {"title": "Test", "description": "Test workflow"}
        workflow = orch._create_feature_workflow(request)

        assert hasattr(workflow, 'id')
        assert hasattr(workflow, 'name')
        assert hasattr(workflow, 'state')
        assert hasattr(workflow, 'steps')
        assert hasattr(workflow, 'context')
        assert hasattr(workflow, 'created_at')

    async def test_consolidate_results_empty(self, mock_env):
        """Testa consolidação de resultados vazios"""
        orch = Orchestrator()

        consolidated = orch._consolidate_results(None, [])

        assert consolidated is not None
        assert "leader" in consolidated
        assert "assistant" in consolidated
        assert "source" in consolidated

    async def test_consolidate_results_with_data(self, mock_env):
        """Testa consolidação de resultados com dados"""
        orch = Orchestrator()

        leader_result = {"data": "leader"}
        supporter_results = [
            {"data": "supporter1"},
            {"data": "supporter2"}
        ]

        consolidated = orch._consolidate_results(leader_result, supporter_results)

        assert consolidated is not None
        assert consolidated["leader"] == leader_result
        assert len(consolidated["assistant"]) == 2
        assert consolidated["source"] == "collaborative"
