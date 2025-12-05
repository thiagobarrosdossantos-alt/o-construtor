"""
O Construtor - Claude Code Client
Integração com Claude Code CLI para execução autônoma de código

Claude Code é a ferramenta preferencial para implementação,
oferecendo capacidades de:
- Leitura e escrita de arquivos
- Execução de comandos
- Navegação no codebase
- Implementação autônoma de features
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ClaudeCodeResponse:
    """Resposta do Claude Code"""
    success: bool
    output: str
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0


@dataclass
class ClaudeCodeTask:
    """Uma tarefa para Claude Code executar"""
    prompt: str
    working_directory: str
    allowed_tools: List[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep"
    ])
    max_tokens: int = 16384
    timeout_seconds: int = 300
    context_files: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)


class ClaudeCodeClient:
    """
    Cliente para integração com Claude Code

    Permite executar tarefas de desenvolvimento de forma autônoma
    usando Claude Code CLI ou SDK.

    Funcionalidades:
    - Execução de prompts com ferramentas
    - Implementação de features
    - Refatoração de código
    - Debugging e correção de bugs
    - Execução de testes

    Uso:
        client = ClaudeCodeClient(working_dir="/path/to/project")
        await client.initialize()

        result = await client.execute_task(ClaudeCodeTask(
            prompt="Implemente uma função que calcula fibonacci",
            working_directory="/path/to/project",
        ))
    """

    def __init__(
        self,
        working_dir: str = ".",
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        use_cli: bool = True,
    ):
        self.working_dir = Path(working_dir).resolve()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.use_cli = use_cli

        self._initialized = False
        self._cli_available = False
        self._sdk_client: Optional[Any] = None

        # Estatísticas
        self._stats = {
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

        logger.info(f"ClaudeCodeClient initialized for {self.working_dir}")

    async def initialize(self) -> bool:
        """
        Inicializa o cliente, verificando disponibilidade do CLI/SDK.

        Returns:
            True se inicializado com sucesso
        """
        if self._initialized:
            return True

        # Verifica se CLI está disponível
        self._cli_available = await self._check_cli_available()

        if self._cli_available:
            logger.info("Claude Code CLI disponível")
        else:
            logger.warning("Claude Code CLI não encontrado, usando SDK")
            # Inicializa SDK como fallback
            await self._initialize_sdk()

        self._initialized = True
        return True

    async def _check_cli_available(self) -> bool:
        """Verifica se Claude Code CLI está instalado"""
        try:
            process = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()

            if process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Claude Code CLI version: {version}")
                return True
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"CLI check failed: {e}")

        return False

    async def _initialize_sdk(self) -> None:
        """Inicializa SDK Anthropic como fallback"""
        try:
            from anthropic import Anthropic
            self._sdk_client = Anthropic(api_key=self.api_key)
            logger.info("Anthropic SDK initialized")
        except ImportError:
            logger.error("anthropic package not installed")
        except Exception as e:
            logger.error(f"SDK initialization failed: {e}")

    async def execute_task(self, task: ClaudeCodeTask) -> ClaudeCodeResponse:
        """
        Executa uma tarefa usando Claude Code.

        Args:
            task: Tarefa a ser executada

        Returns:
            ClaudeCodeResponse com resultado
        """
        await self.initialize()

        start_time = datetime.now()
        self._stats["tasks_executed"] += 1

        logger.info(f"Executing Claude Code task: {task.prompt[:100]}...")

        try:
            if self._cli_available and self.use_cli:
                result = await self._execute_via_cli(task)
            else:
                result = await self._execute_via_sdk(task)

            result.duration_seconds = (datetime.now() - start_time).total_seconds()

            if result.success:
                self._stats["tasks_succeeded"] += 1
            else:
                self._stats["tasks_failed"] += 1

            self._stats["total_tokens"] += result.tokens_used

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self._stats["tasks_failed"] += 1

            return ClaudeCodeResponse(
                success=False,
                output="",
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

    async def _execute_via_cli(self, task: ClaudeCodeTask) -> ClaudeCodeResponse:
        """
        Executa tarefa via Claude Code CLI.

        Args:
            task: Tarefa a executar

        Returns:
            ClaudeCodeResponse
        """
        # Prepara comando
        cmd = [
            "claude",
            "--print",  # Output para stdout
            "--output-format", "json",
            "--max-tokens", str(task.max_tokens),
        ]

        # Adiciona arquivos de contexto
        for ctx_file in task.context_files:
            cmd.extend(["--add-file", ctx_file])

        # Adiciona allowed tools
        allowed = ",".join(task.allowed_tools)
        cmd.extend(["--allowedTools", allowed])

        # Prompt
        cmd.extend(["--prompt", task.prompt])

        logger.debug(f"CLI command: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task.working_directory,
                env={**os.environ, **task.environment},
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout_seconds,
            )

            output = stdout.decode()

            if process.returncode == 0:
                # Tenta parsear JSON
                try:
                    result_data = json.loads(output)
                    return ClaudeCodeResponse(
                        success=True,
                        output=result_data.get("result", output),
                        files_modified=result_data.get("files_modified", []),
                        files_created=result_data.get("files_created", []),
                        commands_executed=result_data.get("commands", []),
                        tokens_used=result_data.get("tokens", 0),
                    )
                except json.JSONDecodeError:
                    return ClaudeCodeResponse(
                        success=True,
                        output=output,
                    )
            else:
                return ClaudeCodeResponse(
                    success=False,
                    output=output,
                    error=stderr.decode() if stderr else "Command failed",
                )

        except asyncio.TimeoutError:
            return ClaudeCodeResponse(
                success=False,
                output="",
                error=f"Timeout after {task.timeout_seconds} seconds",
            )

    async def _execute_via_sdk(self, task: ClaudeCodeTask) -> ClaudeCodeResponse:
        """
        Executa tarefa via Anthropic SDK (fallback).

        Args:
            task: Tarefa a executar

        Returns:
            ClaudeCodeResponse
        """
        if not self._sdk_client:
            return ClaudeCodeResponse(
                success=False,
                output="",
                error="SDK not initialized",
            )

        try:
            # Prepara contexto
            context_content = ""
            for ctx_file in task.context_files:
                file_path = Path(task.working_directory) / ctx_file
                if file_path.exists():
                    content = file_path.read_text()
                    context_content += f"\n\n--- {ctx_file} ---\n{content}"

            # Cria mensagem
            full_prompt = task.prompt
            if context_content:
                full_prompt = f"Context files:{context_content}\n\nTask: {task.prompt}"

            response = self._sdk_client.messages.create(
                model=self.model,
                max_tokens=task.max_tokens,
                messages=[{"role": "user", "content": full_prompt}],
            )

            output = response.content[0].text if response.content else ""

            return ClaudeCodeResponse(
                success=True,
                output=output,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            )

        except Exception as e:
            return ClaudeCodeResponse(
                success=False,
                output="",
                error=str(e),
            )

    # ============================================================
    # HIGH-LEVEL METHODS
    # ============================================================

    async def implement_feature(
        self,
        description: str,
        context_files: Optional[List[str]] = None,
        target_files: Optional[List[str]] = None,
    ) -> ClaudeCodeResponse:
        """
        Implementa uma feature completa.

        Args:
            description: Descrição da feature
            context_files: Arquivos para contexto
            target_files: Arquivos alvo da implementação

        Returns:
            ClaudeCodeResponse
        """
        prompt = f"""Implemente a seguinte feature:

