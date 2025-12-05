"""
O Construtor - Equipes de IA Estratégicas
==========================================

FILOSOFIA: Cada família de IA trabalha com sua própria equipe,
           otimizando custos e performance ao distribuir tarefas
           baseado nas forças de cada modelo.

ESTRUTURA DAS EQUIPES:
======================

🏛️ EQUIPE ANTHROPIC (Claude)
   ├─ Opus 4.5: Raciocínio profundo, arquitetura complexa
   ├─ Sonnet 4.5: Implementação, refatoração, code review
   └─ Haiku 4: Tarefas rápidas, validações, formatação

🔮 EQUIPE GOOGLE (Gemini)
   ├─ Gemini 3 Pro: Análise profunda, segurança, performance
   ├─ Gemini 2.5 Pro: DevOps, documentação, code review
   └─ Gemini Flash (2.5/2.0): Testes rápidos, chat, validações

🤖 EQUIPE OPENAI (GPT)
   ├─ GPT-5.1: Design de sistemas, decisões críticas
   ├─ GPT-4o: Implementação, debugging, análise
   └─ GPT-4o-mini: Tarefas simples, autocomplete, formatação
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class TeamType(Enum):
    """Tipos de equipes"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"


@dataclass
class TeamStrategy:
    """Estratégia de uma equipe"""
    name: str
    team_type: TeamType
    lead_model: str  # Modelo principal (raciocínio profundo)
    mid_model: str   # Modelo intermediário (implementação)
    fast_model: str  # Modelo rápido (tarefas simples)
    specialty: str   # Especialidade da equipe

    # Distribuição de tarefas por complexidade
    complex_tasks: List[str]  # Lead model
    medium_tasks: List[str]   # Mid model
    simple_tasks: List[str]   # Fast model


# ============================================================
# 🏛️ EQUIPE ANTHROPIC - ESPECIALISTA EM ARQUITETURA
# ============================================================

TEAM_ANTHROPIC = TeamStrategy(
    name="Equipe Claude (Anthropic)",
    team_type=TeamType.ANTHROPIC,
    lead_model="CLAUDE_OPUS",
    mid_model="CLAUDE_SONNET",
    fast_model="CLAUDE_HAIKU",
    specialty="Arquitetura de Sistemas, Design de APIs, Raciocínio Profundo",

    complex_tasks=[
        # Claude Opus 4.5 - Para o que REALMENTE importa
        "architecture",           # Design de sistemas complexos
        "system_design",         # Arquitetura de alto nível
        "database_design",       # Design de banco de dados
        "api_design",           # Design de APIs RESTful/GraphQL
        "complex_refactoring",  # Refatoração de arquitetura
        "technical_decisions",  # Decisões técnicas críticas
        "tradeoff_analysis",   # Análise de trade-offs
    ],

    medium_tasks=[
        # Claude Sonnet 4.5 - O trabalhador incansável
        "code_implementation",   # Implementação de features
        "refactoring",          # Refatoração de código
        "bug_fix",              # Correção de bugs complexos
        "code_review",          # Code review detalhado
        "feature_development",  # Desenvolvimento de features
        "integration",          # Integração de componentes
        "migration",            # Migração de código
        "documentation_complex", # Documentação técnica avançada
    ],

    simple_tasks=[
        # Claude Haiku 4 - Rápido e eficiente
        "code_formatting",      # Formatação de código
        "simple_validation",    # Validações simples
        "quick_fixes",          # Correções rápidas
        "linting",              # Lint e análise estática
        "simple_tests",         # Testes unitários simples
        "type_annotations",     # Adicionar type hints
        "docstrings",           # Adicionar docstrings
        "imports_organization", # Organizar imports
    ]
)


# ============================================================
# 🔮 EQUIPE GOOGLE - ESPECIALISTA EM ANÁLISE E DEVOPS
# ============================================================

