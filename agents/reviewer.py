"""
O Construtor - Reviewer Agent
Agente especializado em code review e análise de qualidade

Usa: Gemini 3 Pro Preview (análise profunda)
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


class ReviewerAgent(BaseAgent):
    """
    Agente Revisor - Especialista em Code Review

    Responsabilidades:
    - Análise de qualidade de código
    - Identificação de bugs e code smells
    - Verificação de padrões e convenções
    - Sugestões de melhorias

    Modelo Primário: Gemini 3 Pro Preview (análise profunda)
    Modelo Secundário: Claude Sonnet 4 (segunda opinião)
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Revisor",
            emoji="🔍",
            capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_ANALYSIS,
                AgentCapability.PERFORMANCE_ANALYSIS,
            ],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return """Você é o Revisor do sistema "O Construtor", especialista em análise de código e garantia de qualidade.

## Sua Identidade
- Nome: Revisor
- Papel: Guardião da qualidade do código
- Modelo: Gemini 3 Pro Preview (análise profunda)

## Suas Responsabilidades
1. **Code Review**
   - Analisar mudanças de código em PRs
   - Identificar bugs, vulnerabilidades, code smells
   - Verificar aderência a padrões do projeto
   - Sugerir melhorias concretas

2. **Análise de Performance**
   - Identificar gargalos de performance
   - Analisar complexidade algorítmica (Big O)
   - Sugerir otimizações

3. **Qualidade Geral**
   - Verificar legibilidade e manutenibilidade
   - Validar tratamento de erros
   - Checar cobertura de edge cases

## Formato de Review
```
## Resumo
[Visão geral das mudanças]

## Pontos Positivos
- [O que está bom]

## Problemas Encontrados
### 🔴 Crítico
- [Problemas que bloqueiam merge]

### 🟡 Médio
- [Problemas importantes mas não bloqueantes]

### 🟢 Menor
- [Sugestões de melhoria]

## Decisão
[APROVAR / SOLICITAR MUDANÇAS / REJEITAR]
```

## Comunicação
- Receba código do Desenvolvedor
- Envie feedback construtivo
- Aprove ou solicite mudanças
- Colabore com Especialista em Segurança para análises críticas
"""

    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """Executa tarefa de revisão"""
        self.status = AgentStatus.WORKING
        self._current_context = context

        logger.info(f"{self.emoji} {self.name} executing: {task_type}")

        try:
            handlers = {
                "code_review": self._review_code,
                "performance_analysis": self._analyze_performance,
                "complexity_analysis": self._analyze_complexity,
                "pr_review": self._review_pr,
            }

            handler = handlers.get(task_type, self._generic_review)
            result = await handler(input_data, context)

            self._stats["tasks_completed"] += 1

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=True,
                content=result,
                suggestions=result.get("suggestions"),
                warnings=result.get("warnings"),
            )

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            self._stats["tasks_failed"] += 1

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

    async def _review_code(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Review de código"""
        code = input_data.get("code", "")

        return {
            "type": "code_review",
            "summary": "",
            "positive_points": [],
            "critical_issues": [],
            "medium_issues": [],
            "minor_issues": [],
            "decision": "PENDING",
            "reasoning": "Code review pendente de implementação com Gemini 3 Pro",
            "suggestions": [],
            "warnings": [],
        }

    async def _analyze_performance(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Análise de performance"""
        return {
            "type": "performance_analysis",
            "bottlenecks": [],
            "complexity_issues": [],
            "memory_issues": [],
            "optimization_suggestions": [],
            "reasoning": "Performance analysis pendente",
            "suggestions": [],
        }

    async def _analyze_complexity(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Análise de complexidade"""
        return {
            "type": "complexity_analysis",
            "cyclomatic_complexity": {},
            "cognitive_complexity": {},
            "recommendations": [],
            "reasoning": "Complexity analysis pendente",
            "suggestions": [],
        }

    async def _review_pr(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Review de Pull Request"""
        pr_data = input_data.get("pr_data", {})

        return {
            "type": "pr_review",
            "pr_number": pr_data.get("number"),
            "files_reviewed": [],
            "comments": [],
            "approval_status": "PENDING",
            "reasoning": "PR review pendente",
            "suggestions": [],
        }

    async def _generic_review(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Review genérico"""
        return {
            "type": "generic_review",
            "reasoning": "Task type não específico",
            "suggestions": [],
        }
