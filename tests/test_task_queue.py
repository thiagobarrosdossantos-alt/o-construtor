"""
Unit tests para TaskQueue
Testa enfileiramento, processamento, retries, e cleanup automático
"""
import pytest
import asyncio
from datetime import datetime
from core.task_queue import TaskQueue, Task, TaskStatus, TaskPriority


@pytest.mark.asyncio
class TestTaskQueue:
    """Testes do TaskQueue"""

    async def test_enqueue_task(self):
        """Testa enfileiramento de tarefa"""
        queue = TaskQueue()

        task = await queue.enqueue(
            name="Test Task",
            task_type="test",
            payload={"data": "test"},
            priority=TaskPriority.NORMAL
        )

        assert task.id is not None
        assert task.name == "Test Task"
        assert task.status == TaskStatus.QUEUED
        assert task.priority == TaskPriority.NORMAL.value

    async def test_enqueue_with_different_priorities(self):
        """Testa enfileiramento com diferentes prioridades"""
        queue = TaskQueue()

        low_task = await queue.enqueue(
            name="Low Priority",
            task_type="test",
            payload={},
            priority=TaskPriority.LOW
        )

        high_task = await queue.enqueue(
            name="High Priority",
            task_type="test",
            payload={},
            priority=TaskPriority.HIGH
        )

        # Tarefa de alta prioridade deve ter menor valor (processada primeiro)
        assert high_task.priority < low_task.priority

    async def test_get_task_by_id(self):
        """Testa busca de tarefa por ID"""
        queue = TaskQueue()

        task = await queue.enqueue(
            name="Find Me",
            task_type="test",
            payload={}
        )

        found_task = queue.get_task(task.id)
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.name == "Find Me"

    async def test_get_nonexistent_task(self):
        """Testa busca de tarefa inexistente"""
        queue = TaskQueue()
        task = queue.get_task("nonexistent-id")
        assert task is None

    async def test_task_handler_registration(self):
        """Testa registro de handlers"""
        queue = TaskQueue()

        async def test_handler(task: Task) -> dict:
            return {"result": "success"}

        queue.register_handler("test_type", test_handler)

        # Verificar se handler foi registrado
        assert "test_type" in queue._handlers
        assert queue._handlers["test_type"] == test_handler

    async def test_task_execution_with_handler(self):
        """Testa execução de tarefa com handler"""
        queue = TaskQueue()
        execution_count = 0

        async def counting_handler(task: Task) -> dict:
            nonlocal execution_count
            execution_count += 1
            return {"count": execution_count}

        queue.register_handler("count", counting_handler)

        task = await queue.enqueue(
            name="Count Task",
            task_type="count",
            payload={}
        )

        await queue._execute_task(task)

        assert execution_count == 1
        assert task.status == TaskStatus.COMPLETED

    async def test_get_queue_size(self):
        """Testa contagem de tarefas na fila"""
        queue = TaskQueue()

        # Fila vazia
        assert queue.get_queue_size() == 0

        # Adicionar tarefas
        await queue.enqueue("Task 1", "test", {})
        await queue.enqueue("Task 2", "test", {})
        await queue.enqueue("Task 3", "test", {})

        assert queue.get_queue_size() == 3

    async def test_get_pending_tasks(self):
        """Testa busca de tarefas pendentes"""
        queue = TaskQueue()

        task1 = await queue.enqueue("Pending 1", "test", {})
        task2 = await queue.enqueue("Pending 2", "test", {})

        pending = queue.get_pending_tasks()

        assert len(pending) == 2
        assert all(t.status == TaskStatus.QUEUED for t in pending)

    async def test_clear_completed(self):
        """Testa limpeza de tarefas completadas"""
        queue = TaskQueue()

        # Criar tarefas
        task1 = await queue.enqueue("Task 1", "test", {})
        task2 = await queue.enqueue("Task 2", "test", {})
        task3 = await queue.enqueue("Task 3", "test", {})

        # Marcar algumas como completadas
        task1.status = TaskStatus.COMPLETED
        task2.status = TaskStatus.COMPLETED

        # Limpar completadas
        cleared_count = queue.clear_completed()

        assert cleared_count == 2
        assert queue.get_task(task1.id) is None
        assert queue.get_task(task2.id) is None
        assert queue.get_task(task3.id) is not None

    async def test_get_stats(self):
        """Testa estatísticas da fila"""
        queue = TaskQueue()

        await queue.enqueue("Task 1", "test", {})
        await queue.enqueue("Task 2", "test", {})

        stats = queue.get_stats()

        assert "queue_size" in stats
        assert "total_tasks" in stats
        assert stats["queue_size"] == 2
        assert stats["total_tasks"] == 2

    async def test_worker_lifecycle(self):
        """Testa ciclo de vida dos workers"""
        queue = TaskQueue()

        # Iniciar workers
        await queue.start_workers(num_workers=2)
        assert queue._running is True
        assert len(queue._workers) == 3  # 2 workers + 1 cleanup worker

        # Parar workers
        await queue.stop_workers()
        assert queue._running is False

    async def test_cleanup_worker_creation(self):
        """Testa criação do worker de cleanup automático"""
        queue = TaskQueue()

        await queue.start_workers(num_workers=2, cleanup_interval_minutes=5)

        # Deve ter 2 workers + 1 cleanup worker
        assert len(queue._workers) == 3
        assert queue._running is True

    async def test_task_timeout(self):
        """Testa timeout de tarefa"""
        queue = TaskQueue()

        async def slow_handler(task: Task) -> dict:
            await asyncio.sleep(10)  # Simula operação lenta
            return {"result": "too late"}

        queue.register_handler("slow", slow_handler)

        task = await queue.enqueue(
            name="Slow Task",
            task_type="slow",
            payload={},
            timeout_seconds=1,  # Timeout curto
            max_retries=0  # Sem retries para teste
        )

        # Executar tarefa (deve dar timeout)
        await queue._execute_task(task)

        # Com timeout, tarefa é re-enfileirada se tiver retries disponíveis
        # Como max_retries=0, status permanece QUEUED com erro registrado
        assert task.error is not None
        assert "timed out" in task.error.lower() or "timeout" in task.error.lower()

    async def test_correlation_id(self):
        """Testa correlation_id para rastreamento"""
        queue = TaskQueue()

        task = await queue.enqueue(
            name="Traceable Task",
            task_type="test",
            payload={},
            correlation_id="trace-123"
        )

        assert task.correlation_id == "trace-123"

    async def test_parent_task_relationship(self):
        """Testa relacionamento pai-filho entre tarefas"""
        queue = TaskQueue()

        parent = await queue.enqueue(
            name="Parent Task",
            task_type="test",
            payload={}
        )

        child = await queue.enqueue(
            name="Child Task",
            task_type="test",
            payload={},
            parent_task_id=parent.id
        )

        assert child.parent_task_id == parent.id