TEAM_GOOGLE = TeamStrategy(
    name="Equipe Gemini (Google)",
    team_type=TeamType.GOOGLE,
    lead_model="GEMINI_3_PRO",
    mid_model="GEMINI_25_PRO",
    fast_model="GEMINI_25_FLASH",
    specialty="Performance, Segurança, DevOps, Análise Profunda",

    complex_tasks=[
        # Gemini 3 Pro - Analista supremo
        "performance_analysis",  # Análise de performance
        "security_analysis",     # Análise de segurança
        "complexity_analysis",   # Análise de complexidade
        "optimization",          # Otimização de algoritmos
        "profiling",            # Profiling de código
        "security_audit",       # Auditoria de segurança
        "vulnerability_scan",   # Scan de vulnerabilidades
        "code_quality_analysis", # Análise de qualidade
        "kubernetes_design",    # Design de K8s complexo
    ],

    medium_tasks=[
        # Gemini 2.5 Pro - DevOps e documentação
        "ci_cd_config",         # Configuração de CI/CD
        "docker_config",        # Dockerfiles e compose
        "infrastructure",       # Infraestrutura como código
        "monitoring_setup",     # Setup de monitoring
        "documentation",        # Documentação técnica
        "api_docs",            # Documentação de APIs
        "deployment_scripts",  # Scripts de deploy
        "environment_config",  # Configuração de ambientes
        "integration_test",    # Testes de integração
    ],

    simple_tasks=[
        # Gemini 2.5 Flash / 2.0 Flash - Velocidade
        "unit_test_generation", # Geração de testes unitários
        "quick_validation",     # Validações rápidas
        "chat_interaction",     # Interação com usuário
        "quick_answer",         # Respostas rápidas
        "readme_generation",    # Geração de README
        "changelog",            # Geração de CHANGELOG
        "simple_scripts",       # Scripts simples
        "config_validation",    # Validação de configs
    ]
)


# ============================================================
# 🤖 EQUIPE OPENAI - ESPECIALISTA EM CÓDIGO E DEBUGGING
# ============================================================

TEAM_OPENAI = TeamStrategy(
    name="Equipe GPT (OpenAI)",
    team_type=TeamType.OPENAI,
    lead_model="GPT_51",
    mid_model="GPT_4O",
    fast_model="GPT_4O_MINI",
    specialty="Implementação de Código, Debugging, Problem Solving",

    complex_tasks=[
        # GPT-5.1 - Solucionador de problemas complexos
        "complex_algorithms",   # Algoritmos complexos
        "system_integration",   # Integração de sistemas
        "complex_debugging",    # Debugging avançado
        "architectural_review", # Review de arquitetura
        "technical_planning",   # Planejamento técnico
        "design_patterns",      # Implementação de patterns
        "scalability_design",   # Design para escala
        "distributed_systems",  # Sistemas distribuídos
    ],

    medium_tasks=[
        # GPT-4o - Desenvolvedor sênior
        "feature_implementation", # Implementação de features
        "bug_investigation",      # Investigação de bugs
        "code_optimization",      # Otimização de código
        "test_development",       # Desenvolvimento de testes
        "api_implementation",     # Implementação de APIs
        "database_queries",       # Queries e otimização SQL
        "error_handling",         # Tratamento de erros
        "logging_implementation", # Implementação de logging
    ],

    simple_tasks=[
        # GPT-4o-mini - Assistente rápido
        "code_completion",      # Autocomplete de código
        "syntax_checking",      # Verificação de sintaxe
        "simple_refactoring",   # Refatoração simples
        "variable_naming",      # Sugestão de nomes
        "comment_generation",   # Geração de comentários
        "simple_formatting",    # Formatação simples
        "quick_suggestions",    # Sugestões rápidas
        "snippet_generation",   # Geração de snippets
    ]
)


# ============================================================
# MAPEAMENTO: AGENTE → EQUIPE PRIMÁRIA
# ============================================================

AGENT_TO_TEAM: Dict[str, TeamType] = {
    # Arquiteto: Anthropic (especialista em design)
    "architect": TeamType.ANTHROPIC,

    # Desenvolvedor: OpenAI (melhor em implementação)
    "developer": TeamType.OPENAI,

    # Revisor: Google (melhor em análise)
    "reviewer": TeamType.GOOGLE,

    # Tester: Google (rápido e eficiente)
    "tester": TeamType.GOOGLE,

    # DevOps: Google (especialista em infra)
    "devops": TeamType.GOOGLE,

    # Documentador: Anthropic (melhor escrita)
    "documenter": TeamType.ANTHROPIC,

    # Segurança: Google (melhor análise de segurança)
    "security": TeamType.GOOGLE,

    # Otimizador: Google (especialista em performance)
    "optimizer": TeamType.GOOGLE,
}


# ============================================================
# DISTRIBUIÇÃO INTELIGENTE POR COMPLEXIDADE
# ============================================================

def get_model_for_task(agent: str, task_complexity: str) -> str:
    """
    Retorna o modelo apropriado baseado no agente e complexidade.

    Args:
        agent: Nome do agente (architect, developer, etc.)
        task_complexity: "complex", "medium", "simple"

    Returns:
        Nome do modelo (CLAUDE_OPUS, GEMINI_3_PRO, etc.)

    Exemplo:
        >>> get_model_for_task("architect", "complex")
        "CLAUDE_OPUS"
        >>> get_model_for_task("architect", "simple")
        "CLAUDE_HAIKU"
    """
    team_type = AGENT_TO_TEAM.get(agent, TeamType.ANTHROPIC)

    if team_type == TeamType.ANTHROPIC:
        team = TEAM_ANTHROPIC
    elif team_type == TeamType.GOOGLE:
        team = TEAM_GOOGLE
    else:  # OPENAI
        team = TEAM_OPENAI

    if task_complexity == "complex":
        return team.lead_model
    elif task_complexity == "medium":
        return team.mid_model
    else:  # simple
        return team.fast_model