{description}

Requisitos:
- Siga os padrões do projeto existente
- Adicione type hints
- Escreva código limpo e bem documentado
- Considere edge cases e tratamento de erros
"""

        if target_files:
            prompt += f"\nArquivos alvo: {', '.join(target_files)}"

        task = ClaudeCodeTask(
            prompt=prompt,
            working_directory=str(self.working_dir),
            context_files=context_files or [],
        )

        return await self.execute_task(task)

    async def fix_bug(
        self,
        bug_description: str,
        error_message: Optional[str] = None,
        affected_files: Optional[List[str]] = None,
    ) -> ClaudeCodeResponse:
        """
        Corrige um bug.

        Args:
            bug_description: Descrição do bug
            error_message: Mensagem de erro se disponível
            affected_files: Arquivos afetados

        Returns:
            ClaudeCodeResponse
        """
        prompt = f"""Corrija o seguinte bug:

Descrição: {bug_description}
"""
        if error_message:
            prompt += f"\nErro: {error_message}"

        if affected_files:
            prompt += f"\nArquivos afetados: {', '.join(affected_files)}"

        prompt += """

Passos:
1. Analise o código para encontrar a causa raiz
2. Implemente a correção
3. Verifique que não introduz regressões
"""

        task = ClaudeCodeTask(
            prompt=prompt,
            working_directory=str(self.working_dir),
            context_files=affected_files or [],
        )

        return await self.execute_task(task)

    async def refactor_code(
        self,
        file_path: str,
        refactoring_goals: str,
    ) -> ClaudeCodeResponse:
        """
        Refatora código.

        Args:
            file_path: Arquivo a refatorar
            refactoring_goals: Objetivos da refatoração

        Returns:
            ClaudeCodeResponse
        """
        prompt = f"""Refatore o arquivo {file_path} com os seguintes objetivos:

{refactoring_goals}

Requisitos:
- Mantenha o comportamento existente
- Melhore legibilidade e manutenibilidade
- Aplique design patterns apropriados
- Não altere a API pública sem necessidade
"""

        task = ClaudeCodeTask(
            prompt=prompt,
            working_directory=str(self.working_dir),
            context_files=[file_path],
        )

        return await self.execute_task(task)

    async def generate_tests(
        self,
        target_file: str,
        test_framework: str = "pytest",
    ) -> ClaudeCodeResponse:
        """
        Gera testes para um arquivo.

        Args:
            target_file: Arquivo para gerar testes
            test_framework: Framework de teste (pytest, unittest)

        Returns:
            ClaudeCodeResponse
        """
        prompt = f"""Gere testes abrangentes para o arquivo {target_file}.

Framework: {test_framework}

Requisitos:
- Teste todos os métodos públicos
- Inclua happy paths e edge cases
- Teste tratamento de erros
- Use mocks quando apropriado
- Siga o padrão AAA (Arrange, Act, Assert)
"""

        task = ClaudeCodeTask(
            prompt=prompt,
            working_directory=str(self.working_dir),
            context_files=[target_file],
        )

        return await self.execute_task(task)

    async def run_command(
        self,
        command: str,
        description: Optional[str] = None,
    ) -> ClaudeCodeResponse:
        """
        Executa um comando via Claude Code.

        Args:
            command: Comando a executar
            description: Descrição do que o comando faz

        Returns:
            ClaudeCodeResponse
        """
        prompt = f"Execute o comando: {command}"
        if description:
            prompt += f"\n\nDescrição: {description}"

        task = ClaudeCodeTask(
            prompt=prompt,
            working_directory=str(self.working_dir),
            allowed_tools=["Bash"],
        )

        return await self.execute_task(task)

    # ============================================================
    # UTILITIES
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        return {
            **self._stats,
            "cli_available": self._cli_available,
            "sdk_available": self._sdk_client is not None,
            "working_dir": str(self.working_dir),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cliente"""
        await self.initialize()

        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "cli_available": self._cli_available,
            "sdk_available": self._sdk_client is not None,
            "working_directory_exists": self.working_dir.exists(),
        }
