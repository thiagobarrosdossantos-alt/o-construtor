"""
O Construtor - Task Queue
Sistema de fila de tarefas para processamento assíncrono

Gerencia a fila de tarefas para os agentes:
- Priorização de tarefas
- Retry automático
- Timeout handling
- Distribuição de carga
- **Persistência via Redis** (NOVO)
"""

import asyncio
import logging
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import uuid4
from enum import Enum
import heapq

# Importar Redis
import redis.asyncio as redis

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
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "queued_at": self.queued_at.isoformat() if isinstance(self.queued_at, datetime) else str(self.queued_at) if self.queued_at else None,
            "started_at": self.started_at.isoformat() if isinstance(self.started_at, datetime) else str(self.started_at) if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else str(self.completed_at) if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Cria tarefa a partir de dicionário"""
        # Converter timestamps de volta
        for field_name in ['created_at', 'queued_at', 'started_at', 'completed_at']:
            if data.get(field_name):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = None
            else:
                data[field_name] = None

        # Converter status
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])

        # Se created_at for None (bug fix), define agora
        if not data.get('created_at'):
            data['created_at'] = datetime.now()

        return cls(**data)


# Type alias para task handlers
TaskHandler = Callable[[Task], Coroutine[Any, Any, Any]]


class TaskQueue:
    """
    Fila de Tarefas do O Construtor (Redis-backed)

    Implementa uma priority queue persistente usando Redis:
    - Tarefas críticas são processadas primeiro
    - Suporte a retry com backoff exponencial
    - Timeout automático
    - Persistência real para escalabilidade
    """

    def __init__(self, redis_url: str = None):
        # Configuração do Redis
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[redis.Redis] = None

        # Handlers por tipo de tarefa (em memória, cada worker tem os seus)
        self._handlers: Dict[str, TaskHandler] = {}

        # Workers locais
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._semaphore: Optional[asyncio.Semaphore] = None

        # Chaves do Redis
        self.QUEUE_KEY = "task_queue:pending"  # Sorted set (score = priority)
        self.TASKS_KEY = "task_queue:data"     # Hash map (id -> json)
        self.PROCESSING_KEY = "task_queue:processing" # Set

        logger.info(f"TaskQueue initialized with Redis: {self.redis_url}")

    async def initialize(self):
        """Inicializa conexão com Redis"""
        # Se já existe e está fechado, ou loop fechou, recria
        if self.redis:
            try:
                await self.redis.ping()
            except (ConnectionError, RuntimeError):
                # RuntimeError geralmente significa loop fechado
                logger.warning("Redis connection lost or loop closed. Reconnecting...")
                await self.redis.close()
                self.redis = None

        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            try:
                await self.redis.ping()
                logger.info("Connected to Redis successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise ConnectionError(f"Redis connection failed: {e}")

    # ============================================================
    # HANDLER REGISTRATION
    # ============================================================

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        self._handlers[task_type] = handler

    def unregister_handler(self, task_type: str) -> None:
        if task_type in self._handlers:
            del self._handlers[task_type]

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
        """Adiciona uma tarefa à fila Redis"""
        if not self.redis:
            await self.initialize()

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

        # Salvar dados da task
        task_json = json.dumps(task.to_dict())
        await self.redis.hset(self.TASKS_KEY, task.id, task_json)

        # Adicionar à fila de prioridade (Sorted Set)
        # Redis ZSET ordena do menor para o maior score.
        # TaskPriority: CRITICAL=1 (primeiro), LOW=4 (ultimo).
        # Usamos priority como score diretamente.
        await self.redis.zadd(self.QUEUE_KEY, {task.id: task.priority})

        logger.info(f"Task enqueued (Redis): {task.name} ID: {task.id}")
        return task

    async def dequeue(self) -> Optional[Task]:
        """Remove e retorna a próxima tarefa da fila Redis"""
        if not self.redis:
            await self.initialize()

        # Transação atômica para pegar e mover para processing seria ideal
        # Simplificação: ZPOPMIN
        result = await self.redis.zpopmin(self.QUEUE_KEY)
        if not result:
            return None

        task_id, score = result[0]  # zpopmin retorna lista de tuplas [(member, score)]

        # Pegar dados completos
        task_json = await self.redis.hget(self.TASKS_KEY, task_id)
        if not task_json:
            logger.warning(f"Task ID {task_id} in queue but data missing")
            return None

        # Deserializar
        task_dict = json.loads(task_json)
        task = Task.from_dict(task_dict)

        # Mover para status de processamento (opcional, para monitoramento)
        task.status = TaskStatus.RUNNING
        await self.redis.sadd(self.PROCESSING_KEY, task.id)
        # Atualizar status no hash
        task_dict['status'] = TaskStatus.RUNNING.value
        await self.redis.hset(self.TASKS_KEY, task.id, json.dumps(task_dict))

        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Retorna uma tarefa pelo ID"""
        if not self.redis:
            await self.initialize()

        task_json = await self.redis.hget(self.TASKS_KEY, task_id)
        if task_json:
            return Task.from_dict(json.loads(task_json))
        return None

    # ============================================================
    # QUERY METHODS (Restored for Dashboard)
    # ============================================================

    async def get_queue_size(self) -> int:
        """Retorna número de tarefas na fila de espera"""
        if not self.redis: await self.initialize()
        return await self.redis.zcard(self.QUEUE_KEY)

    async def get_running_tasks(self) -> List[Task]:
        """Retorna lista de tarefas em execução"""
        if not self.redis: await self.initialize()

        # Get IDs from processing set
        processing_ids = await self.redis.smembers(self.PROCESSING_KEY)
        if not processing_ids:
            return []

        # Fetch actual task data
        tasks = []
        for tid in processing_ids:
            t = await self.get_task(tid)
            if t: tasks.append(t)
        return tasks

    async def get_all_tasks(self, limit: int = 100) -> List[Task]:
        """
        Retorna todas as tarefas (limitado).
        Nota: Em produção com Redis, idealmente usaria SCAN ou chaves separadas por status.
        Aqui faremos um scan simples no hash de dados.
        """
        if not self.redis: await self.initialize()

        # Pegar chaves aleatórias ou scan (simplificado: HGETALL é perigoso se muito grande)
        # Vamos usar HSCAN
        tasks = []
        cursor = 0
        while True:
            cursor, data = await self.redis.hscan(self.TASKS_KEY, cursor, count=20)
            for tid, task_json in data.items():
                try:
                    tasks.append(Task.from_dict(json.loads(task_json)))
                except:
                    pass
            if cursor == 0 or len(tasks) >= limit:
                break

        return tasks[:limit]

    # ============================================================
    # TASK EXECUTION & WORKERS
    # ============================================================

    async def start_workers(self, num_workers: int = 3) -> None:
        if self._running:
            return

        # Inicializa redis se necessário
        if not self.redis:
            try:
                await self.initialize()
            except Exception:
                # Se falhar ao conectar (ex: local dev sem redis), loga erro mas não quebra tudo
                # ou implementa fallback in-memory se fosse crítico.
                # Aqui vamos falhar graciosamente
                logger.error("Cannot start workers without Redis")
                return

        self._running = True
        self._semaphore = asyncio.Semaphore(num_workers)

        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)

        logger.info(f"Started {num_workers} Redis workers")

    async def stop_workers(self) -> None:
        self._running = False
        if self._workers:
            for w in self._workers:
                w.cancel()
        if self.redis:
            await self.redis.close()

    async def _worker_loop(self, worker_id: str) -> None:
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            try:
                # Polling com backoff se vazio
                task = await self.dequeue()
                if not task:
                    await asyncio.sleep(1) # Wait if queue is empty
                    continue

                async with self._semaphore:
                    await self._execute_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

    async def _execute_task(self, task: Task) -> None:
        handler = self._handlers.get(task.task_type)
        if not handler:
            logger.error(f"No handler for {task.task_type}")
            await self._update_task_status(task, TaskStatus.FAILED, error="No handler")
            return

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        await self._update_task_status(task, TaskStatus.RUNNING)

        try:
            result = await asyncio.wait_for(handler(task), timeout=task.timeout_seconds)

            task.result = result
            task.completed_at = datetime.now()
            await self._update_task_status(task, TaskStatus.COMPLETED, result=result)
            logger.info(f"Task {task.name} completed")

        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")

            if task.retry_count < task.max_retries:
                # Retry
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                # Re-queue with priority (maybe lower priority or same)
                # Ideally with delay (implementing delay in Redis requires ZADD with future timestamp)
                # Simples re-enqueue for now
                await asyncio.sleep(task.retry_delay_seconds)

                # Update data
                task_json = json.dumps(task.to_dict())
                await self.redis.hset(self.TASKS_KEY, task.id, task_json)
                await self.redis.zadd(self.QUEUE_KEY, {task.id: task.priority})
            else:
                await self._update_task_status(task, TaskStatus.FAILED, error=str(e))

        finally:
             # Remove from processing set
            await self.redis.srem(self.PROCESSING_KEY, task.id)

    async def _update_task_status(self, task: Task, status: TaskStatus, result: Any = None, error: str = None):
        """Atualiza status da tarefa no Redis"""
        task.status = status
        if result: task.result = result
        if error: task.error = error

        # Atualiza timestamp based on status
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = datetime.now()

        task_dict = task.to_dict()
        await self.redis.hset(self.TASKS_KEY, task.id, json.dumps(task_dict))
