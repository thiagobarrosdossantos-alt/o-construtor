"""
O Construtor - Architect Agent
Agente especializado em arquitetura e design de sistemas

Usa: Claude Opus 4.5 (raciocínio profundo)
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


class ArchitectAgent(BaseAgent):
    """
    Agente Arquiteto - Especialista em Design de Sistemas

    Responsabilidades:
    - Design de arquitetura de software
    - Decisões de alto nível (padrões, tecnologias)
    - Análise de trade-offs
    - Definição de interfaces e contratos
    - Planejamento de refatorações

    Modelo Primário: Claude Opus 4.5 (melhor em raciocínio profundo)
    Modelo Secundário: Gemini 3 Pro Preview (validação)
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Arquiteto",
            emoji="🏛️",
            capabilities=[
                AgentCapability.ARCHITECTURE,
                AgentCapability.CODE_REVIEW,
                AgentCapability.DOCUMENTATION,
            ],
            **kwargs,
        )

        self._system_prompt = self.get_system_prompt()

    def get_system_prompt(self) -> str:
        return """Você é o Arquiteto do sistema "O Construtor", um especialista em design de software e arquitetura de sistemas.

## Sua Identidade
- Nome: Arquiteto
- Papel: Líder técnico em decisões arquiteturais
- Modelo: Claude Opus 4.5 (raciocínio profundo)

## Suas Responsabilidades
1. **Design de Arquitetura**
   - Definir estrutura de alto nível dos sistemas
   - Escolher padrões arquiteturais apropriados
   - Projetar interfaces entre componentes

2. **Análise de Trade-offs**
   - Avaliar prós e contras de diferentes abordagens
   - Considerar escalabilidade, manutenibilidade, performance
   - Documentar decisões com justificativas

3. **Princípios de Design**
   - Aplicar SOLID, DRY, KISS, YAGNI
   - Garantir separation of concerns
   - Promover código testável e modular

4. **Revisão Técnica**
   - Validar que implementações seguem a arquitetura
   - Identificar desvios e propor correções
   - Mentorear outros agentes em boas práticas

## Formato de Resposta
Sempre estruture suas análises em:
1. **Contexto**: Entendimento do problema
2. **Análise**: Opções consideradas
3. **Decisão**: Recomendação escolhida
4. **Justificativa**: Por que esta abordagem
5. **Próximos Passos**: O que deve ser feito

## Comunicação com Outros Agentes
- Após definir arquitetura, faça handoff para o Desenvolvedor
- Peça validação do Revisor para decisões complexas
- Consulte o Especialista em Segurança para sistemas críticos

## Princípios
- Simplicidade sobre complexidade
- Evolução incremental sobre big bang
- Decisões reversíveis quando possível
- Documentação clara de trade-offs
"""

    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        Executa uma tarefa arquitetural.

        Task types suportados:
        - system_design: Design de novo sistema
        - architecture_review: Revisão de arquitetura existente
        - api_design: Design de API
        - database_design: Design de banco de dados
        - refactoring_plan: Plano de refatoração
        """
        self.status = AgentStatus.WORKING
        self._current_context = context

        logger.info(f"{self.emoji} {self.name} executing: {task_type}")

        try:
            # Roteia para método específico
            handlers = {
                "system_design": self._design_system,
                "architecture_review": self._review_architecture,
                "api_design": self._design_api,
                "database_design": self._design_database,
                "refactoring_plan": self._plan_refactoring,
            }

            handler = handlers.get(task_type, self._generic_analysis)
            result = await handler(input_data, context)

            self._stats["tasks_completed"] += 1

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=True,
                content=result,
                reasoning=result.get("reasoning"),
                suggestions=result.get("suggestions"),
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
            self._current_context = None

    async def _design_system(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Design de novo sistema"""
        requirement = input_data.get("requirement", {})

        # Estrutura do design
        design = {
            "type": "system_design",
            "title": requirement.get("title", "New System"),
            "description": requirement.get("description", ""),
            "components": [],
            "interfaces": [],
            "data_flow": [],
            "technology_stack": [],
            "patterns": [],
            "considerations": {
                "scalability": [],
                "security": [],
                "performance": [],
                "maintainability": [],
            },
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar chamada real ao Claude Opus
        # Por enquanto, estrutura placeholder
        design["reasoning"] = "Análise arquitetural pendente de implementação do modelo"
        design["suggestions"] = [
            "Implementar chamada ao Claude Opus 4.5",
            "Adicionar análise de requisitos",
            "Gerar diagrama de componentes",
        ]

        return design

    async def _review_architecture(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Revisão de arquitetura existente"""
        code_context = input_data.get("code_context", "")

        review = {
            "type": "architecture_review",
            "findings": [],
            "violations": [],
            "improvements": [],
            "patterns_identified": [],
            "patterns_recommended": [],
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar análise real
        review["reasoning"] = "Revisão arquitetural pendente de implementação"

        return review

    async def _design_api(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Design de API"""
        return {
            "type": "api_design",
            "endpoints": [],
            "schemas": [],
            "authentication": {},
            "versioning": {},
            "reasoning": "API design pendente de implementação",
            "suggestions": [],
        }

    async def _design_database(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Design de banco de dados"""
        return {
            "type": "database_design",
            "entities": [],
            "relationships": [],
            "indexes": [],
            "migrations": [],
            "reasoning": "Database design pendente de implementação",
            "suggestions": [],
        }

    async def _plan_refactoring(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Plano de refatoração"""
        return {
            "type": "refactoring_plan",
            "current_issues": [],
            "target_architecture": {},
            "steps": [],
            "risks": [],
            "estimated_effort": "",
            "reasoning": "Refactoring plan pendente de implementação",
            "suggestions": [],
        }

    async def _generic_analysis(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Análise genérica para tasks não mapeados"""
        return {
            "type": "generic_analysis",
            "input_received": input_data,
            "reasoning": "Análise genérica - task type não específico",
            "suggestions": ["Especificar task type para análise mais precisa"],
        }
