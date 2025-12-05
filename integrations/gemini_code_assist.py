"""
O Construtor - Gemini Code Assist Client
Integração com Gemini Code Assist para sugestões e autocomplete

Gemini Code Assist trabalha em conjunto com Claude Code:
- Claude Code: Implementação e execução
- Gemini Code Assist: Sugestões, autocomplete, validação

Juntos formam uma dupla poderosa para desenvolvimento autônomo.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CodeSuggestion:
    """Uma sugestão de código do Gemini Code Assist"""
    suggestion_type: str  # completion, refactoring, fix, optimization
    original_code: str
    suggested_code: str
    explanation: str
    confidence: float  # 0.0 - 1.0
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeAssistResponse:
    """Resposta do Gemini Code Assist"""
    success: bool
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    explanation: str = ""
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class GeminiCodeAssistClient:
    """
    Cliente para integração com Gemini Code Assist

    Fornece capacidades de:
    - Autocomplete inteligente
    - Sugestões de refatoração
    - Detecção e correção de erros
    - Documentação inline
    - Pair programming assistido

    Colaboração com Claude Code:
    - Gemini sugere, Claude implementa
    - Gemini valida, Claude corrige
    - Trabalho em tempo real coordenado

    Uso:
        client = GeminiCodeAssistClient()
        await client.initialize()

        # Obter sugestões de completion
        suggestions = await client.get_completions(
            code="def calculate_",
            file_path="utils.py",
            cursor_position=15,
        )

        # Validar código
        validation = await client.validate_code(code, file_path)
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",  # Flash para baixa latência
    ):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model

        self._initialized = False
        self._vertex_client: Optional[Any] = None
        self._genai_client: Optional[Any] = None

        # Cache de sugestões para evitar chamadas repetidas
        self._suggestion_cache: Dict[str, CodeAssistResponse] = {}
        self._cache_ttl_seconds = 300

        # Estatísticas
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_suggestions": 0,
            "average_latency_ms": 0.0,
        }

        logger.info("GeminiCodeAssistClient initialized")

    async def initialize(self) -> bool:
        """
        Inicializa o cliente.

        Returns:
            True se inicializado com sucesso
        """
        if self._initialized:
            return True

        try:
            # Tenta inicializar via Vertex AI
            if self.project_id:
                await self._initialize_vertex()

            # Fallback para Google AI Studio
            if not self._vertex_client and self.api_key:
                await self._initialize_genai()

            self._initialized = self._vertex_client is not None or self._genai_client is not None
            return self._initialized

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False

    async def _initialize_vertex(self) -> None:
        """Inicializa via Vertex AI"""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=self.project_id, location="us-central1")
            self._vertex_client = GenerativeModel(self.model)
            logger.info("Vertex AI client initialized")
        except Exception as e:
            logger.warning(f"Vertex AI init failed: {e}")

    async def _initialize_genai(self) -> None:
        """Inicializa via Google AI Studio"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._genai_client = genai.GenerativeModel(self.model)
            logger.info("Google AI Studio client initialized")
        except Exception as e:
            logger.warning(f"Google AI Studio init failed: {e}")

    # ============================================================
    # CORE METHODS
    # ============================================================

    async def get_completions(
        self,
        code: str,
        file_path: str,
        cursor_position: int,
        language: Optional[str] = None,
        max_suggestions: int = 5,
    ) -> CodeAssistResponse:
        """
        Obtém sugestões de completion para código.

        Args:
            code: Código atual
            file_path: Caminho do arquivo
            cursor_position: Posição do cursor
            language: Linguagem (inferida se não fornecida)
            max_suggestions: Número máximo de sugestões

        Returns:
            CodeAssistResponse com sugestões
        """
        await self.initialize()
        start_time = datetime.now()
        self._stats["total_requests"] += 1

        # Verifica cache
        cache_key = f"{file_path}:{cursor_position}:{hash(code)}"
        if cache_key in self._suggestion_cache:
            self._stats["cache_hits"] += 1
            return self._suggestion_cache[cache_key]

        # Detecta linguagem se não fornecida
        if not language:
            language = self._detect_language(file_path)

        # Prepara prompt
        prompt = f"""Você é um assistente de código especializado em {language}.