def estimate_task_complexity(task_type: str, task_description: str = "") -> str:
    """
    Estima a complexidade de uma tarefa.

    Args:
        task_type: Tipo da tarefa
        task_description: Descrição da tarefa (opcional)

    Returns:
        "complex", "medium", ou "simple"
    """
    # Palavras-chave que indicam complexidade
    complex_keywords = [
        "architecture", "design", "system", "distributed", "scalable",
        "complex", "advanced", "critical", "integration", "migration"
    ]

    medium_keywords = [
        "implement", "feature", "refactor", "review", "test",
        "debug", "optimize", "configure", "setup"
    ]

    simple_keywords = [
        "format", "lint", "validate", "quick", "simple",
        "add", "fix", "update", "check"
    ]

    # Verificar no tipo e descrição
    full_text = (task_type + " " + task_description).lower()

    if any(keyword in full_text for keyword in complex_keywords):
        return "complex"
    elif any(keyword in full_text for keyword in simple_keywords):
        return "simple"
    else:
        return "medium"


# ============================================================
# ESTATÍSTICAS E MONITORAMENTO
# ============================================================

def get_team_stats() -> Dict:
    """Retorna estatísticas das equipes"""
    return {
        "teams": {
            "anthropic": {
                "name": TEAM_ANTHROPIC.name,
                "specialty": TEAM_ANTHROPIC.specialty,
                "models": {
                    "lead": TEAM_ANTHROPIC.lead_model,
                    "mid": TEAM_ANTHROPIC.mid_model,
                    "fast": TEAM_ANTHROPIC.fast_model,
                },
                "task_distribution": {
                    "complex": len(TEAM_ANTHROPIC.complex_tasks),
                    "medium": len(TEAM_ANTHROPIC.medium_tasks),
                    "simple": len(TEAM_ANTHROPIC.simple_tasks),
                }
            },
            "google": {
                "name": TEAM_GOOGLE.name,
                "specialty": TEAM_GOOGLE.specialty,
                "models": {
                    "lead": TEAM_GOOGLE.lead_model,
                    "mid": TEAM_GOOGLE.mid_model,
                    "fast": TEAM_GOOGLE.fast_model,
                },
                "task_distribution": {
                    "complex": len(TEAM_GOOGLE.complex_tasks),
                    "medium": len(TEAM_GOOGLE.medium_tasks),
                    "simple": len(TEAM_GOOGLE.simple_tasks),
                }
            },
            "openai": {
                "name": TEAM_OPENAI.name,
                "specialty": TEAM_OPENAI.specialty,
                "models": {
                    "lead": TEAM_OPENAI.lead_model,
                    "mid": TEAM_OPENAI.mid_model,
                    "fast": TEAM_OPENAI.fast_model,
                },
                "task_distribution": {
                    "complex": len(TEAM_OPENAI.complex_tasks),
                    "medium": len(TEAM_OPENAI.medium_tasks),
                    "simple": len(TEAM_OPENAI.simple_tasks),
                }
            }
        },
        "agent_assignments": AGENT_TO_TEAM
    }


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("O CONSTRUTOR - EQUIPES DE IA ESTRATEGICAS")
    print("=" * 60)

    # Mostrar estatísticas
    stats = get_team_stats()

    for team_key, team_data in stats["teams"].items():
        print(f"\n{team_data['name']}")
        print(f"Especialidade: {team_data['specialty']}")
        print(f"Modelos:")
        print(f"  - Lead:  {team_data['models']['lead']}")
        print(f"  - Mid:   {team_data['models']['mid']}")
        print(f"  - Fast:  {team_data['models']['fast']}")
        print(f"Tarefas: {team_data['task_distribution']['complex']} complexas, "
              f"{team_data['task_distribution']['medium']} médias, "
              f"{team_data['task_distribution']['simple']} simples")

    # Exemplo de uso
    print("\n" + "=" * 60)
    print("EXEMPLO DE DISTRIBUIÇÃO:")
    print("=" * 60)

    examples = [
        ("architect", "Desenhar arquitetura de microserviços"),
        ("developer", "Implementar endpoint REST simples"),
        ("reviewer", "Analisar segurança do código"),
        ("tester", "Gerar testes unitários básicos"),
    ]

    for agent, task in examples:
        complexity = estimate_task_complexity(agent, task)
        model = get_model_for_task(agent, complexity)
        print(f"\nAgente: {agent}")
        print(f"Tarefa: {task}")
        print(f"Complexidade: {complexity}")
        print(f"Modelo: {model}")
