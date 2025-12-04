"""
O Construtor - Base Agent
Classe base para todos os agentes especializados

Define a interface comum e funcionalidades compartilhadas
entre todos os agentes do sistema.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from uuid import uuid4

if TYPE_CHECKING:
    from core.memory_store import MemoryStore
    from core.event_bus import EventBus
    from config.models import ModelSpec, AgentConfig

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Capacidades que um agente pode ter"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_EXECUTION = "code_execution"
    FILE_MANIPULATION = "file_manipulation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DEVOPS = "devops"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"


class AgentStatus(Enum):
    """Status de um agente"""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"  # Aguardando input externo
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentContext:
    """Contexto de execução de um agente"""
    task_id: str
    workflow_id: Optional[str] = None
    project_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    local_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Resposta de um agente"""
    agent_id: str
    agent_name: str
    task_id: str
    success: bool
    content: Any
    reasoning: Optional[str] = None
    code_changes: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "success": self.success,
            "content": self.content,
            "reasoning": self.reasoning,
            "code_changes": self.code_changes,
            "suggestions": self.suggestions,
            "warnings": self.warnings,
            "errors": self.errors,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Classe Base para Agentes do O Construtor

    Todos os agentes especializados herdam desta classe.
    Fornece:
    - Interface comum para execução de tarefas
    - Gerenciamento de estado e contexto
    - Comunicação com outros agentes via EventBus
    - Acesso à memória compartilhada
    - Logging e métricas
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "BaseAgent",
        emoji: str = "🤖",
        capabilities: Optional[List[AgentCapability]] = None,
        primary_model: Optional["ModelSpec"] = None,
        secondary_models: Optional[List["ModelSpec"]] = None,
        memory_store: Optional["MemoryStore"] = None,
        event_bus: Optional["EventBus"] = None,
    ):
        self.id = agent_id or str(uuid4())
        self.name = name
        self.emoji = emoji
        self.capabilities = capabilities or []
        self.primary_model = primary_model
        self.secondary_models = secondary_models or []

        # Componentes externos
        self.memory_store = memory_store
        self.event_bus = event_bus

        # Estado interno
        self.status = AgentStatus.IDLE
        self._current_context: Optional[AgentContext] = None
        self._conversation_history: List[Dict[str, str]] = []

        # Estatísticas
        self._stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0,
        }

        # System prompt base (sobrescrito por subclasses)
        self._system_prompt: str = ""

        logger.info(f"Agent initialized: {self.emoji} {self.name} (ID: {self.id})")

    # ============================================================
    # ABSTRACT METHODS (Devem ser implementados por subclasses)
    # ============================================================

    @abstractmethod
    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        Executa uma tarefa específica.

        Args:
            task_type: Tipo da tarefa
            input_data: Dados de entrada
            context: Contexto de execução

        Returns:
            AgentResponse com resultado
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Retorna o system prompt do agente.

        Returns:
            String com o system prompt
        """
        pass

    # ============================================================
    # COMMON METHODS
    # ============================================================

    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_secondary: bool = False,
    ) -> str:
        """
        Faz o agente "pensar" sobre um prompt.

        Args:
            prompt: Prompt para o modelo
            context: Contexto adicional
            use_secondary: Se deve usar modelo secundário

        Returns:
            Resposta do modelo
        """
        self.status = AgentStatus.THINKING

        model = self.secondary_models[0] if use_secondary and self.secondary_models else self.primary_model
        if not model:
            raise ValueError(f"No model configured for agent {self.name}")

        # Emite evento de pensamento
        if self.event_bus:
            await self.event_bus.emit(
                event_type="agent.thinking",
                payload={
                    "agent_id": self.id,
                    "agent_name": self.name,
                    "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                },
                source=self.id,
            )

        # TODO: Implementar chamada real ao modelo
        # Por enquanto, placeholder
        response = f"[{self.name}] Thinking about: {prompt[:50]}..."

        self.status = AgentStatus.IDLE
        return response

    async def collaborate_with(
        self,
        other_agent_id: str,
        message: Dict[str, Any],
        wait_for_response: bool = True,
        timeout: float = 60.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Inicia colaboração com outro agente.

        Args:
            other_agent_id: ID do outro agente
            message: Mensagem/dados a enviar
            wait_for_response: Se deve aguardar resposta
            timeout: Timeout em segundos

        Returns:
            Resposta do outro agente ou None
        """
        if not self.event_bus:
            logger.warning("No event bus configured, cannot collaborate")
            return None

        # Envia mensagem
        await self.event_bus.send_to_agent(
            from_agent=self.id,
            to_agent=other_agent_id,
            message=message,
        )

        if not wait_for_response:
            return None

        # Aguarda resposta (implementação simplificada)
        # TODO: Implementar mecanismo de resposta real
        self.status = AgentStatus.WAITING
        await asyncio.sleep(0.1)  # Placeholder
        self.status = AgentStatus.IDLE

        return None

    async def handoff_to(
        self,
        other_agent_id: str,
        task_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """
        Faz handoff de tarefa para outro agente.

        Args:
            other_agent_id: ID do agente destino
            task_data: Dados da tarefa
            context: Contexto a passar
        """
        if not self.event_bus:
            logger.warning("No event bus configured, cannot handoff")
            return

        await self.event_bus.agent_handoff(
            from_agent=self.id,
            to_agent=other_agent_id,
            task_data=task_data,
            context={
                **context,
                "handoff_from": self.id,
                "handoff_from_name": self.name,
            },
        )

    async def remember(
        self,
        key: str,
        content: Any,
        category: str = "agent_memory",
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Armazena algo na memória.

        Args:
            key: Chave da memória
            content: Conteúdo a armazenar
            category: Categoria
            ttl_seconds: Tempo de vida
        """
        if not self.memory_store:
            logger.warning("No memory store configured")
            return

        await self.memory_store.store_agent_memory(
            agent_id=self.id,
            key=key,
            content=content,
        )

    async def recall(
        self,
        key: str,
    ) -> Optional[Any]:
        """
        Recupera algo da memória.

        Args:
            key: Chave da memória

        Returns:
            Conteúdo ou None
        """
        if not self.memory_store:
            return None

        return await self.memory_store.get_agent_memory(
            agent_id=self.id,
            key=key,
        )

    def add_to_conversation(
        self,
        role: str,
        content: str,
    ) -> None:
        """
        Adiciona mensagem ao histórico de conversação.

        Args:
            role: Papel (user, assistant, system)
            content: Conteúdo da mensagem
        """
        self._conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def clear_conversation(self) -> None:
        """Limpa histórico de conversação"""
        self._conversation_history.clear()

    def has_capability(self, capability: AgentCapability) -> bool:
        """
        Verifica se agente tem uma capacidade.

        Args:
            capability: Capacidade a verificar

        Returns:
            True se tem a capacidade
        """
        return capability in self.capabilities

    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do agente"""
        return {
            "id": self.id,
            "name": self.name,
            "emoji": self.emoji,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "primary_model": self.primary_model.name if self.primary_model else None,
            "stats": self._stats,
            "current_task": self._current_context.task_id if self._current_context else None,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do agente"""
        return self._stats.copy()

    # ============================================================
    # LIFECYCLE
    # ============================================================

    async def startup(self) -> None:
        """Inicializa o agente"""
        logger.info(f"Starting agent: {self.emoji} {self.name}")
        self.status = AgentStatus.IDLE

        # Carrega memórias persistentes se disponível
        if self.memory_store:
            history = await self.memory_store.get_agent_history(self.id, limit=10)
            logger.debug(f"Loaded {len(history)} memories from store")

    async def shutdown(self) -> None:
        """Desliga o agente gracefully"""
        logger.info(f"Shutting down agent: {self.emoji} {self.name}")

        # Salva estado se necessário
        if self.memory_store and self._conversation_history:
            await self.memory_store.store_agent_memory(
                agent_id=self.id,
                key="last_conversation",
                content=self._conversation_history[-10:],  # Últimas 10 mensagens
            )

        self.status = AgentStatus.OFFLINE

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.emoji} {self.name} ({self.status.value})>"
