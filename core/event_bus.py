"""
O Construtor - Event Bus
Sistema de comunicação assíncrona entre agentes de IA

Este módulo implementa um barramento de eventos que permite:
1. Comunicação desacoplada entre agentes
2. Broadcast de eventos para múltiplos listeners
3. Pub/Sub para coordenação de workflows
4. Rastreamento de eventos para debugging
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from uuid import uuid4
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipos de eventos do sistema"""

    # === WORKFLOW EVENTS ===
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_STEP_FAILED = "workflow.step.failed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"

    # === AGENT EVENTS ===
    AGENT_STARTED = "agent.started"
    AGENT_THINKING = "agent.thinking"
    AGENT_RESPONSE = "agent.response"
    AGENT_ERROR = "agent.error"
    AGENT_COMPLETED = "agent.completed"

    # === COMMUNICATION EVENTS ===
    AGENT_TO_AGENT = "communication.agent_to_agent"
    AGENT_HANDOFF = "communication.handoff"
    AGENT_FEEDBACK = "communication.feedback"
    AGENT_QUESTION = "communication.question"
    AGENT_ANSWER = "communication.answer"

    # === CODE EVENTS ===
    CODE_GENERATED = "code.generated"
    CODE_REVIEWED = "code.reviewed"
    CODE_APPROVED = "code.approved"
    CODE_REJECTED = "code.rejected"
    CODE_MERGED = "code.merged"

    # === TEST EVENTS ===
    TEST_STARTED = "test.started"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"
    TEST_COVERAGE = "test.coverage"

    # === DEPLOYMENT EVENTS ===
    DEPLOY_STARTED = "deploy.started"
    DEPLOY_COMPLETED = "deploy.completed"
    DEPLOY_FAILED = "deploy.failed"
    DEPLOY_ROLLBACK = "deploy.rollback"

    # === SYSTEM EVENTS ===
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"

    # === USER EVENTS ===
    USER_INPUT = "user.input"
    USER_FEEDBACK = "user.feedback"
    USER_APPROVAL = "user.approval"