Analise o código abaixo e forneça completions inteligentes para a posição do cursor.

Arquivo: {file_path}
Linguagem: {language}
Posição do cursor: {cursor_position}

Código:
```{language}
{code}
```

Forneça até {max_suggestions} sugestões de completion no formato JSON:
{{
    "suggestions": [
        {{
            "code": "código sugerido",
            "explanation": "explicação breve",
            "confidence": 0.95
        }}
    ]
}}
"""

        try:
            response = await self._call_model(prompt)
            suggestions = self._parse_suggestions(response, "completion", code, file_path)

            result = CodeAssistResponse(
                success=True,
                suggestions=suggestions,
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

            # Atualiza cache
            self._suggestion_cache[cache_key] = result
            self._stats["total_suggestions"] += len(suggestions)

            return result

        except Exception as e:
            logger.error(f"Completion failed: {e}")
            return CodeAssistResponse(
                success=False,
                error=str(e),
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    async def suggest_refactoring(
        self,
        code: str,
        file_path: str,
        focus_area: Optional[str] = None,
    ) -> CodeAssistResponse:
        """
        Sugere refatorações para o código.

        Args:
            code: Código a refatorar
            file_path: Caminho do arquivo
            focus_area: Área de foco (performance, readability, etc.)

        Returns:
            CodeAssistResponse com sugestões de refatoração
        """
        await self.initialize()
        start_time = datetime.now()

        language = self._detect_language(file_path)
        focus = focus_area or "qualidade geral"

        prompt = f"""Analise o código abaixo e sugira refatorações com foco em {focus}.

Arquivo: {file_path}
Linguagem: {language}

Código:
```{language}
{code}
```

Para cada sugestão, forneça:
1. O código original que pode ser melhorado
2. O código refatorado
3. Explicação do benefício
4. Nível de confiança (0-1)

Formato JSON:
{{
    "suggestions": [
        {{
            "original": "código original",
            "refactored": "código melhorado",
            "explanation": "por que é melhor",
            "confidence": 0.85,
            "type": "readability|performance|security|maintainability"
        }}
    ]
}}
"""

        try:
            response = await self._call_model(prompt)
            suggestions = self._parse_suggestions(response, "refactoring", code, file_path)

            return CodeAssistResponse(
                success=True,
                suggestions=suggestions,
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    async def validate_code(
        self,
        code: str,
        file_path: str,
    ) -> CodeAssistResponse:
        """
        Valida código e sugere correções.

        Args:
            code: Código a validar
            file_path: Caminho do arquivo

        Returns:
            CodeAssistResponse com problemas e correções
        """
        await self.initialize()
        start_time = datetime.now()

        language = self._detect_language(file_path)

        prompt = f"""Valide o código abaixo e identifique problemas potenciais.

Arquivo: {file_path}
Linguagem: {language}

Código:
```{language}
{code}
```

Identifique:
1. Erros de sintaxe
2. Bugs potenciais
3. Más práticas
4. Vulnerabilidades de segurança
5. Problemas de performance

Para cada problema, forneça uma correção sugerida.

