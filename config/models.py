"""
O Construtor - Model Configuration
Configuração estratégica de modelos de IA para cada tarefa

ESTRATÉGIA DE MODELOS:
======================

1. CLAUDE OPUS 4.5 (claude-opus-4-5-20251101)
   - Arquitetura de sistemas complexos
   - Decisões de design de alto nível
   - Análise de trade-offs
   - Raciocínio profundo e planejamento

2. CLAUDE SONNET 4.5 (claude-sonnet-4-5-20250929)
   - Implementação de código
   - Refatoração
   - Code review detalhado
   - Debugging complexo

3. GEMINI 3 PRO PREVIEW (gemini-3-pro-preview)
   - Análise de performance (novo modelo, melhor raciocínio)
   - Otimização de algoritmos
   - Análise de segurança avançada
   - Tarefas que requerem raciocínio multimodal

4. GEMINI 2.5 PRO (gemini-2.5-pro)
   - Code review de alta qualidade
   - Análise de complexidade
   - DevOps e CI/CD
   - Documentação técnica

5. GEMINI 2.0 FLASH (gemini-2.0-flash-exp)
   - Chat interativo (baixa latência)
   - Tarefas rápidas
   - Streaming responses
   - Prototipagem rápida

6. GEMINI 2.5 FLASH (gemini-2.5-flash-preview-05-20)
   - Testes automatizados
   - Validações rápidas
   - Análises leves
   - Alta throughput

7. CLAUDE CODE (via CLI/Extension)
   - Implementação autônoma
   - Edição de arquivos
   - Execução de comandos
   - Fluxo de desenvolvimento completo

8. GEMINI CODE ASSIST (via Extension)
   - Autocompletar inteligente
   - Sugestões em tempo real
   - Documentação inline
   - Pair programming
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from enum import Enum


class TaskType(Enum):
    """Tipos de tarefas que o sistema pode executar"""
    # Planejamento e Design
    ARCHITECTURE = "architecture"
    SYSTEM_DESIGN = "system_design"
    API_DESIGN = "api_design"
    DATABASE_DESIGN = "database_design"

    # Implementação
    CODE_IMPLEMENTATION = "code_implementation"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    FEATURE_DEVELOPMENT = "feature_development"

    # Review e Análise
    CODE_REVIEW = "code_review"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLEXITY_ANALYSIS = "complexity_analysis"

    # Testing
    UNIT_TEST_GENERATION = "unit_test_generation"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "e2e_test"
    TEST_REVIEW = "test_review"

    # DevOps
    CI_CD_CONFIG = "ci_cd_config"
    DOCKER_CONFIG = "docker_config"
    KUBERNETES_CONFIG = "kubernetes_config"
    INFRASTRUCTURE = "infrastructure"

    # Documentação
    DOCUMENTATION = "documentation"
    API_DOCS = "api_docs"
    README_GENERATION = "readme_generation"
    CHANGELOG = "changelog"

    # Interação
    CHAT = "chat"
    QUICK_ANSWER = "quick_answer"
    EXPLANATION = "explanation"


class Provider(Enum):
    """Provedores de IA"""
    ANTHROPIC_VERTEX = "anthropic_vertex"  # Claude via Vertex AI
    ANTHROPIC_DIRECT = "anthropic_direct"  # Claude via API direta
    GOOGLE_VERTEX = "google_vertex"  # Gemini via Vertex AI
    GOOGLE_AI_STUDIO = "google_ai_studio"  # Gemini via AI Studio
    OPENAI_DIRECT = "openai_direct"  # GPT via API direta
    CLAUDE_CODE = "claude_code"  # Claude Code CLI
    GEMINI_CODE_ASSIST = "gemini_code_assist"  # Gemini Code Assist Extension


@dataclass
class ModelSpec:
    """Especificação de um modelo"""
    name: str
    provider: Provider
    max_tokens: int
    temperature: float = 0.7
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_code_execution: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    latency_class: Literal["low", "medium", "high"] = "medium"
    reasoning_depth: Literal["shallow", "medium", "deep"] = "medium"


@dataclass
class ModelConfig:
    """Configuração completa de modelos do O Construtor"""

    # ============================================================
    # MODELOS CLAUDE (Anthropic API Direta)
    # ============================================================

    CLAUDE_OPUS: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="claude-opus-4-5-20251101",
        provider=Provider.ANTHROPIC_DIRECT,
        max_tokens=8192,
        temperature=0.8,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        latency_class="high",
        reasoning_depth="deep"
    ))

    CLAUDE_SONNET: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="claude-sonnet-4-5-20250929",
        provider=Provider.ANTHROPIC_DIRECT,
        max_tokens=8192,
        temperature=0.5,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        latency_class="medium",
        reasoning_depth="medium"
    ))

    CLAUDE_HAIKU: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="claude-haiku-4-20250514",
        provider=Provider.ANTHROPIC_DIRECT,
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        latency_class="low",
        reasoning_depth="shallow"
    ))

    # ============================================================
    # MODELOS GEMINI (Google via Vertex AI / AI Studio)
    # ============================================================

    GEMINI_3_PRO: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gemini-3-pro-preview",
        provider=Provider.GOOGLE_VERTEX,
        max_tokens=8192,
        temperature=0.4,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=True,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        latency_class="medium",
        reasoning_depth="deep"  # Novo modelo com raciocínio melhorado
    ))

    GEMINI_25_PRO: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gemini-2.5-pro",
        provider=Provider.GOOGLE_VERTEX,
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=True,
        supports_code_execution=True,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        latency_class="medium",
        reasoning_depth="medium"
    ))

    GEMINI_20_FLASH: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gemini-2.0-flash-exp",
        provider=Provider.GOOGLE_AI_STUDIO,
        max_tokens=8192,
        temperature=0.7,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        latency_class="low",
        reasoning_depth="shallow"
    ))

    GEMINI_25_FLASH: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gemini-2.5-flash-preview-05-20",
        provider=Provider.GOOGLE_VERTEX,
        max_tokens=8192,
        temperature=0.5,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        latency_class="low",
        reasoning_depth="medium"
    ))

    # ============================================================
    # MODELOS GPT (OpenAI via API Direta)
    # ============================================================

    GPT_51: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gpt-5.1",
        provider=Provider.OPENAI_DIRECT,
        max_tokens=16384,
        temperature=0.7,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.010,
        cost_per_1k_output=0.030,
        latency_class="medium",
        reasoning_depth="deep"
    ))

    GPT_4O: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gpt-4o",
        provider=Provider.OPENAI_DIRECT,
        max_tokens=8192,
        temperature=0.5,
        supports_streaming=True,
        supports_vision=True,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.010,
        latency_class="medium",
        reasoning_depth="medium"
    ))

    GPT_4O_MINI: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gpt-4o-mini",
        provider=Provider.OPENAI_DIRECT,
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        latency_class="low",
        reasoning_depth="shallow"
    ))

    # ============================================================
    # FERRAMENTAS DE CÓDIGO (IDE Integration)
    # ============================================================

    CLAUDE_CODE: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="claude-code",
        provider=Provider.CLAUDE_CODE,
        max_tokens=16384,
        temperature=0.3,
        supports_streaming=True,
        supports_code_execution=True,
        latency_class="medium",
        reasoning_depth="deep"
    ))

    GEMINI_CODE_ASSIST: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="gemini-code-assist",
        provider=Provider.GEMINI_CODE_ASSIST,
        max_tokens=8192,
        temperature=0.2,
        supports_streaming=True,
        supports_code_execution=True,
        latency_class="low",
        reasoning_depth="medium"
    ))


# ============================================================
# MAPEAMENTO ESTRATÉGICO: TAREFA → MODELO(S)
# ============================================================

TASK_MODEL_MAPPING: Dict[TaskType, List[str]] = {
    # === ARQUITETURA E DESIGN (Requer raciocínio profundo) ===
    TaskType.ARCHITECTURE: ["CLAUDE_OPUS"],  # Melhor em design de sistemas
    TaskType.SYSTEM_DESIGN: ["CLAUDE_OPUS", "GEMINI_3_PRO"],  # Opus lidera, Gemini 3 valida
    TaskType.API_DESIGN: ["CLAUDE_SONNET", "GEMINI_25_PRO"],
    TaskType.DATABASE_DESIGN: ["CLAUDE_OPUS", "GEMINI_3_PRO"],

    # === IMPLEMENTAÇÃO (Claude Code + Gemini Code Assist juntos) ===
    TaskType.CODE_IMPLEMENTATION: ["CLAUDE_CODE", "GEMINI_CODE_ASSIST"],  # Dupla poderosa!
    TaskType.REFACTORING: ["CLAUDE_CODE", "GEMINI_3_PRO"],  # Claude Code executa, Gemini 3 sugere
    TaskType.BUG_FIX: ["CLAUDE_CODE", "GEMINI_CODE_ASSIST"],
    TaskType.FEATURE_DEVELOPMENT: ["CLAUDE_CODE", "GEMINI_CODE_ASSIST", "CLAUDE_SONNET"],

    # === REVIEW E ANÁLISE ===
    TaskType.CODE_REVIEW: ["GEMINI_3_PRO", "CLAUDE_SONNET"],  # Gemini 3 para análise profunda
    TaskType.SECURITY_ANALYSIS: ["GEMINI_3_PRO", "CLAUDE_OPUS"],  # Segurança requer raciocínio profundo
    TaskType.PERFORMANCE_ANALYSIS: ["GEMINI_3_PRO"],  # Gemini 3 é especialista em performance
    TaskType.COMPLEXITY_ANALYSIS: ["GEMINI_3_PRO", "GEMINI_25_PRO"],

    # === TESTING ===
    TaskType.UNIT_TEST_GENERATION: ["GEMINI_25_FLASH", "CLAUDE_CODE"],  # Flash para velocidade
    TaskType.INTEGRATION_TEST: ["GEMINI_25_PRO", "CLAUDE_SONNET"],
    TaskType.E2E_TEST: ["GEMINI_3_PRO", "CLAUDE_SONNET"],
    TaskType.TEST_REVIEW: ["GEMINI_25_PRO"],

    # === DEVOPS ===
    TaskType.CI_CD_CONFIG: ["GEMINI_25_PRO"],  # Jules engine
    TaskType.DOCKER_CONFIG: ["GEMINI_25_PRO", "GEMINI_25_FLASH"],
    TaskType.KUBERNETES_CONFIG: ["GEMINI_3_PRO", "GEMINI_25_PRO"],  # K8s é complexo
    TaskType.INFRASTRUCTURE: ["GEMINI_3_PRO", "CLAUDE_OPUS"],

    # === DOCUMENTAÇÃO ===
    TaskType.DOCUMENTATION: ["GEMINI_25_PRO", "CLAUDE_SONNET"],
    TaskType.API_DOCS: ["GEMINI_25_FLASH", "CLAUDE_SONNET"],
    TaskType.README_GENERATION: ["GEMINI_25_FLASH"],
    TaskType.CHANGELOG: ["GEMINI_25_FLASH"],

    # === INTERAÇÃO (Baixa latência) ===
    TaskType.CHAT: ["GEMINI_20_FLASH"],  # Mais rápido para chat
    TaskType.QUICK_ANSWER: ["GEMINI_25_FLASH"],
    TaskType.EXPLANATION: ["GEMINI_25_PRO", "CLAUDE_SONNET"],
}


# ============================================================
# ESTRATÉGIA DE FALLBACK
# ============================================================

MODEL_FALLBACK_CHAIN: Dict[str, List[str]] = {
    "CLAUDE_OPUS": ["CLAUDE_SONNET", "GEMINI_3_PRO"],
    "CLAUDE_SONNET": ["GEMINI_3_PRO", "GEMINI_25_PRO"],
    "GEMINI_3_PRO": ["GEMINI_25_PRO", "CLAUDE_SONNET"],
    "GEMINI_25_PRO": ["GEMINI_25_FLASH", "GEMINI_20_FLASH"],
    "GEMINI_20_FLASH": ["GEMINI_25_FLASH"],
    "GEMINI_25_FLASH": ["GEMINI_20_FLASH"],
    "CLAUDE_CODE": ["CLAUDE_SONNET", "GEMINI_CODE_ASSIST"],
    "GEMINI_CODE_ASSIST": ["GEMINI_25_FLASH", "CLAUDE_CODE"],
}


# ============================================================
# AGENTES E SEUS MODELOS PRIMÁRIOS
# ============================================================

@dataclass
class AgentConfig:
    """Configuração de um agente especializado"""
    name: str
    role: str
    primary_model: str
    secondary_models: List[str]
    tasks: List[TaskType]
    system_prompt_file: str
    emoji: str


AGENT_CONFIGS: Dict[str, AgentConfig] = {
    "architect": AgentConfig(
        name="Arquiteto",
        role="Design de sistemas e arquitetura",
        primary_model="CLAUDE_OPUS",
        secondary_models=["GEMINI_3_PRO"],
        tasks=[TaskType.ARCHITECTURE, TaskType.SYSTEM_DESIGN, TaskType.API_DESIGN, TaskType.DATABASE_DESIGN],
        system_prompt_file="architect.md",
        emoji="🏛️"
    ),
    "developer": AgentConfig(
        name="Desenvolvedor",
        role="Implementação e coding",
        primary_model="CLAUDE_CODE",
        secondary_models=["GEMINI_CODE_ASSIST", "CLAUDE_SONNET"],
        tasks=[TaskType.CODE_IMPLEMENTATION, TaskType.REFACTORING, TaskType.BUG_FIX, TaskType.FEATURE_DEVELOPMENT],
        system_prompt_file="developer.md",
        emoji="👨‍💻"
    ),
    "reviewer": AgentConfig(
        name="Revisor",
        role="Code review e análise de qualidade",
        primary_model="GEMINI_3_PRO",  # Gemini 3 Pro para análises profundas
        secondary_models=["CLAUDE_SONNET", "GEMINI_25_PRO"],
        tasks=[TaskType.CODE_REVIEW, TaskType.SECURITY_ANALYSIS, TaskType.PERFORMANCE_ANALYSIS],
        system_prompt_file="reviewer.md",
        emoji="🔍"
    ),
    "tester": AgentConfig(
        name="Tester",
        role="Geração e validação de testes",
        primary_model="GEMINI_25_FLASH",  # Flash para velocidade
        secondary_models=["GEMINI_25_PRO", "CLAUDE_CODE"],
        tasks=[TaskType.UNIT_TEST_GENERATION, TaskType.INTEGRATION_TEST, TaskType.E2E_TEST],
        system_prompt_file="tester.md",
        emoji="🧪"
    ),
    "devops": AgentConfig(
        name="Jules (DevOps)",
        role="CI/CD, infraestrutura e deploy",
        primary_model="GEMINI_25_PRO",
        secondary_models=["GEMINI_3_PRO", "GEMINI_25_FLASH"],
        tasks=[TaskType.CI_CD_CONFIG, TaskType.DOCKER_CONFIG, TaskType.KUBERNETES_CONFIG, TaskType.INFRASTRUCTURE],
        system_prompt_file="devops.md",
        emoji="🚀"
    ),
    "documenter": AgentConfig(
        name="Documentador",
        role="Documentação técnica",
        primary_model="GEMINI_25_PRO",
        secondary_models=["CLAUDE_SONNET", "GEMINI_25_FLASH"],
        tasks=[TaskType.DOCUMENTATION, TaskType.API_DOCS, TaskType.README_GENERATION, TaskType.CHANGELOG],
        system_prompt_file="documenter.md",
        emoji="📚"
    ),
    "security": AgentConfig(
        name="Especialista em Segurança",
        role="Análise de vulnerabilidades e segurança",
        primary_model="GEMINI_3_PRO",  # Gemini 3 Pro para análise de segurança
        secondary_models=["CLAUDE_OPUS"],
        tasks=[TaskType.SECURITY_ANALYSIS],
        system_prompt_file="security.md",
        emoji="🔐"
    ),
    "optimizer": AgentConfig(
        name="Otimizador",
        role="Performance e otimização",
        primary_model="GEMINI_3_PRO",  # Gemini 3 Pro é especialista em performance
        secondary_models=["GEMINI_25_PRO"],
        tasks=[TaskType.PERFORMANCE_ANALYSIS, TaskType.COMPLEXITY_ANALYSIS],
        system_prompt_file="optimizer.md",
        emoji="⚡"
    ),
}


def get_model_for_task(task: TaskType, config: Optional[ModelConfig] = None) -> List[ModelSpec]:
    """
    Retorna os modelos recomendados para uma tarefa específica.

    Args:
        task: Tipo de tarefa a ser executada
        config: Configuração de modelos (usa padrão se não fornecido)

    Returns:
        Lista de ModelSpec ordenada por prioridade
    """
    if config is None:
        config = ModelConfig()

    model_names = TASK_MODEL_MAPPING.get(task, ["GEMINI_25_PRO"])
    models = []

    for name in model_names:
        model = getattr(config, name, None)
        if model:
            models.append(model)

    return models


def get_fallback_models(model_name: str, config: Optional[ModelConfig] = None) -> List[ModelSpec]:
    """
    Retorna modelos de fallback para um modelo específico.

    Args:
        model_name: Nome do modelo que falhou
        config: Configuração de modelos

    Returns:
        Lista de ModelSpec de fallback
    """
    if config is None:
        config = ModelConfig()

    fallback_names = MODEL_FALLBACK_CHAIN.get(model_name, [])
    models = []

    for name in fallback_names:
        model = getattr(config, name, None)
        if model:
            models.append(model)

    return models


# ============================================================
# ESTRATÉGIA DE COLABORAÇÃO CLAUDE CODE + GEMINI CODE ASSIST
# ============================================================

COLLABORATION_STRATEGY = {
    "implementation": {
        "leader": "CLAUDE_CODE",  # Claude Code lidera implementação
        "assistant": "GEMINI_CODE_ASSIST",  # Gemini assiste com autocomplete
        "workflow": [
            "1. Claude Code analisa o requisito e planeja a implementação",
            "2. Gemini Code Assist sugere snippets e autocomplete em tempo real",
            "3. Claude Code implementa a lógica principal",
            "4. Gemini Code Assist valida sintaxe e sugere melhorias",
            "5. Claude Code finaliza e formata o código",
        ]
    },
    "debugging": {
        "leader": "CLAUDE_CODE",  # Claude Code para debugging profundo
        "assistant": "GEMINI_3_PRO",  # Gemini 3 para análise de root cause
        "workflow": [
            "1. Claude Code identifica o bug",
            "2. Gemini 3 Pro analisa possíveis causas raiz",
            "3. Claude Code implementa a correção",
            "4. Gemini 3 Pro valida que não há regressões",
        ]
    },
    "refactoring": {
        "leader": "GEMINI_3_PRO",  # Gemini 3 para sugestões de refactoring
        "assistant": "CLAUDE_CODE",  # Claude Code executa as mudanças
        "workflow": [
            "1. Gemini 3 Pro analisa o código e sugere refatorações",
            "2. Claude Code implementa as mudanças sugeridas",
            "3. Gemini Code Assist valida e sugere ajustes finais",
        ]
    },
    "review": {
        "leader": "GEMINI_3_PRO",  # Gemini 3 para review profundo
        "assistant": "CLAUDE_SONNET",  # Claude Sonnet para segunda opinião
        "workflow": [
            "1. Gemini 3 Pro faz análise de performance e complexidade",
            "2. Claude Sonnet faz análise de legibilidade e padrões",
            "3. Resultados são consolidados em um único review",
        ]
    }
}
