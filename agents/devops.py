"""
O Construtor - DevOps Agent (Jules)
Agente especializado em CI/CD, infraestrutura e deploy

Usa: Gemini 2.5 Pro
"""

import logging
from typing import Any, Dict, Optional

from agents.base_agent import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentResponse,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class DevOpsAgent(BaseAgent):
    """
    Agente DevOps (Jules) - Especialista em Infraestrutura

    Responsabilidades:
    - Configuração de CI/CD
    - Docker e containerização
    - Kubernetes e orquestração
    - Deploy e releases

    Modelo Primário: Gemini 2.5 Pro
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Jules (DevOps)",
            emoji="🚀",
            capabilities=[
                AgentCapability.DEVOPS,
                AgentCapability.CODE_GENERATION,
                AgentCapability.FILE_MANIPULATION,
            ],
            **kwargs,
        )

    def get_system_prompt(self) -> str:
        return """Você é Jules, o DevOps do sistema "O Construtor", especialista em infraestrutura e automação.

## Sua Identidade
- Nome: Jules
- Papel: Especialista em DevOps e SRE
- Modelo: Gemini 2.5 Pro

## Suas Responsabilidades
1. **CI/CD**
   - Configurar pipelines de build e deploy
   - Otimizar tempo de build
   - Implementar quality gates

2. **Containerização**
   - Criar Dockerfiles otimizados
   - Configurar docker-compose
   - Multi-stage builds

3. **Orquestração**
   - Kubernetes manifests
   - Helm charts
   - Service mesh

4. **Deploy**
   - Estratégias de deploy (blue/green, canary)
   - Rollback automático
   - Monitoramento

## Princípios
- Infrastructure as Code
- Immutable infrastructure
- GitOps workflow
- Security by default
"""

    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """Executa tarefa de DevOps"""
        self.status = AgentStatus.WORKING

        logger.info(f"{self.emoji} {self.name} executing: {task_type}")

        try:
            handlers = {
                "ci_cd_config": self._configure_ci_cd,
                "docker_config": self._configure_docker,
                "kubernetes_config": self._configure_kubernetes,
                "infrastructure": self._configure_infrastructure,
                "deploy": self._deploy,
            }

            handler = handlers.get(task_type, self._generic_devops)
            result = await handler(input_data, context)

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=True,
                content=result,
                code_changes=result.get("config_files"),
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

    async def _configure_ci_cd(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "ci_cd_config", "config_files": [], "reasoning": "CI/CD config pendente"}

    async def _configure_docker(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "docker_config", "dockerfile": "", "docker_compose": "", "reasoning": "Docker config pendente"}

    async def _configure_kubernetes(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "kubernetes_config", "manifests": [], "reasoning": "K8s config pendente"}

    async def _configure_infrastructure(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "infrastructure", "terraform": "", "reasoning": "Infra config pendente"}

    async def _deploy(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "deploy", "status": "pending", "reasoning": "Deploy pendente"}

    async def _generic_devops(self, input_data: Dict, context: Optional[AgentContext]) -> Dict:
        return {"type": "generic_devops", "reasoning": "Task type não específico"}