@dataclass
class Event:
    """Representa um evento no sistema"""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType = EventType.SYSTEM_HEALTH
    source: str = "system"  # ID do agente ou componente que emitiu
    target: Optional[str] = None  # ID do destinatário (None = broadcast)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # Para rastrear eventos relacionados
    parent_event_id: Optional[str] = None  # Para hierarquia de eventos
    priority: int = 5  # 1 (highest) to 10 (lowest)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id,
            "priority": self.priority,
        }

    def to_json(self) -> str:
        """Converte para JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Cria evento a partir de dicionário"""
        data["type"] = EventType(data["type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


# Type alias para handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Barramento de Eventos do O Construtor

    Implementa padrão Pub/Sub para comunicação entre componentes:
    - Agentes podem publicar eventos
    - Componentes podem se inscrever em tipos específicos de eventos
    - Suporta filtros por source e target
    - Mantém histórico de eventos para debugging

    Uso:
        bus = EventBus()

        # Subscrever em eventos
        async def handle_workflow_created(event: Event):
            print(f"Workflow criado: {event.payload}")

        bus.subscribe(EventType.WORKFLOW_CREATED, handle_workflow_created)

        # Emitir evento
        await bus.emit(EventType.WORKFLOW_CREATED, {"workflow_id": "123"})
    """

    def __init__(
        self,
        history_limit: int = 1000,
        enable_persistence: bool = False,
    ):
        # Handlers por tipo de evento
        self._handlers: Dict[EventType, List[EventHandler]] = {}

        # Handlers globais (recebem todos os eventos)
        self._global_handlers: List[EventHandler] = []

        # Handlers por source específico
        self._source_handlers: Dict[str, List[EventHandler]] = {}

        # Handlers por target específico
        self._target_handlers: Dict[str, List[EventHandler]] = {}

        # Histórico de eventos
        self._history: List[Event] = []
        self._history_limit = history_limit

        # Configurações
        self._enable_persistence = enable_persistence

        # Estatísticas
        self._stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_source": {},
        }

        # Lock para operações thread-safe
        self._lock = asyncio.Lock()

        # Fila de eventos para processamento assíncrono
        self._event_queue: asyncio.Queue = asyncio.Queue()

        # Flag para shutdown graceful
        self._running = False

        logger.info("EventBus initialized")

    # ============================================================
    # SUBSCRIPTION METHODS
    # ============================================================

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """
        Inscreve um handler para um tipo de evento.

        Args:
            event_type: Tipo de evento a escutar
            handler: Função async que será chamada
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.value}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Inscreve um handler para todos os eventos (global listener).

        Args:
            handler: Função async que será chamada para todos os eventos
        """
        self._global_handlers.append(handler)
        logger.debug("Global handler subscribed")

    def subscribe_source(
        self,
        source_id: str,
        handler: EventHandler,
    ) -> None:
        """
        Inscreve um handler para eventos de uma source específica.

        Args:
            source_id: ID da source a escutar
            handler: Função async que será chamada
        """
        if source_id not in self._source_handlers:
            self._source_handlers[source_id] = []

        self._source_handlers[source_id].append(handler)
        logger.debug(f"Handler subscribed to source: {source_id}")

    def subscribe_target(
        self,
        target_id: str,
        handler: EventHandler,
    ) -> None:
        """
        Inscreve um handler para eventos direcionados a um target específico.

        Args:
            target_id: ID do target
            handler: Função async que será chamada
        """
        if target_id not in self._target_handlers:
            self._target_handlers[target_id] = []

        self._target_handlers[target_id].append(handler)
        logger.debug(f"Handler subscribed to target: {target_id}")

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """
        Remove inscrição de um handler.

        Args:
            event_type: Tipo de evento
            handler: Handler a remover
        """
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type.value}")

    # ============================================================
    # EMISSION METHODS
    # ============================================================

    async def emit(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        source: str = "system",
        target: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Emite um evento para todos os handlers inscritos.

        Args:
            event_type: Tipo do evento
            payload: Dados do evento
            source: ID da source que emitiu
            target: ID do target (None = broadcast)
            correlation_id: ID para correlação com outros eventos
            priority: Prioridade (1-10)
            metadata: Metadados adicionais

        Returns:
            Evento emitido
        """
        event = Event(
            type=event_type,
            source=source,
            target=target,
            payload=payload,
            correlation_id=correlation_id,
            priority=priority,
            metadata=metadata or {},
        )

        await self._dispatch(event)
        return event

    async def emit_event(self, event: Event) -> None:
        """
        Emite um evento já criado.

        Args:
            event: Evento a emitir
        """
        await self._dispatch(event)

    async def _dispatch(self, event: Event) -> None:
        """
        Despacha um evento para todos os handlers apropriados.

        Args:
            event: Evento a despachar
        """
        async with self._lock:
            # Adiciona ao histórico
            self._history.append(event)
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit:]

            # Atualiza estatísticas
            self._stats["total_events"] += 1
            type_key = event.type.value
            self._stats["events_by_type"][type_key] = self._stats["events_by_type"].get(type_key, 0) + 1
            self._stats["events_by_source"][event.source] = self._stats["events_by_source"].get(event.source, 0) + 1

        logger.debug(f"Dispatching event: {event.type.value} from {event.source}")

        # Coleta todos os handlers que devem receber o evento
        handlers: List[EventHandler] = []

        # Handlers por tipo
        if event.type in self._handlers:
            handlers.extend(self._handlers[event.type])

        # Handlers globais
        handlers.extend(self._global_handlers)

        # Handlers por source
        if event.source in self._source_handlers:
            handlers.extend(self._source_handlers[event.source])

        # Handlers por target
        if event.target and event.target in self._target_handlers:
            handlers.extend(self._target_handlers[event.target])

        # Executa handlers (sem duplicatas)
        unique_handlers = list(set(handlers))

        # Executa em paralelo
        if unique_handlers:
            tasks = [self._safe_call(handler, event) for handler in unique_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(
        self,
        handler: EventHandler,
        event: Event,
    ) -> None:
        """
        Chama um handler de forma segura, capturando exceções.

        Args:
            handler: Handler a chamar
            event: Evento a passar
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler: {e}", exc_info=True)
            # Emite evento de erro (sem recursão)
            if event.type != EventType.SYSTEM_ERROR:
                error_event = Event(
                    type=EventType.SYSTEM_ERROR,
                    source="event_bus",
                    payload={
                        "error": str(e),
                        "original_event_id": event.id,
                        "original_event_type": event.type.value,
                    },
                )
                self._history.append(error_event)

    # ============================================================
    # AGENT COMMUNICATION HELPERS
    # ============================================================

    async def send_to_agent(
        self,
        from_agent: str,
        to_agent: str,
        message: Dict[str, Any],
        message_type: str = "general",
    ) -> Event:
        """
        Envia mensagem direta de um agente para outro.

        Args:
            from_agent: ID do agente remetente
            to_agent: ID do agente destinatário
            message: Conteúdo da mensagem
            message_type: Tipo da mensagem

        Returns:
            Evento criado
        """
        return await self.emit(
            event_type=EventType.AGENT_TO_AGENT,
            payload={
                "message": message,
                "message_type": message_type,
            },
            source=from_agent,
            target=to_agent,
        )

    async def agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Event:
        """
        Faz handoff de uma tarefa de um agente para outro.

        Args:
            from_agent: Agente que está passando a tarefa
            to_agent: Agente que receberá a tarefa
            task_data: Dados da tarefa
            context: Contexto acumulado

        Returns:
            Evento de handoff
        """
        return await self.emit(
            event_type=EventType.AGENT_HANDOFF,
            payload={
                "task": task_data,
                "context": context,
                "handoff_reason": "task_completion",
            },
            source=from_agent,
            target=to_agent,
            priority=3,  # Alta prioridade
        )

    async def agent_feedback(
        self,
        from_agent: str,
        to_agent: str,
        feedback: Dict[str, Any],
        severity: str = "info",
    ) -> Event:
        """
        Envia feedback de um agente para outro.

        Args:
            from_agent: Agente que está dando feedback
            to_agent: Agente que receberá feedback
            feedback: Conteúdo do feedback
            severity: Severidade (info, warning, error)

        Returns:
            Evento de feedback
        """
        return await self.emit(
            event_type=EventType.AGENT_FEEDBACK,
            payload={
                "feedback": feedback,
                "severity": severity,
            },
            source=from_agent,
            target=to_agent,
        )

    async def broadcast_to_agents(
        self,
        source: str,
        message: Dict[str, Any],
        agent_ids: Optional[List[str]] = None,
    ) -> List[Event]:
        """
        Faz broadcast de mensagem para múltiplos agentes.

        Args:
            source: Source da mensagem
            message: Conteúdo
            agent_ids: Lista de IDs de agentes (None = todos)

        Returns:
            Lista de eventos criados
        """
        if agent_ids is None:
            # Broadcast para todos (sem target específico)
            event = await self.emit(
                event_type=EventType.AGENT_TO_AGENT,
                payload={"message": message, "broadcast": True},
                source=source,
            )
            return [event]

        events = []
        for agent_id in agent_ids:
            event = await self.send_to_agent(source, agent_id, message)
            events.append(event)
        return events

    # ============================================================
    # QUERY AND HISTORY
    # ============================================================

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Retorna histórico de eventos com filtros opcionais.

        Args:
            event_type: Filtrar por tipo
            source: Filtrar por source
            limit: Número máximo de resultados

        Returns:
            Lista de eventos
        """
        events = self._history.copy()

        if event_type:
            events = [e for e in events if e.type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]

    def get_correlation_chain(
        self,
        correlation_id: str,
    ) -> List[Event]:
        """
        Retorna todos os eventos de uma cadeia de correlação.

        Args:
            correlation_id: ID de correlação

        Returns:
            Lista de eventos correlacionados
        """
        return [e for e in self._history if e.correlation_id == correlation_id]

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do event bus.

        Returns:
            Dicionário com estatísticas
        """
        return {
            **self._stats,
            "history_size": len(self._history),
            "registered_handlers": sum(len(h) for h in self._handlers.values()),
            "global_handlers": len(self._global_handlers),
        }

    # ============================================================
    # LIFECYCLE
    # ============================================================

    async def start(self) -> None:
        """Inicia o processamento de eventos em background"""
        self._running = True
        logger.info("EventBus started")

    async def stop(self) -> None:
        """Para o processamento de eventos"""
        self._running = False
        logger.info("EventBus stopped")

    def clear_history(self) -> None:
        """Limpa histórico de eventos"""
        self._history.clear()
        logger.info("Event history cleared")

    def reset_stats(self) -> None:
        """Reseta estatísticas"""
        self._stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_source": {},
        }
        logger.info("Event stats reset")
