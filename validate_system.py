"""
Script de Validação do Sistema
Verifica se todos os componentes estão funcionando
"""
import asyncio
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_success(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")


def print_error(msg):
    print(f"{RED}[ERRO]{RESET} {msg}")


def print_warning(msg):
    print(f"{YELLOW}[AVISO]{RESET} {msg}")


def print_header(msg):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")


async def validate_environment():
    """Valida variáveis de ambiente"""
    print_header("1. Validando Variáveis de Ambiente")

    required_vars = ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    optional_vars = ["GITHUB_TOKEN", "GCP_PROJECT_ID", "SUPABASE_URL"]

    all_valid = True

    for var in required_vars:
        if os.getenv(var):
            print_success(f"{var} configurada")
        else:
            print_error(f"{var} NÃO configurada (obrigatória)")
            all_valid = False

    for var in optional_vars:
        if os.getenv(var):
            print_success(f"{var} configurada")
        else:
            print_warning(f"{var} não configurada (opcional)")

    return all_valid


async def validate_integrations():
    """Valida integrações"""
    print_header("2. Validando Integrações")

    # Claude Code Client
    try:
        from integrations.claude_code_client import ClaudeCodeClient
        client = ClaudeCodeClient()
        health = await client.health_check()
        if health['status'] == 'healthy':
            print_success("ClaudeCodeClient OK")
        else:
            print_error("ClaudeCodeClient com problemas")
    except Exception as e:
        print_error(f"ClaudeCodeClient: {e}")

    # Gemini Code Assist
    try:
        from integrations.gemini_code_assist import GeminiCodeAssistClient
        client = GeminiCodeAssistClient()
        health = await client.health_check()
        if health['status'] == 'healthy':
            print_success("GeminiCodeAssistClient OK")
        else:
            print_error("GeminiCodeAssistClient com problemas")
    except Exception as e:
        print_error(f"GeminiCodeAssistClient: {e}")

    # GitHub Client
    try:
        from integrations.github_client import GitHubClient
        if os.getenv("GITHUB_TOKEN"):
            client = GitHubClient()
            print_success("GitHubClient OK")
        else:
            print_warning("GitHubClient: Token não configurado")
    except Exception as e:
        print_error(f"GitHubClient: {e}")


async def validate_core():
    """Valida componentes core"""
    print_header("3. Validando Componentes Core")

    try:
        from core.event_bus import EventBus
        bus = EventBus()
        print_success("EventBus OK")
    except Exception as e:
        print_error(f"EventBus: {e}")

    try:
        from core.memory_store import MemoryStore
        store = MemoryStore()
        print_success("MemoryStore OK")
    except Exception as e:
        print_error(f"MemoryStore: {e}")

    try:
        from core.task_queue import TaskQueue
        queue = TaskQueue()
        print_success("TaskQueue OK")
    except Exception as e:
        print_error(f"TaskQueue: {e}")

    try:
        from core.orchestrator import Orchestrator
        print_success("Orchestrator OK")
    except Exception as e:
        print_error(f"Orchestrator: {e}")


async def validate_api():
    """Valida API"""
    print_header("4. Validando API")

    try:
        from api.main import app
        print_success("API main OK")
    except Exception as e:
        print_error(f"API: {e}")

    try:
        from api.routes import health, tasks, agents, workflows
        print_success("API routes OK")
    except Exception as e:
        print_error(f"API routes: {e}")


def validate_files():
    """Valida arquivos importantes"""
    print_header("5. Validando Arquivos")

    important_files = [
        "api/main.py",
        "app_advanced.py",
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        "Makefile",
        "README.md",
        "QUICK_START.md",
        ".gitignore",
    ]

    for file in important_files:
        if os.path.exists(file):
            print_success(f"{file}")
        else:
            print_error(f"{file} não encontrado")


def validate_dependencies():
    """Valida dependências instaladas"""
    print_header("6. Validando Dependências")

    required_packages = {
        "fastapi": "fastapi",
        "streamlit": "streamlit",
        "anthropic": "anthropic",
        "google-generativeai": "google.generativeai",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic",
        "pytest": "pytest",
    }

    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} nao instalado")


async def main():
    """Main validation"""
    print(f"\n{BOLD}{'='*60}")
    print("O CONSTRUTOR - VALIDAÇÃO DO SISTEMA")
    print(f"{'='*60}{RESET}\n")

    env_ok = await validate_environment()
    await validate_integrations()
    await validate_core()
    await validate_api()
    validate_files()
    validate_dependencies()

    print_header("RESUMO")

    if env_ok:
        print(f"{GREEN}{BOLD}[OK] Sistema pronto para uso!{RESET}")
        print("\nProximos passos:")
        print("1. Inicie a API: uvicorn api.main:app --reload")
        print("2. Inicie a Interface: streamlit run app_advanced.py")
        print("3. Ou use Docker: docker-compose up")
    else:
        print(f"{RED}{BOLD}[ERRO] Sistema com problemas{RESET}")
        print("\nConfigure as variaveis de ambiente obrigatorias no .env")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
