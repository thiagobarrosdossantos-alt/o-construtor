"""
O Construtor - Tester Agent
Agente especializado em testes automatizados

Usa: Gemini 2.5 Flash (velocidade) + Claude Code (execução)
"""

import logging
from typing import Any, Dict, List, Optional

from agents.base_agent import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentResponse,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class TesterAgent(BaseAgent):
    """
    Agente Tester - Especialista em Testes

    Responsabilidades:
    - Geração de testes unitários
    - Criação de testes de integração
    - Testes E2E
    - Análise de cobertura

    Modelo Primário: Gemini 2.5 Flash (velocidade para gerar muitos testes)
    Modelo Secundário: Claude Code (execução de testes)
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Tester",
            emoji="🧪",
            capabilities=[
                AgentCapability.TESTING,
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_EXECUTION,
            ],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return """Você é o Tester do sistema "O Construtor", especialista em garantia de qualidade através de testes.

## Sua Identidade
- Nome: Tester
- Papel: Garantir qualidade através de testes abrangentes
- Modelo: Gemini 2.5 Flash (velocidade para alta throughput)

## Suas Responsabilidades
1. **Testes Unitários**
   - Gerar testes para cada função/método
   - Cobrir happy paths e edge cases
   - Testar tratamento de erros

2. **Testes de Integração**
   - Testar interações entre componentes
   - Validar fluxos de dados
   - Testar APIs

3. **Testes E2E**
   - Simular fluxos de usuário
   - Testar cenários completos
   - Validar requisitos de negócio

4. **Cobertura**
   - Analisar cobertura atual
   - Identificar código não testado
   - Recomendar testes adicionais

## Formato de Teste (Python/Pytest)
```python
import pytest

class TestClassName:
    \"\"\"Testes para ClassName\"\"\"

    def test_should_do_something_when_condition(self):
        \"\"\"Descrição do comportamento esperado\"\"\"
        # Arrange
        # Act
        # Assert
```

## Princípios
- Um assert por teste quando possível
- Testes independentes e isolados
- Nomes descritivos (test_should_X_when_Y)
- AAA pattern (Arrange, Act, Assert)
"""

    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """Executa tarefa de teste"""
        self.status = AgentStatus.WORKING

        logger.info(f"{self.emoji} {self.name} executing: {task_type}")

        try:
            handlers = {
                "unit_test_generation": self._generate_unit_tests,
                "integration_test": self._generate_integration_tests,
                "e2e_test": self._generate_e2e_tests,
                "test_review": self._review_tests,
                "coverage_analysis": self._analyze_coverage,
            }

            handler = handlers.get(task_type, self._generic_test)
            result = await handler(input_data, context)

            self._stats["tasks_completed"] += 1

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=True,
                content=result,
                code_changes=result.get("test_files"),
            )

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=False,
                content=None,
                errors=[str(e)],
            )

        finally:
            self.status = AgentStatus.IDLE

    async def _generate_unit_tests(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Gera testes unitários"""
        return {
            "type": "unit_tests",
            "test_files": [],
            "test_count": 0,
            "coverage_estimate": 0,
            "reasoning": "Geração de testes pendente",
        }

    async def _generate_integration_tests(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Gera testes de integração"""
        return {
            "type": "integration_tests",
            "test_files": [],
            "scenarios_covered": [],
            "reasoning": "Geração de testes de integração pendente",
        }

    async def _generate_e2e_tests(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Gera testes E2E"""
        return {
            "type": "e2e_tests",
            "test_files": [],
            "user_flows_covered": [],
            "reasoning": "Geração de testes E2E pendente",
        }

    async def _review_tests(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Review de testes existentes"""
        return {
            "type": "test_review",
            "quality_score": 0,
            "issues": [],
            "suggestions": [],
            "reasoning": "Review de testes pendente",
        }

    async def _analyze_coverage(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Análise de cobertura"""
        return {
            "type": "coverage_analysis",
            "total_coverage": 0,
            "uncovered_areas": [],
            "recommendations": [],
            "reasoning": "Análise de cobertura pendente",
        }

    async def _generic_test(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Teste genérico"""
        return {
            "type": "generic_test",
            "reasoning": "Task type não específico",
        }
