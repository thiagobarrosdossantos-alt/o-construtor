"""
O Construtor - Orchestrator (Cérebro Central)
Sistema de orquestração que coordena todos os agentes de IA

Este é o componente mais importante do sistema:
- Recebe tarefas e distribui para os agentes apropriados
- Gerencia o fluxo de trabalho entre agentes
- Consolida resultados e gerencia feedback loops
- Mantém contexto compartilhado entre agentes
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from uuid import uuid4

# API Clients
import anthropic
from openai import OpenAI
import google.generativeai as genai

from config.settings import get_settings
from config.models import (
    TaskType,
    ModelConfig,
    AGENT_CONFIGS,
    TASK_MODEL_MAPPING,
    COLLABORATION_STRATEGY,
    get_model_for_task as get_model_for_task_legacy,
)
from config.teams import (
    get_model_for_task as get_team_model_selection,
    estimate_task_complexity,
    AGENT_TO_TEAM,
)

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Estados do fluxo de trabalho"""
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    TESTING = "testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(Enum):
    """Papéis dos agentes no sistema"""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DEVOPS = "devops"
    DOCUMENTER = "documenter"
    SECURITY = "security"
    OPTIMIZER = "optimizer"


@dataclass
class WorkflowStep:
    """Um passo no fluxo de trabalho"""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_role: AgentRole = AgentRole.DEVELOPER
    task_type: TaskType = TaskType.CODE_IMPLEMENTATION
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: WorkflowState = WorkflowState.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class Workflow:
    """Representa um fluxo de trabalho completo"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    state: WorkflowState = WorkflowState.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    initiator: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """
    Cérebro Central do O Construtor

    Responsável por:
    1. Receber requisições (issues, PRs, comandos do chat)
    2. Planejar o fluxo de trabalho
    3. Distribuir tarefas para agentes
    4. Coordenar comunicação entre agentes
    5. Consolidar resultados
    6. Gerenciar erros e retries
    """

    def __init__(
        self,
        memory_store: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        task_queue: Optional[Any] = None,
    ):
        self.settings = get_settings()
        self.model_config = ModelConfig()
        self.memory_store = memory_store
        self.event_bus = event_bus
        self.task_queue = task_queue

        self.active_workflows: Dict[str, Workflow] = {}
        self.agents: Dict[AgentRole, Any] = {}
        self._initialized = False

        # API IMPLEMENTATION: Inicializar clientes reais das APIs
        self._init_api_clients()

        logger.info("Orchestrator initialized")

    def _init_api_clients(self):
        """Inicializa clientes das APIs de IA"""
        # Anthropic (Claude)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None

        # OpenAI (GPT)
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None

        # Google (Gemini)
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            genai.configure(api_key=google_key)
            self.gemini_available = True
        else:
            self.gemini_available = False

        logger.info(f"API Clients initialized - Claude: {bool(self.anthropic_client)}, "
                    f"GPT: {bool(self.openai_client)}, Gemini: {self.gemini_available}")

    async def initialize(self):
        """Inicializa o orquestrador e seus componentes"""
        if self._initialized:
            return

        logger.info("Initializing Orchestrator components...")

        # Inicializa agentes
        for role in AgentRole:
            agent_config = AGENT_CONFIGS.get(role.value)
            if agent_config:
                self.agents[role] = {
                    "config": agent_config,
                    "status": "ready",
                    "current_task": None,
                }
                logger.info(f"Agent {agent_config.name} ({agent_config.emoji}) ready")

        self._initialized = True
        logger.info("Orchestrator fully initialized")

    # ============================================================
    # WORKFLOW TEMPLATES
    # ============================================================

    def _create_feature_workflow(self, request: Dict[str, Any]) -> Workflow:
        """Cria workflow para desenvolvimento de feature"""
        return Workflow(
            name=f"Feature: {request.get('title', 'New Feature')}",
            description=request.get("description", ""),
            context={"request": request},
            steps=[
                WorkflowStep(
                    agent_role=AgentRole.ARCHITECT,
                    task_type=TaskType.SYSTEM_DESIGN,
                    input_data={"requirement": request},
                ),
                WorkflowStep(
                    agent_role=AgentRole.DEVELOPER,
                    task_type=TaskType.CODE_IMPLEMENTATION,
                    input_data={},  # Preenchido com output do arquiteto
                ),
                WorkflowStep(
                    agent_role=AgentRole.REVIEWER,
                    task_type=TaskType.CODE_REVIEW,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.TESTER,
                    task_type=TaskType.UNIT_TEST_GENERATION,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.SECURITY,
                    task_type=TaskType.SECURITY_ANALYSIS,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.DOCUMENTER,
                    task_type=TaskType.DOCUMENTATION,
                    input_data={},
                ),
            ],
        )

    def _create_bugfix_workflow(self, request: Dict[str, Any]) -> Workflow:
        """Cria workflow para correção de bug"""
        return Workflow(
            name=f"Bugfix: {request.get('title', 'Bug Fix')}",
            description=request.get("description", ""),
            context={"request": request},
            steps=[
                WorkflowStep(
                    agent_role=AgentRole.DEVELOPER,
                    task_type=TaskType.BUG_FIX,
                    input_data={"bug_report": request},
                ),
                WorkflowStep(
                    agent_role=AgentRole.REVIEWER,
                    task_type=TaskType.CODE_REVIEW,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.TESTER,
                    task_type=TaskType.UNIT_TEST_GENERATION,
                    input_data={},
                ),
            ],
        )

    def _create_review_workflow(self, request: Dict[str, Any]) -> Workflow:
        """Cria workflow para review de PR"""
        return Workflow(
            name=f"Review: PR #{request.get('pr_number', 'N/A')}",
            description=request.get("description", ""),
            context={"request": request},
            steps=[
                WorkflowStep(
                    agent_role=AgentRole.REVIEWER,
                    task_type=TaskType.CODE_REVIEW,
                    input_data={"pr_data": request},
                ),
                WorkflowStep(
                    agent_role=AgentRole.OPTIMIZER,
                    task_type=TaskType.PERFORMANCE_ANALYSIS,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.SECURITY,
                    task_type=TaskType.SECURITY_ANALYSIS,
                    input_data={},
                ),
            ],
        )

    def _create_refactor_workflow(self, request: Dict[str, Any]) -> Workflow:
        """Cria workflow para refatoração"""
        return Workflow(
            name=f"Refactor: {request.get('title', 'Code Refactoring')}",
            description=request.get("description", ""),
            context={"request": request},
            steps=[
                WorkflowStep(
                    agent_role=AgentRole.ARCHITECT,
                    task_type=TaskType.ARCHITECTURE,
                    input_data={"current_code": request.get("files", [])},
                ),
                WorkflowStep(
                    agent_role=AgentRole.OPTIMIZER,
                    task_type=TaskType.PERFORMANCE_ANALYSIS,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.DEVELOPER,
                    task_type=TaskType.REFACTORING,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.REVIEWER,
                    task_type=TaskType.CODE_REVIEW,
                    input_data={},
                ),
                WorkflowStep(
                    agent_role=AgentRole.TESTER,
                    task_type=TaskType.UNIT_TEST_GENERATION,
                    input_data={},
                ),
            ],
        )

    # ============================================================
    # CORE ORCHESTRATION METHODS
    # ============================================================

    async def process_request(
        self,
        request_type: str,
        request_data: Dict[str, Any],
        priority: str = "normal",
    ) -> Workflow:
        """
        Processa uma requisição criando e executando um workflow.

        Args:
            request_type: Tipo da requisição (feature, bugfix, review, refactor)
            request_data: Dados da requisição
            priority: Prioridade (low, normal, high, critical)

        Returns:
            Workflow criado e em execução
        """
        await self.initialize()

        logger.info(f"Processing request: {request_type} with priority {priority}")

        # Cria workflow baseado no tipo
        workflow_creators = {
            "feature": self._create_feature_workflow,
            "bugfix": self._create_bugfix_workflow,
            "review": self._create_review_workflow,
            "refactor": self._create_refactor_workflow,
        }

        creator = workflow_creators.get(request_type, self._create_feature_workflow)
        workflow = creator(request_data)
        workflow.metadata["priority"] = priority

        # Registra workflow
        self.active_workflows[workflow.id] = workflow

        # Salva na memória se disponível
        if self.memory_store:
            await self.memory_store.save_workflow(workflow)

        # Emite evento se event bus disponível
        if self.event_bus:
            await self.event_bus.emit(
                "workflow.created",
                {"workflow_id": workflow.id, "type": request_type},
            )

        # Inicia execução
        asyncio.create_task(self._execute_workflow(workflow))

        return workflow

    async def _execute_workflow(self, workflow: Workflow):
        """
        Executa um workflow passo a passo.

        Args:
            workflow: Workflow a ser executado
        """
        workflow.state = WorkflowState.IN_PROGRESS
        workflow.updated_at = datetime.now()

        logger.info(f"Starting workflow execution: {workflow.name}")

        try:
            for i, step in enumerate(workflow.steps):
                # Atualiza estado do passo
                step.status = WorkflowState.IN_PROGRESS
                step.started_at = datetime.now()

                # Obter valores de forma segura
                agent_role_value = step.agent_role.value if hasattr(step.agent_role, 'value') else str(step.agent_role)
                task_type_value = step.task_type.value if hasattr(step.task_type, 'value') else str(step.task_type)

                logger.info(
                    f"Executing step {i + 1}/{len(workflow.steps)}: "
                    f"{agent_role_value} - {task_type_value}"
                )

                # Prepara input com contexto acumulado
                if i > 0:
                    previous_step = workflow.steps[i - 1]
                    step.input_data["previous_output"] = previous_step.output_data
                    step.input_data["workflow_context"] = workflow.context

                # Executa o passo
                try:
                    result = await self._execute_step(step, workflow)
                    step.output_data = result
                    step.status = WorkflowState.COMPLETED
                    step.completed_at = datetime.now()

                    # Atualiza contexto do workflow
                    workflow.context[f"step_{i}_result"] = result

                    logger.info(f"Step {i + 1} completed successfully")

                except Exception as e:
                    logger.error(f"Step {i + 1} failed: {e}")
                    step.error = str(e)
                    step.retry_count += 1

                    # Tenta retry se ainda tem tentativas
                    if step.retry_count < step.max_retries:
                        logger.info(f"Retrying step {i + 1} ({step.retry_count}/{step.max_retries})")
                        await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                        continue
                    else:
                        step.status = WorkflowState.FAILED
                        workflow.state = WorkflowState.FAILED
                        break

            # Finaliza workflow
            if workflow.state != WorkflowState.FAILED:
                workflow.state = WorkflowState.COMPLETED
                workflow.completed_at = datetime.now()
                logger.info(f"Workflow completed: {workflow.name}")

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            workflow.state = WorkflowState.FAILED

        finally:
            workflow.updated_at = datetime.now()

            # Emite evento de conclusão
            if self.event_bus:
                await self.event_bus.emit(
                    "workflow.completed" if workflow.state == WorkflowState.COMPLETED else "workflow.failed",
                    {"workflow_id": workflow.id, "state": workflow.state.value},
                )

    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow,
    ) -> Dict[str, Any]:
        """
        Executa um passo individual do workflow com seleção inteligente de modelo.

        NOVO: Usa sistema de equipes estratégicas para selecionar o modelo
        mais apropriado baseado no agente e complexidade da tarefa.

        Args:
            step: Passo a ser executado
            workflow: Workflow pai

        Returns:
            Resultado da execução do passo
        """
        # Obtém valores de forma segura
        agent_role_str = step.agent_role.value if hasattr(step.agent_role, 'value') else str(step.agent_role)
        task_type_str = step.task_type.value if hasattr(step.task_type, 'value') else str(step.task_type)

        # Obtém configuração do agente
        agent_config = AGENT_CONFIGS.get(agent_role_str)
        if not agent_config:
            raise ValueError(f"Agent config not found for role: {step.agent_role}")

        # === NOVA LÓGICA: SELEÇÃO INTELIGENTE COM EQUIPES ===

        # 1. Estima complexidade da tarefa
        task_description = step.input_data.get("description", "")
        if not task_description and workflow.description:
            task_description = workflow.description

        complexity = estimate_task_complexity(
            task_type=task_type_str,
            task_description=task_description
        )

        # 2. Obtém modelo apropriado da equipe do agente
        model_name = get_team_model_selection(
            agent=agent_role_str,
            task_complexity=complexity
        )

        # 3. Converte nome do modelo para ModelSpec
        model_spec = getattr(self.model_config, model_name, None)
        if not model_spec:
            # Fallback para sistema legado se modelo não encontrado
            logger.warning(f"Model {model_name} not found, using legacy selection")
            models = get_model_for_task_legacy(step.task_type)
            model_spec = models[0] if models else None

        if not model_spec:
            raise ValueError(f"No model found for task: {step.task_type}")

        # Log detalhado da seleção
        team = AGENT_TO_TEAM.get(step.agent_role.value, "unknown")
        team_name = team.value if hasattr(team, 'value') else str(team)
        logger.info(
            f"Agent: {agent_config.name} ({agent_config.emoji}) | "
            f"Team: {team_name} | "
            f"Complexity: {complexity} | "
            f"Model: {model_spec.name}"
        )

        # Verifica se é tarefa colaborativa (Claude Code + Gemini Code Assist)
        collaboration = self._get_collaboration_strategy(step.task_type)
        if collaboration:
            return await self._execute_collaborative_step(step, collaboration, workflow)

        # Execução simples com um modelo
        return await self._call_agent(
            agent_config=agent_config,
            model=model_spec,
            task_type=step.task_type,
            input_data=step.input_data,
            context=workflow.context,
        )

    def _get_collaboration_strategy(self, task_type: TaskType) -> Optional[Dict]:
        """Verifica se a tarefa requer colaboração entre agentes"""
        task_collaboration_map = {
            TaskType.CODE_IMPLEMENTATION: "implementation",
            TaskType.BUG_FIX: "debugging",
            TaskType.REFACTORING: "refactoring",
            TaskType.CODE_REVIEW: "review",
        }

        strategy_key = task_collaboration_map.get(task_type)
        if strategy_key:
            return COLLABORATION_STRATEGY.get(strategy_key)
        return None

    async def _execute_collaborative_step(
        self,
        step: WorkflowStep,
        collaboration: Dict,
        workflow: Workflow,
    ) -> Dict[str, Any]:
        """
        Executa um passo colaborativo onde múltiplos agentes trabalham juntos.

        Args:
            step: Passo a ser executado
            collaboration: Estratégia de colaboração
            workflow: Workflow pai

        Returns:
            Resultado consolidado da colaboração
        """
        logger.info(f"Executing collaborative step with strategy: {collaboration}")

        leader_model_name = collaboration.get("leader", "CLAUDE_CODE")
        assistant_model_name = collaboration.get("assistant", "GEMINI_CODE_ASSIST")

        # Obtém modelos
        leader_model = getattr(self.model_config, leader_model_name, None)
        assistant_model = getattr(self.model_config, assistant_model_name, None)

        results = {
            "leader_result": None,
            "assistant_result": None,
            "consolidated": None,
            "collaboration_workflow": collaboration.get("workflow", []),
        }

        # Executa líder primeiro
        if leader_model:
            logger.info(f"Leader ({leader_model_name}) starting...")
            results["leader_result"] = await self._call_model(
                model=leader_model,
                task_type=step.task_type,
                input_data=step.input_data,
                context=workflow.context,
            )

        # Executa assistente com contexto do líder
        if assistant_model:
            logger.info(f"Assistant ({assistant_model_name}) reviewing...")
            assistant_input = {
                **step.input_data,
                "leader_output": results["leader_result"],
            }
            results["assistant_result"] = await self._call_model(
                model=assistant_model,
                task_type=step.task_type,
                input_data=assistant_input,
                context=workflow.context,
            )

        # Consolida resultados
        results["consolidated"] = self._consolidate_results(
            results["leader_result"],
            results["assistant_result"],
        )

        return results

    async def _call_agent(
        self,
        agent_config: Any,
        model: Any,
        task_type: TaskType,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Chama um agente específico para executar uma tarefa via API real.

        API IMPLEMENTATION: Conectado aos clients reais (Anthropic, OpenAI, Google)
        """
        # Obter valor de forma segura
        task_type_str = task_type.value if hasattr(task_type, 'value') else str(task_type)

        logger.info(f"Calling agent {agent_config.name} with model {model.name}")

        # Construir prompt baseado no agente e tarefa
        prompt = self._build_prompt(agent_config, task_type_str, input_data, context)

        # Chamar API real baseado no provider do modelo
        try:
            result = await self._call_model(model, prompt)
            return {
                "agent": agent_config.name,
                "model": model.name,
                "task": task_type_str,
                "status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calling {model.name}: {e}")
            return {
                "agent": agent_config.name,
                "model": model.name,
                "task": task_type_str,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _call_model(self, model: Any, prompt: str) -> str:
        """
        Chama um modelo específico via API real.

        API IMPLEMENTATION: Conectado aos providers reais (Anthropic, OpenAI, Google)
        """
        model_name = model.name.lower()

        # Claude (Anthropic)
        if "claude" in model_name:
            if not self.anthropic_client:
                raise Exception("Anthropic API key not configured")

            response = self.anthropic_client.messages.create(
                model=model.name,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        # GPT (OpenAI)
        elif "gpt" in model_name:
            if not self.openai_client:
                raise Exception("OpenAI API key not configured")

            response = self.openai_client.chat.completions.create(
                model=model.name,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "You are an expert software engineering AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        # Gemini (Google)
        elif "gemini" in model_name:
            if not self.gemini_available:
                raise Exception("Google API key not configured")

            gemini_model = genai.GenerativeModel(model.name)
            response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.7,
                )
            )
            return response.text

        else:
            raise Exception(f"Unknown model provider for: {model.name}")

    def _build_prompt(
        self,
        agent_config: Any,
        task_type: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Constrói o prompt para o modelo baseado no agente e tarefa"""
        # Prompt base com identidade do agente
        prompt = f"""You are {agent_config.name} ({agent_config.emoji}), {agent_config.description}.

Task Type: {task_type}

Input Data:
{self._format_dict(input_data)}

Context:
{self._format_dict(context)}

Please analyze the task and provide a comprehensive response following best practices for {task_type}.
Focus on quality, security, performance, and maintainability."""

        return prompt

    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Formata dicionário para exibição no prompt"""
        lines = []
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: {', '.join(str(v) for v in value[:5])}")
            else:
                # Limitar tamanho de strings longas
                str_value = str(value)
                if len(str_value) > 200:
                    str_value = str_value[:200] + "..."
                lines.append(f"{prefix}{key}: {str_value}")
        return "\n".join(lines)

    def _consolidate_results(
        self,
        leader_result: Optional[Dict],
        assistant_result: Optional[Dict],
    ) -> Dict[str, Any]:
        """Consolida resultados de múltiplos agentes"""
        return {
            "source": "collaborative",
            "leader": leader_result,
            "assistant": assistant_result,
            "timestamp": datetime.now().isoformat(),
        }

    # ============================================================
    # STATUS AND MONITORING
    # ============================================================

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retorna status de um workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "id": workflow.id,
            "name": workflow.name,
            "state": workflow.state.value,
            "progress": self._calculate_progress(workflow),
            "current_step": self._get_current_step(workflow),
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
        }

    def _calculate_progress(self, workflow: Workflow) -> float:
        """Calcula progresso do workflow em porcentagem"""
        if not workflow.steps:
            return 0.0

        completed = sum(1 for s in workflow.steps if s.status == WorkflowState.COMPLETED)
        return (completed / len(workflow.steps)) * 100

    def _get_current_step(self, workflow: Workflow) -> Optional[Dict]:
        """Retorna o passo atual em execução"""
        for step in workflow.steps:
            if step.status == WorkflowState.IN_PROGRESS:
                # Obter valores de forma segura
                agent_role_str = step.agent_role.value if hasattr(step.agent_role, 'value') else str(step.agent_role)
                task_type_str = step.task_type.value if hasattr(step.task_type, 'value') else str(step.task_type)

                return {
                    "agent": agent_role_str,
                    "task": task_type_str,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                }
        return None

    def get_agent_status(self) -> Dict[str, Any]:
        """Retorna status de todos os agentes"""
        return {
            role.value: {
                "config": self.agents[role]["config"].name if role in self.agents else None,
                "status": self.agents[role]["status"] if role in self.agents else "not_initialized",
                "emoji": self.agents[role]["config"].emoji if role in self.agents else None,
            }
            for role in AgentRole
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancela um workflow em execução"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.state = WorkflowState.CANCELLED
        workflow.updated_at = datetime.now()

        logger.info(f"Workflow cancelled: {workflow_id}")
        return True
