"""
O Construtor - Task Queue
Sistema de fila de tarefas para processamento assíncrono

Gerencia a fila de tarefas para os agentes:
- Priorização de tarefas
- Retry automático
- Timeout handling
- Distribuição de carga
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import uuid4
from enum import Enum
import heapq

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status de uma tarefa"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Prioridade de tarefas"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass(order=True)
class Task:
    """Representa uma tarefa na fila"""

    # Campos para ordenação (priority queue)
    priority: int = field(compare=True)
    created_at: datetime = field(compare=True)

    # Campos principais (não usados na comparação)
    id: str = field(default_factory=lambda: str(uuid4()), compare=False)
    name: str = field(default="", compare=False)
    task_type: str = field(default="generic", compare=False)
    payload: Dict[str, Any] = field(default_factory=dict, compare=False)

    # Metadados
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    assigned_agent: Optional[str] = field(default=None, compare=False)

    # Configurações
    timeout_seconds: int = field(default=300, compare=False)
    max_retries: int = field(default=3, compare=False)
    retry_count: int = field(default=0, compare=False)
    retry_delay_seconds: int = field(default=5, compare=False)

    # Timestamps
    queued_at: Optional[datetime] = field(default=None, compare=False)
    started_at: Optional[datetime] = field(default=None, compare=False)
    completed_at: Optional[datetime] = field(default=None, compare=False)

    # Resultado
    result: Optional[Any] = field(default=None, compare=False)
    error: Optional[str] = field(default=None, compare=False)

    # Contexto
    correlation_id: Optional[str] = field(default=None, compare=False)
    parent_task_id: Optional[str] = field(default=None, compare=False)
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority,
            "assigned_agent": self.assigned_agent,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


# Type alias para task handlers
TaskHandler = Callable[[Task], Coroutine[Any, Any, Any]]


class TaskQueue:
    """
    Fila de Tarefas do O Construtor

    Implementa uma priority queue para gerenciar tarefas:
    - Tarefas críticas são processadas primeiro
    - Suporte a retry com backoff exponencial
    - Timeout automático
    - Múltiplos workers paralelos

    Uso:
        queue = TaskQueue()

        # Registrar handler
        async def process_code_review(task: Task):
            return {"status": "approved"}

        queue.register_handler("code_review", process_code_review)

        # Adicionar tarefa
        task = await queue.enqueue(
            name="Review PR #123",
            task_type="code_review",
            payload={"pr_number": 123},
            priority=TaskPriority.HIGH,
        )

        # Iniciar processamento
        await queue.start_workers(num_workers=3)
    """

    def __init__(self):
        # Priority queue (heap)
        self._queue: List[Task] = []

        # Tasks por ID (para lookup rápido)
        self._tasks: Dict[str, Task] = {}

        # Handlers por tipo de tarefa
        self._handlers: Dict[str, TaskHandler] = {}

        # Workers ativos
        self._workers: List[asyncio.Task] = []
        self._running = False

        # Semáforo para controle de concorrência
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Estatísticas
        self._stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retries": 0,
            "by_type": {},
        }

        # Event para notificar workers de novas tarefas
        self._new_task_event = asyncio.Event()

        logger.info("TaskQueue initialized")

    # ============================================================
    # HANDLER REGISTRATION
    # ============================================================

    def register_handler(
        self,
        task_type: str,
        handler: TaskHandler,
    ) -> None:
        """
        Registra um handler para um tipo de tarefa.

        Args:
            task_type: Tipo de tarefa
            handler: Função async que processa a tarefa
        """
        self._handlers[task_type] = handler
        logger.debug(f"Handler registered for task type: {task_type}")

    def unregister_handler(self, task_type: str) -> None:
        """
        Remove handler de um tipo de tarefa.

        Args:
            task_type: Tipo de tarefa
        """
        if task_type in self._handlers:
            del self._handlers[task_type]
            logger.debug(f"Handler unregistered for task type: {task_type}")

    # ============================================================
    # TASK MANAGEMENT
    # ============================================================

    async def enqueue(
        self,
        name: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        assigned_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Adiciona uma tarefa à fila.

        Args:
            name: Nome descritivo da tarefa
            task_type: Tipo da tarefa (deve ter handler registrado)
            payload: Dados da tarefa
            priority: Prioridade
            timeout_seconds: Timeout em segundos
            max_retries: Número máximo de retries
            assigned_agent: Agente específico para executar
            correlation_id: ID para correlação
            parent_task_id: ID da tarefa pai
            metadata: Metadados adicionais

        Returns:
            Task criada
        """
        task = Task(
            priority=priority.value,
            created_at=datetime.now(),
            name=name,
            task_type=task_type,
            payload=payload,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            assigned_agent=assigned_agent,
            correlation_id=correlation_id,
            parent_task_id=parent_task_id,
            metadata=metadata or {},
        )

        task.status = TaskStatus.QUEUED
        task.queued_at = datetime.now()

        # Adiciona ao heap (priority queue)
        heapq.heappush(self._queue, task)

        # Registra para lookup
        self._tasks[task.id] = task

        # Atualiza estatísticas
        self._stats["total_enqueued"] += 1
        self._stats["by_type"][task_type] = self._stats["by_type"].get(task_type, 0) + 1

        # Notifica workers
        self._new_task_event.set()

        logger.info(f"Task enqueued: {task.name} (type: {task_type}, priority: {priority.name})")
        return task

    async def dequeue(self) -> Optional[Task]:
        """
        Remove e retorna a próxima tarefa da fila (maior prioridade).

        Returns:
            Task ou None se fila vazia
        """
        while self._queue:
            task = heapq.heappop(self._queue)

            # Verifica se task ainda existe e está no estado correto
            if task.id in self._tasks and task.status == TaskStatus.QUEUED:
                return task

        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retorna uma tarefa pelo ID.

        Args:
            task_id: ID da tarefa

        Returns:
            Task ou None
        """
        return self._tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma tarefa.

        Args:
            task_id: ID da tarefa

        Returns:
            True se cancelada com sucesso
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Task cancelled: {task_id}")
            return True

        return False

    # ============================================================
    # TASK EXECUTION
    # ============================================================

    async def _execute_task(self, task: Task) -> None:
        """
        Executa uma tarefa individual.

        Args:
            task: Tarefa a executar
        """
        handler = self._handlers.get(task.task_type)
        if not handler:
            logger.error(f"No handler for task type: {task.task_type}")
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for type: {task.task_type}"
            return

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        logger.info(f"Executing task: {task.name} (ID: {task.id})")

        try:
            # Executa com timeout
            result = await asyncio.wait_for(
                handler(task),
                timeout=task.timeout_seconds,
            )

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()

            self._stats["total_completed"] += 1
            logger.info(f"Task completed: {task.name}")

        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = f"Task timed out after {task.timeout_seconds} seconds"
            logger.error(f"Task timeout: {task.name}")

            # Tenta retry
            await self._maybe_retry(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task failed: {task.name} - {e}")

            # Tenta retry
            await self._maybe_retry(task)

    async def _maybe_retry(self, task: Task) -> None:
        """
        Verifica se deve fazer retry e reenfileira se necessário.

        Args:
            task: Tarefa que falhou
        """
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING

            # Calcula delay com backoff exponencial
            delay = task.retry_delay_seconds * (2 ** (task.retry_count - 1))

            logger.info(
                f"Retrying task {task.name} in {delay}s "
                f"(attempt {task.retry_count}/{task.max_retries})"
            )

            self._stats["total_retries"] += 1

            # Aguarda delay e reenfileira
            await asyncio.sleep(delay)

            task.status = TaskStatus.QUEUED
            task.queued_at = datetime.now()
            heapq.heappush(self._queue, task)
            self._new_task_event.set()

        else:
            task.status = TaskStatus.FAILED
            self._stats["total_failed"] += 1
            logger.error(f"Task failed after {task.max_retries} retries: {task.name}")

    # ============================================================
    # WORKER MANAGEMENT
    # ============================================================

    async def start_workers(self, num_workers: int = 3) -> None:
        """
        Inicia workers para processar a fila.

        Args:
            num_workers: Número de workers paralelos
        """
        if self._running:
            logger.warning("Workers already running")
            return

        self._running = True
        self._semaphore = asyncio.Semaphore(num_workers)

        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)

        logger.info(f"Started {num_workers} workers")

    async def stop_workers(self, timeout: float = 30.0) -> None:
        """
        Para todos os workers gracefully.

        Args:
            timeout: Tempo máximo de espera
        """
        self._running = False
        self._new_task_event.set()  # Desperta workers dormindo

        # Aguarda workers terminarem
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("Workers did not stop in time, cancelling...")
                for worker in self._workers:
                    worker.cancel()

        self._workers.clear()
        logger.info("Workers stopped")

    async def _worker_loop(self, worker_id: str) -> None:
        """
        Loop principal de um worker.

        Args:
            worker_id: Identificador do worker
        """
        logger.debug(f"Worker {worker_id} started")

        while self._running:
            # Aguarda nova tarefa ou shutdown
            try:
                await asyncio.wait_for(
                    self._new_task_event.wait(),
                    timeout=1.0,
                )
            except asyncio.TimeoutError:
                continue

            self._new_task_event.clear()

            # Processa tarefas disponíveis
            while self._running:
                task = await self.dequeue()
                if not task:
                    break

                async with self._semaphore:
                    await self._execute_task(task)

        logger.debug(f"Worker {worker_id} stopped")

    # ============================================================
    # QUERY AND STATS
    # ============================================================

    def get_queue_size(self) -> int:
        """Retorna número de tarefas na fila"""
        return len([t for t in self._queue if t.status == TaskStatus.QUEUED])

    def get_pending_tasks(self, limit: int = 50) -> List[Task]:
        """Retorna tarefas pendentes/enfileiradas"""
        return [
            t for t in self._tasks.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED]
        ][:limit]

    def get_running_tasks(self) -> List[Task]:
        """Retorna tarefas em execução"""
        return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]

    def get_completed_tasks(self, limit: int = 50) -> List[Task]:
        """Retorna tarefas completadas"""
        tasks = [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]
        return sorted(tasks, key=lambda t: t.completed_at or datetime.min, reverse=True)[:limit]

    def get_failed_tasks(self, limit: int = 50) -> List[Task]:
        """Retorna tarefas que falharam"""
        return [t for t in self._tasks.values() if t.status == TaskStatus.FAILED][:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da fila"""
        return {
            **self._stats,
            "queue_size": self.get_queue_size(),
            "running_count": len(self.get_running_tasks()),
            "total_tasks": len(self._tasks),
            "workers_active": len(self._workers) if self._running else 0,
        }

    def clear_completed(self) -> int:
        """
        Remove tarefas completadas do histórico.

        Returns:
            Número de tarefas removidas
        """
        completed_ids = [
            task_id for task_id, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ]

        for task_id in completed_ids:
            del self._tasks[task_id]

        logger.info(f"Cleared {len(completed_ids)} completed tasks")
        return len(completed_ids)