Formato JSON:
{{
    "issues": [
        {{
            "type": "error|warning|info",
            "line": 10,
            "message": "descrição do problema",
            "original": "código problemático",
            "fix": "código corrigido",
            "explanation": "por que é um problema"
        }}
    ],
    "overall_quality": 0.75
}}
"""

        try:
            response = await self._call_model(prompt)
            suggestions = self._parse_validation(response, code, file_path)

            return CodeAssistResponse(
                success=True,
                suggestions=suggestions,
                explanation=f"Encontrados {len(suggestions)} problemas",
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    async def generate_documentation(
        self,
        code: str,
        file_path: str,
        style: str = "google",  # google, numpy, sphinx
    ) -> CodeAssistResponse:
        """
        Gera documentação para o código.

        Args:
            code: Código a documentar
            file_path: Caminho do arquivo
            style: Estilo de docstring

        Returns:
            CodeAssistResponse com código documentado
        """
        await self.initialize()
        start_time = datetime.now()

        language = self._detect_language(file_path)

        prompt = f"""Adicione documentação completa ao código abaixo.

Arquivo: {file_path}
Linguagem: {language}
Estilo de docstring: {style}

Código:
```{language}
{code}
```

Requisitos:
- Docstrings para todas as funções/classes/métodos
- Type hints se não existirem
- Comentários inline para lógica complexa
- Exemplos de uso quando apropriado

Retorne o código completo com documentação.
"""

        try:
            response = await self._call_model(prompt)

            suggestion = CodeSuggestion(
                suggestion_type="documentation",
                original_code=code,
                suggested_code=response,
                explanation="Código com documentação adicionada",
                confidence=0.9,
                file_path=file_path,
            )

            return CodeAssistResponse(
                success=True,
                suggestions=[suggestion],
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    async def explain_code(
        self,
        code: str,
        file_path: str,
        detail_level: str = "medium",  # brief, medium, detailed
    ) -> CodeAssistResponse:
        """
        Explica o que o código faz.

        Args:
            code: Código a explicar
            file_path: Caminho do arquivo
            detail_level: Nível de detalhe

        Returns:
            CodeAssistResponse com explicação
        """
        await self.initialize()
        start_time = datetime.now()

        language = self._detect_language(file_path)

        prompt = f"""Explique o código abaixo com nível de detalhe {detail_level}.

Arquivo: {file_path}
Linguagem: {language}

Código:
```{language}
{code}
```

Inclua:
- O que o código faz (propósito geral)
- Como funciona (lógica passo a passo)
- Pontos importantes de atenção
- Possíveis edge cases
"""

        try:
            response = await self._call_model(prompt)

            return CodeAssistResponse(
                success=True,
                explanation=response,
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    # ============================================================
    # COLLABORATION WITH CLAUDE CODE
    # ============================================================

    async def review_claude_output(
        self,
        original_request: str,
        claude_output: str,
        context_code: Optional[str] = None,
    ) -> CodeAssistResponse:
        """
        Revisa output do Claude Code antes de aplicar.

        Esta função permite que Gemini Code Assist valide
        as implementações do Claude Code, formando uma
        dupla de verificação.

        Args:
            original_request: Requisição original
            claude_output: Output do Claude Code
            context_code: Código de contexto

        Returns:
            CodeAssistResponse com validação
        """
        await self.initialize()

        prompt = f"""Você é um revisor de código. Valide a implementação do Claude Code.

REQUISIÇÃO ORIGINAL:
{original_request}

IMPLEMENTAÇÃO DO CLAUDE:
{claude_output}

{f"CONTEXTO:{context_code}" if context_code else ""}

Verifique:
1. A implementação atende aos requisitos?
2. O código segue boas práticas?
3. Existem bugs ou problemas potenciais?
4. Existem melhorias sugeridas?

Responda em JSON:
{{
    "approved": true/false,
    "score": 0-10,
    "issues": ["lista de problemas"],
    "improvements": ["lista de melhorias sugeridas"],
    "summary": "resumo da revisão"
}}
"""

        try:
            response = await self._call_model(prompt)

            return CodeAssistResponse(
                success=True,
                explanation=response,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    async def suggest_next_step(
        self,
        current_code: str,
        task_description: str,
        progress: str,
    ) -> CodeAssistResponse:
        """
        Sugere próximo passo para Claude Code.

        Gemini analisa o progresso e sugere o que
        Claude Code deve fazer em seguida.

        Args:
            current_code: Estado atual do código
            task_description: Descrição da tarefa
            progress: O que já foi feito

        Returns:
            CodeAssistResponse com sugestão de próximo passo
        """
        await self.initialize()

        prompt = f"""Analise o progresso da tarefa e sugira o próximo passo.

