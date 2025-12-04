"""
O Construtor - Memory Store
Sistema de memória compartilhada para persistência de contexto entre agentes

Este módulo permite que:
1. Agentes compartilhem conhecimento
2. Decisões anteriores sejam lembradas
3. Contexto de projetos seja mantido
4. Padrões e preferências sejam aprendidos
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypeVar
from uuid import uuid4
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Tipos de memória suportados"""
    SHORT_TERM = "short_term"  # Cache em memória, expira em minutos
    LONG_TERM = "long_term"  # Persistido em banco de dados
    EPISODIC = "episodic"  # Memórias de eventos específicos
    SEMANTIC = "semantic"  # Conhecimento geral aprendido
    PROCEDURAL = "procedural"  # Como fazer coisas (padrões, workflows)


@dataclass
class Memory:
    """Representa uma unidade de memória"""
    id: str = field(default_factory=lambda: str(uuid4()))
    memory_type: MemoryType = MemoryType.SHORT_TERM
    category: str = ""  # Ex: "architecture", "code_pattern", "user_preference"
    key: str = ""  # Identificador único dentro da categoria
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    relevance_score: float = 1.0
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Verifica se a memória expirou"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        data = asdict(self)
        data["memory_type"] = self.memory_type.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat() if self.expires_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Cria instância a partir de dicionário"""
        data["memory_type"] = MemoryType(data["memory_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data["expires_at"]:
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)


@dataclass
class ProjectContext:
    """Contexto completo de um projeto"""
    project_id: str
    name: str
    description: str = ""
    repository_url: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    architecture_decisions: List[Dict[str, Any]] = field(default_factory=list)
    code_patterns: List[Dict[str, Any]] = field(default_factory=list)
    known_issues: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    team_conventions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MemoryStore:
    """
    Sistema de Memória Compartilhada do O Construtor

    Implementa múltiplos níveis de memória:
    - SHORT_TERM: Cache rápido em memória (dict)
    - LONG_TERM: Persistido em Supabase
    - EPISODIC: Eventos e interações (histórico)
    - SEMANTIC: Conhecimento aprendido
    - PROCEDURAL: Padrões e workflows

    Funcionalidades:
    - Armazenamento e recuperação de contexto
    - Busca semântica por relevância
    - Expiração automática de memórias
    - Sincronização entre agentes
    """

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None,
    ):
        self.supabase = supabase_client
        self.redis = redis_client

        # Cache em memória (short-term)
        self._short_term_cache: Dict[str, Memory] = {}

        # Contextos de projetos
        self._project_contexts: Dict[str, ProjectContext] = {}

        # Lock para operações thread-safe
        self._lock = asyncio.Lock()

        logger.info("MemoryStore initialized")

    # ============================================================
    # OPERAÇÕES BÁSICAS
    # ============================================================

    async def store(
        self,
        key: str,
        content: Any,
        category: str = "general",
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        ttl_seconds: Optional[int] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Armazena uma memória no sistema.

        Args:
            key: Identificador único
            content: Conteúdo a ser armazenado
            category: Categoria da memória
            memory_type: Tipo de memória
            ttl_seconds: Tempo de vida em segundos
            project_id: ID do projeto associado
            agent_id: ID do agente que criou
            tags: Tags para busca
            metadata: Metadados adicionais

        Returns:
            Memory criada
        """
        async with self._lock:
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            memory = Memory(
                memory_type=memory_type,
                category=category,
                key=key,
                content=content,
                metadata=metadata or {},
                expires_at=expires_at,
                project_id=project_id,
                agent_id=agent_id,
                tags=tags or [],
            )

            # Armazena baseado no tipo
            if memory_type == MemoryType.SHORT_TERM:
                self._short_term_cache[f"{category}:{key}"] = memory

                # Também armazena no Redis se disponível (para distribuição)
                if self.redis:
                    await self._store_in_redis(memory, ttl_seconds)

            else:
                # Memórias de longo prazo vão para Supabase
                if self.supabase:
                    await self._store_in_supabase(memory)
                else:
                    # Fallback para cache local
                    self._short_term_cache[f"{category}:{key}"] = memory

            logger.debug(f"Memory stored: {category}:{key} ({memory_type.value})")
            return memory

    async def retrieve(
        self,
        key: str,
        category: str = "general",
    ) -> Optional[Any]:
        """
        Recupera conteúdo de uma memória.

        Args:
            key: Identificador da memória
            category: Categoria da memória

        Returns:
            Conteúdo da memória ou None
        """
        cache_key = f"{category}:{key}"

        # Tenta cache local primeiro
        if cache_key in self._short_term_cache:
            memory = self._short_term_cache[cache_key]
            if not memory.is_expired():
                memory.access_count += 1
                memory.updated_at = datetime.now()
                return memory.content
            else:
                del self._short_term_cache[cache_key]

        # Tenta Redis
        if self.redis:
            content = await self._retrieve_from_redis(cache_key)
            if content:
                return content

        # Tenta Supabase
        if self.supabase:
            memory = await self._retrieve_from_supabase(category, key)
            if memory:
                # Popula cache local
                self._short_term_cache[cache_key] = memory
                return memory.content

        return None

    async def retrieve_memory(
        self,
        key: str,
        category: str = "general",
    ) -> Optional[Memory]:
        """
        Recupera objeto Memory completo.

        Args:
            key: Identificador da memória
            category: Categoria da memória

        Returns:
            Objeto Memory ou None
        """
        cache_key = f"{category}:{key}"

        if cache_key in self._short_term_cache:
            memory = self._short_term_cache[cache_key]
            if not memory.is_expired():
                memory.access_count += 1
                return memory

        if self.supabase:
            return await self._retrieve_from_supabase(category, key)

        return None

    async def delete(
        self,
        key: str,
        category: str = "general",
    ) -> bool:
        """
        Remove uma memória do sistema.

        Args:
            key: Identificador da memória
            category: Categoria da memória

        Returns:
            True se removido com sucesso
        """
        cache_key = f"{category}:{key}"

        async with self._lock:
            deleted = False

            if cache_key in self._short_term_cache:
                del self._short_term_cache[cache_key]
                deleted = True

            if self.redis:
                await self._delete_from_redis(cache_key)
                deleted = True

            if self.supabase:
                await self._delete_from_supabase(category, key)
                deleted = True

            return deleted

    # ============================================================
    # BUSCA E CONSULTA
    # ============================================================

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Busca memórias por query, tags ou projeto.

        Args:
            query: Texto para busca
            category: Filtrar por categoria
            tags: Filtrar por tags
            project_id: Filtrar por projeto
            limit: Número máximo de resultados

        Returns:
            Lista de memórias encontradas
        """
        results: List[Memory] = []

        # Busca no cache local
        for key, memory in self._short_term_cache.items():
            if memory.is_expired():
                continue

            # Aplica filtros
            if category and memory.category != category:
                continue
            if project_id and memory.project_id != project_id:
                continue
            if tags and not any(tag in memory.tags for tag in tags):
                continue

            # Busca por conteúdo
            if query:
                content_str = json.dumps(memory.content) if isinstance(memory.content, dict) else str(memory.content)
                if query.lower() not in content_str.lower():
                    continue

            results.append(memory)

        # Busca no Supabase se disponível
        if self.supabase and len(results) < limit:
            db_results = await self._search_in_supabase(
                query=query,
                category=category,
                tags=tags,
                project_id=project_id,
                limit=limit - len(results),
            )
            results.extend(db_results)

        # Ordena por relevância e access_count
        results.sort(key=lambda m: (m.relevance_score, m.access_count), reverse=True)

        return results[:limit]

    async def get_by_category(
        self,
        category: str,
        limit: int = 50,
    ) -> List[Memory]:
        """
        Retorna todas as memórias de uma categoria.

        Args:
            category: Categoria a buscar
            limit: Número máximo de resultados

        Returns:
            Lista de memórias
        """
        return await self.search(query="", category=category, limit=limit)

    async def get_by_tags(
        self,
        tags: List[str],
        limit: int = 50,
    ) -> List[Memory]:
        """
        Retorna memórias que possuem as tags especificadas.

        Args:
            tags: Lista de tags
            limit: Número máximo de resultados

        Returns:
            Lista de memórias
        """
        return await self.search(query="", tags=tags, limit=limit)

    # ============================================================
    # CONTEXTO DE PROJETO
    # ============================================================

    async def get_project_context(
        self,
        project_id: str,
    ) -> Optional[ProjectContext]:
        """
        Retorna o contexto completo de um projeto.

        Args:
            project_id: ID do projeto

        Returns:
            ProjectContext ou None
        """
        if project_id in self._project_contexts:
            return self._project_contexts[project_id]

        # Busca no Supabase
        if self.supabase:
            context = await self._load_project_context(project_id)
            if context:
                self._project_contexts[project_id] = context
                return context

        return None

    async def update_project_context(
        self,
        project_id: str,
        updates: Dict[str, Any],
    ) -> ProjectContext:
        """
        Atualiza o contexto de um projeto.

        Args:
            project_id: ID do projeto
            updates: Campos a atualizar

        Returns:
            ProjectContext atualizado
        """
        context = await self.get_project_context(project_id)

        if not context:
            # Cria novo contexto
            context = ProjectContext(
                project_id=project_id,
                name=updates.get("name", project_id),
            )

        # Aplica updates
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.updated_at = datetime.now()

        # Salva
        self._project_contexts[project_id] = context

        if self.supabase:
            await self._save_project_context(context)

        return context

    async def add_architecture_decision(
        self,
        project_id: str,
        decision: Dict[str, Any],
    ) -> None:
        """
        Adiciona uma decisão de arquitetura ao contexto do projeto.

        Args:
            project_id: ID do projeto
            decision: Decisão a adicionar (título, descrição, rationale, etc.)
        """
        context = await self.get_project_context(project_id)
        if not context:
            context = await self.update_project_context(
                project_id,
                {"name": project_id},
            )

        decision["timestamp"] = datetime.now().isoformat()
        context.architecture_decisions.append(decision)
        context.updated_at = datetime.now()

        if self.supabase:
            await self._save_project_context(context)

        # Também salva como memória semântica
        await self.store(
            key=f"arch_decision_{len(context.architecture_decisions)}",
            content=decision,
            category="architecture_decisions",
            memory_type=MemoryType.SEMANTIC,
            project_id=project_id,
            tags=["architecture", "decision"],
        )

    async def add_code_pattern(
        self,
        project_id: str,
        pattern: Dict[str, Any],
    ) -> None:
        """
        Adiciona um padrão de código aprendido.

        Args:
            project_id: ID do projeto
            pattern: Padrão a adicionar (nome, descrição, exemplo, etc.)
        """
        context = await self.get_project_context(project_id)
        if not context:
            context = await self.update_project_context(
                project_id,
                {"name": project_id},
            )

        pattern["timestamp"] = datetime.now().isoformat()
        context.code_patterns.append(pattern)
        context.updated_at = datetime.now()

        if self.supabase:
            await self._save_project_context(context)

        # Também salva como memória procedural
        await self.store(
            key=f"code_pattern_{pattern.get('name', len(context.code_patterns))}",
            content=pattern,
            category="code_patterns",
            memory_type=MemoryType.PROCEDURAL,
            project_id=project_id,
            tags=["code", "pattern"],
        )

    # ============================================================
    # MEMÓRIA PARA AGENTES
    # ============================================================

    async def store_agent_memory(
        self,
        agent_id: str,
        key: str,
        content: Any,
        memory_type: MemoryType = MemoryType.EPISODIC,
    ) -> Memory:
        """
        Armazena memória específica de um agente.

        Args:
            agent_id: ID do agente
            key: Identificador da memória
            content: Conteúdo
            memory_type: Tipo de memória

        Returns:
            Memory criada
        """
        return await self.store(
            key=f"{agent_id}:{key}",
            content=content,
            category="agent_memory",
            memory_type=memory_type,
            agent_id=agent_id,
        )

    async def get_agent_memory(
        self,
        agent_id: str,
        key: str,
    ) -> Optional[Any]:
        """
        Recupera memória específica de um agente.

        Args:
            agent_id: ID do agente
            key: Identificador da memória

        Returns:
            Conteúdo da memória
        """
        return await self.retrieve(
            key=f"{agent_id}:{key}",
            category="agent_memory",
        )

    async def get_agent_history(
        self,
        agent_id: str,
        limit: int = 100,
    ) -> List[Memory]:
        """
        Retorna histórico de memórias de um agente.

        Args:
            agent_id: ID do agente
            limit: Número máximo de resultados

        Returns:
            Lista de memórias do agente
        """
        results = []
        for memory in self._short_term_cache.values():
            if memory.agent_id == agent_id and not memory.is_expired():
                results.append(memory)

        results.sort(key=lambda m: m.created_at, reverse=True)
        return results[:limit]

    # ============================================================
    # WORKFLOW PERSISTENCE
    # ============================================================

    async def save_workflow(self, workflow: Any) -> None:
        """
        Salva estado de um workflow.

        Args:
            workflow: Workflow a salvar
        """
        await self.store(
            key=workflow.id,
            content={
                "id": workflow.id,
                "name": workflow.name,
                "state": workflow.state.value,
                "context": workflow.context,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
            },
            category="workflows",
            memory_type=MemoryType.EPISODIC,
            tags=["workflow"],
        )

    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """
        Recupera workflow salvo.

        Args:
            workflow_id: ID do workflow

        Returns:
            Dados do workflow
        """
        return await self.retrieve(key=workflow_id, category="workflows")

    # ============================================================
    # MANUTENÇÃO
    # ============================================================

    async def cleanup_expired(self) -> int:
        """
        Remove memórias expiradas.

        Returns:
            Número de memórias removidas
        """
        async with self._lock:
            expired_keys = [
                key for key, memory in self._short_term_cache.items()
                if memory.is_expired()
            ]

            for key in expired_keys:
                del self._short_term_cache[key]

            logger.info(f"Cleaned up {len(expired_keys)} expired memories")
            return len(expired_keys)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do memory store.

        Returns:
            Dicionário com estatísticas
        """
        total_memories = len(self._short_term_cache)
        by_type = {}
        by_category = {}

        for memory in self._short_term_cache.values():
            type_name = memory.memory_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            by_category[memory.category] = by_category.get(memory.category, 0) + 1

        return {
            "total_memories": total_memories,
            "total_projects": len(self._project_contexts),
            "by_type": by_type,
            "by_category": by_category,
            "redis_connected": self.redis is not None,
            "supabase_connected": self.supabase is not None,
        }

    # ============================================================
    # MÉTODOS PRIVADOS (STORAGE BACKENDS)
    # ============================================================

    async def _store_in_redis(self, memory: Memory, ttl: Optional[int]) -> None:
        """Armazena memória no Redis"""
        if not self.redis:
            return
        # TODO: Implementar quando Redis estiver configurado
        pass

    async def _retrieve_from_redis(self, key: str) -> Optional[Any]:
        """Recupera do Redis"""
        if not self.redis:
            return None
        # TODO: Implementar
        return None

    async def _delete_from_redis(self, key: str) -> None:
        """Remove do Redis"""
        if not self.redis:
            return
        # TODO: Implementar
        pass

    async def _store_in_supabase(self, memory: Memory) -> None:
        """Armazena memória no Supabase"""
        if not self.supabase:
            return
        # TODO: Implementar quando Supabase estiver configurado
        pass

    async def _retrieve_from_supabase(
        self,
        category: str,
        key: str,
    ) -> Optional[Memory]:
        """Recupera do Supabase"""
        if not self.supabase:
            return None
        # TODO: Implementar
        return None

    async def _delete_from_supabase(self, category: str, key: str) -> None:
        """Remove do Supabase"""
        if not self.supabase:
            return
        # TODO: Implementar
        pass

    async def _search_in_supabase(
        self,
        query: str,
        category: Optional[str],
        tags: Optional[List[str]],
        project_id: Optional[str],
        limit: int,
    ) -> List[Memory]:
        """Busca no Supabase"""
        if not self.supabase:
            return []
        # TODO: Implementar
        return []

    async def _load_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Carrega contexto de projeto do Supabase"""
        if not self.supabase:
            return None
        # TODO: Implementar
        return None

    async def _save_project_context(self, context: ProjectContext) -> None:
        """Salva contexto de projeto no Supabase"""
        if not self.supabase:
            return
        # TODO: Implementar
        pass
