"""
O Construtor - AI Client
Cliente unificado para modelos de IA

Suporta:
- Claude (Anthropic) via API direta
- Gemini via Vertex AI
- Outros modelos disponíveis no Vertex
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Provedores de modelo disponíveis"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class ModelResponse:
    """Resposta de um modelo"""
    success: bool
    content: str
    model: str
    provider: ModelProvider
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VertexAIClient:
    """
    Cliente Unificado para modelos de IA

    Fornece acesso a múltiplos modelos através de uma interface única:
    - Claude Opus 4.5, Sonnet 4.5 (via Anthropic API direta)
    - Gemini 3 Pro Preview, 2.5 Pro, 2.5 Flash, 2.0 Flash (via Vertex AI)

    Uso:
        client = VertexAIClient()
        await client.initialize()

        response = await client.generate(
            prompt="Explique recursão",
            model="claude-opus-4-5-20251101",
        )
    """

    # Mapeamento de modelos para providers
    MODEL_PROVIDERS = {
        # Claude models (Anthropic API direta)
        "claude-opus-4-5-20251101": ModelProvider.ANTHROPIC,
        "claude-sonnet-4-5-20250929": ModelProvider.ANTHROPIC,
        # Gemini models (Vertex AI)
        "gemini-3-pro-preview": ModelProvider.GOOGLE,
        "gemini-2.5-pro": ModelProvider.GOOGLE,
        "gemini-2.5-flash-preview-05-20": ModelProvider.GOOGLE,
        "gemini-2.0-flash-exp": ModelProvider.GOOGLE,
    }

    def __init__(
        self,
        project_id: Optional[str] = None,
        region: str = "us-central1",
        anthropic_api_key: Optional[str] = None,
    ):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "gen-lang-client-0394737170")
        self.region = region
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        self._anthropic_client: Optional[Any] = None
        self._vertex_initialized = False

        # Estatísticas
        self._stats = {
            "total_requests": 0,
            "by_model": {},
            "total_tokens": 0,
            "total_cost": 0.0,
        }

        logger.info(f"AIClient initialized for project {self.project_id}")

    async def initialize(self) -> bool:
        """Inicializa clientes"""
        if self._vertex_initialized:
            return True

        try:
            # Inicializa Vertex AI para Gemini
            import vertexai
            vertexai.init(project=self.project_id, location=self.region)
            logger.info("Vertex AI initialized for Gemini")

            # Inicializa Anthropic direta para Claude
            try:
                from anthropic import Anthropic
                if self.anthropic_api_key:
                    self._anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                    logger.info("Anthropic client initialized (direct API)")
                else:
                    logger.warning("ANTHROPIC_API_KEY not found - Claude models unavailable")
            except Exception as e:
                logger.warning(f"Anthropic client init failed: {e}")

            self._vertex_initialized = True
            return True

        except Exception as e:
            logger.error(f"AI Client initialization failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> ModelResponse:
        """
        Gera resposta usando modelo especificado.

        Args:
            prompt: Prompt do usuário
            model: Nome do modelo
            system_prompt: System prompt opcional
            max_tokens: Máximo de tokens na resposta
            temperature: Temperatura (criatividade)
            stop_sequences: Sequências de parada

        Returns:
            ModelResponse
        """
        await self.initialize()

        start_time = datetime.now()
        self._stats["total_requests"] += 1

        provider = self.MODEL_PROVIDERS.get(model)
        if not provider:
            return ModelResponse(
                success=False,
                content="",
                model=model,
                provider=ModelProvider.GOOGLE,
                error=f"Unknown model: {model}",
            )

        try:
            if provider == ModelProvider.ANTHROPIC:
                response = await self._call_claude(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response = await self._call_gemini(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            response.latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Atualiza estatísticas
            self._stats["by_model"][model] = self._stats["by_model"].get(model, 0) + 1
            self._stats["total_tokens"] += response.tokens_input + response.tokens_output

            return response

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ModelResponse(
                success=False,
                content="",
                model=model,
                provider=provider,
                error=str(e),
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

    async def _call_claude(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> ModelResponse:
        """Chama modelo Claude via Anthropic API direta"""
        if not self._anthropic_client:
            raise RuntimeError("Anthropic client not initialized. Check ANTHROPIC_API_KEY.")

        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Claude Opus suporta temperature até 1.0
        if temperature <= 1.0:
            kwargs["temperature"] = temperature

        response = await asyncio.to_thread(
            self._anthropic_client.messages.create,
            **kwargs,
        )

        content = response.content[0].text if response.content else ""

        return ModelResponse(
            success=True,
            content=content,
            model=model,
            provider=ModelProvider.ANTHROPIC,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
        )

    async def _call_gemini(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> ModelResponse:
        """Chama modelo Gemini via Vertex AI"""
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        from google.cloud.aiplatform_v1beta1.types import SafetySetting, HarmCategory

        # Configuração de geração
        generation_config = GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        # Safety settings
        safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ]

        # Cria modelo
        if system_prompt:
            gemini_model = GenerativeModel(
                model,
                system_instruction=[system_prompt],
            )
        else:
            gemini_model = GenerativeModel(model)

        # Gera resposta
        response = await asyncio.to_thread(
            gemini_model.generate_content,
            prompt,
            generation_config=generation_config,
        )

        return ModelResponse(
            success=True,
            content=response.text,
            model=model,
            provider=ModelProvider.GOOGLE,
            tokens_input=response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            tokens_output=response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
        )

    async def generate_streaming(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Gera resposta com streaming.

        Yields:
            Chunks de texto
        """
        await self.initialize()

        provider = self.MODEL_PROVIDERS.get(model)
        if not provider:
            yield f"Error: Unknown model {model}"
            return

        # TODO: Implementar streaming real
        response = await self.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Simula streaming
        for word in response.content.split():
            yield word + " "
            await asyncio.sleep(0.01)

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Retorna modelos disponíveis e suas características"""
        return {
            "claude-opus-4-5-20251101": {
                "provider": "anthropic",
                "type": "reasoning",
                "max_tokens": 8192,
                "best_for": ["architecture", "complex analysis", "deep reasoning"],
            },
            "claude-sonnet-4-5-20250929": {
                "provider": "anthropic",
                "type": "balanced",
                "max_tokens": 8192,
                "best_for": ["code implementation", "general tasks"],
            },
            "gemini-3-pro-preview": {
                "provider": "google",
                "type": "reasoning",
                "max_tokens": 8192,
                "best_for": ["performance analysis", "security", "code review"],
            },
            "gemini-2.5-pro": {
                "provider": "google",
                "type": "balanced",
                "max_tokens": 8192,
                "best_for": ["code review", "devops", "documentation"],
            },
            "gemini-2.5-flash-preview-05-20": {
                "provider": "google",
                "type": "fast",
                "max_tokens": 8192,
                "best_for": ["testing", "quick tasks", "high throughput"],
            },
            "gemini-2.0-flash-exp": {
                "provider": "google",
                "type": "fast",
                "max_tokens": 8192,
                "best_for": ["chat", "low latency", "streaming"],
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        return {
            **self._stats,
            "vertex_initialized": self._vertex_initialized,
            "anthropic_available": self._anthropic_client is not None,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cliente"""
        await self.initialize()

        return {
            "status": "healthy" if self._vertex_initialized else "unhealthy",
            "project_id": self.project_id,
            "region": self.region,
            "vertex_initialized": self._vertex_initialized,
            "anthropic_available": self._anthropic_client is not None,
            "available_models": list(self.MODEL_PROVIDERS.keys()),
        }