TAREFA:
{task_description}

PROGRESSO ATÉ AGORA:
{progress}

CÓDIGO ATUAL:
{current_code}

Sugira o próximo passo mais lógico e eficiente para completar a tarefa.
Seja específico sobre o que deve ser implementado.
"""

        try:
            response = await self._call_model(prompt)

            return CodeAssistResponse(
                success=True,
                explanation=response,
            )

        except Exception as e:
            return CodeAssistResponse(success=False, error=str(e))

    # ============================================================
    # PRIVATE METHODS
    # ============================================================

    async def _call_model(self, prompt: str) -> str:
        """Chama o modelo (Vertex ou GenAI)"""
        if self._vertex_client:
            response = await asyncio.to_thread(
                self._vertex_client.generate_content,
                prompt,
            )
            return response.text

        elif self._genai_client:
            response = await asyncio.to_thread(
                self._genai_client.generate_content,
                prompt,
            )
            return response.text

        else:
            raise RuntimeError("No AI client available")

    def _detect_language(self, file_path: str) -> str:
        """Detecta linguagem pelo caminho do arquivo"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".swift": "swift",
            ".kt": "kotlin",
        }

        ext = Path(file_path).suffix.lower()
        return extension_map.get(ext, "text")

    def _parse_suggestions(
        self,
        response: str,
        suggestion_type: str,
        original_code: str,
        file_path: str,
    ) -> List[CodeSuggestion]:
        """Parseia resposta do modelo em sugestões"""
        suggestions = []

        try:
            import json
            data = json.loads(response)

            for item in data.get("suggestions", []):
                suggestions.append(CodeSuggestion(
                    suggestion_type=suggestion_type,
                    original_code=item.get("original", original_code),
                    suggested_code=item.get("code", item.get("refactored", "")),
                    explanation=item.get("explanation", ""),
                    confidence=float(item.get("confidence", 0.5)),
                    file_path=file_path,
                ))

        except Exception as e:
            logger.warning(f"Failed to parse suggestions: {e}")
            # Retorna resposta raw como sugestão única
            suggestions.append(CodeSuggestion(
                suggestion_type=suggestion_type,
                original_code=original_code,
                suggested_code=response,
                explanation="Raw model response",
                confidence=0.5,
                file_path=file_path,
            ))

        return suggestions

    def _parse_validation(
        self,
        response: str,
        original_code: str,
        file_path: str,
    ) -> List[CodeSuggestion]:
        """Parseia resposta de validação"""
        suggestions = []

        try:
            import json
            data = json.loads(response)

            for issue in data.get("issues", []):
                suggestions.append(CodeSuggestion(
                    suggestion_type=f"fix:{issue.get('type', 'warning')}",
                    original_code=issue.get("original", ""),
                    suggested_code=issue.get("fix", ""),
                    explanation=issue.get("explanation", issue.get("message", "")),
                    confidence=0.8,
                    file_path=file_path,
                    line_start=issue.get("line"),
                ))

        except Exception:
            pass

        return suggestions

    # ============================================================
    # UTILITIES
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        return {
            **self._stats,
            "cache_size": len(self._suggestion_cache),
            "vertex_available": self._vertex_client is not None,
            "genai_available": self._genai_client is not None,
        }

    def clear_cache(self) -> None:
        """Limpa cache de sugestões"""
        self._suggestion_cache.clear()
        logger.info("Suggestion cache cleared")

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cliente"""
        await self.initialize()

        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "vertex_available": self._vertex_client is not None,
            "genai_available": self._genai_client is not None,
            "model": self.model,
        }
