"""
O Construtor - Developer Agent
Agente especializado em implementação de código

Usa: Claude Code (implementação) + Gemini Code Assist (sugestões)
"""

import logging
from typing import Any, Dict, List, Optional

from agents.base_agent import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentResponse,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent):
    """
    Agente Desenvolvedor - Especialista em Implementação

    Responsabilidades:
    - Implementação de código
    - Refatoração
    - Debugging
    - Correção de bugs
    - Integração de features

    Modelo Primário: Claude Code (implementação autônoma)
    Modelo Secundário: Gemini Code Assist (autocompletar)

    Estratégia de Colaboração:
    - Claude Code lidera a implementação
    - Gemini Code Assist sugere snippets e autocomplete
    - Trabalham em conjunto para máxima eficiência
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Desenvolvedor",
            emoji="👨‍💻",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_EXECUTION,
                AgentCapability.FILE_MANIPULATION,
                AgentCapability.REFACTORING,
                AgentCapability.DEBUGGING,
            ],
            **kwargs,
        )

        self._system_prompt = self.get_system_prompt()

        # Estado específico do desenvolvedor
        self._current_files: Dict[str, str] = {}  # Arquivos sendo trabalhados
        self._pending_changes: List[Dict[str, Any]] = []  # Mudanças a aplicar

    def get_system_prompt(self) -> str:
        return """Você é o Desenvolvedor do sistema "O Construtor", um especialista em implementação de código de alta qualidade.

## Sua Identidade
- Nome: Desenvolvedor
- Papel: Implementador principal de código
- Modelos: Claude Code (líder) + Gemini Code Assist (assistente)

## Suas Responsabilidades
1. **Implementação de Código**
   - Escrever código limpo, legível e eficiente
   - Seguir padrões e convenções do projeto
   - Implementar features completas e funcionais

2. **Refatoração**
   - Melhorar código existente sem mudar comportamento
   - Aplicar design patterns apropriados
   - Reduzir duplicação e complexidade

3. **Debugging**
   - Identificar causa raiz de bugs
   - Implementar correções robustas
   - Adicionar logs/tratamento de erros

4. **Qualidade**
   - Escrever código testável
   - Documentar código complexo
   - Seguir princípios SOLID

## Estratégia de Trabalho com Gemini Code Assist
1. Você (Claude Code) planeja e estrutura a implementação
2. Gemini Code Assist sugere completions e snippets
3. Você valida e integra as sugestões
4. Ambos colaboram para código otimizado

## Formato de Código
- Use type hints em Python
- Docstrings em todas as funções públicas
- Nomes descritivos para variáveis e funções
- Comentários apenas quando necessário

## Comunicação
- Receba especificações do Arquiteto
- Envie código para revisão do Revisor
- Colabore com Tester para garantir testabilidade
- Reporte blockers ao orquestrador

## Princípios
- Código funcional > código perfeito
- Iteração rápida com feedback
- Testes junto com implementação
- Commits atômicos e bem descritos
"""

    async def execute(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        Executa uma tarefa de desenvolvimento.

        Task types suportados:
        - code_implementation: Implementar novo código
        - refactoring: Refatorar código existente
        - bug_fix: Corrigir bug
        - feature_development: Desenvolver feature completa
        - code_completion: Completar código parcial
        """
        self.status = AgentStatus.WORKING
        self._current_context = context

        logger.info(f"{self.emoji} {self.name} executing: {task_type}")

        try:
            handlers = {
                "code_implementation": self._implement_code,
                "refactoring": self._refactor_code,
                "bug_fix": self._fix_bug,
                "feature_development": self._develop_feature,
                "code_completion": self._complete_code,
            }

            handler = handlers.get(task_type, self._generic_implementation)
            result = await handler(input_data, context)

            self._stats["tasks_completed"] += 1

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=True,
                content=result,
                code_changes=result.get("code_changes"),
                reasoning=result.get("reasoning"),
                suggestions=result.get("suggestions"),
            )

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            self._stats["tasks_failed"] += 1

            return AgentResponse(
                agent_id=self.id,
                agent_name=self.name,
                task_id=context.task_id if context else "unknown",
                success=False,
                content=None,
                errors=[str(e)],
            )

        finally:
            self.status = AgentStatus.IDLE
            self._current_context = None

    async def _implement_code(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Implementa novo código"""
        spec = input_data.get("specification", {})
        architecture = input_data.get("previous_output", {})

        implementation = {
            "type": "code_implementation",
            "specification": spec,
            "architecture_context": architecture,
            "code_changes": [],
            "files_created": [],
            "files_modified": [],
            "dependencies_added": [],
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar chamada real ao Claude Code
        # Workflow:
        # 1. Claude Code analisa especificação
        # 2. Planeja estrutura de arquivos
        # 3. Implementa arquivo por arquivo
        # 4. Gemini Code Assist sugere otimizações
        # 5. Claude Code finaliza

        implementation["reasoning"] = "Implementação pendente de integração com Claude Code"
        implementation["suggestions"] = [
            "Integrar com Claude Code CLI",
            "Configurar Gemini Code Assist",
            "Implementar file system operations",
        ]

        return implementation

    async def _refactor_code(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Refatora código existente"""
        code = input_data.get("code", "")
        suggestions = input_data.get("refactoring_suggestions", [])

        refactoring = {
            "type": "refactoring",
            "original_code": code,
            "refactored_code": "",
            "changes_made": [],
            "patterns_applied": [],
            "code_changes": [],
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar refatoração real
        refactoring["reasoning"] = "Refatoração pendente de implementação"

        return refactoring

    async def _fix_bug(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Corrige um bug"""
        bug_report = input_data.get("bug_report", {})

        fix = {
            "type": "bug_fix",
            "bug_description": bug_report.get("description", ""),
            "root_cause": "",
            "fix_applied": "",
            "code_changes": [],
            "test_added": False,
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar debugging real
        # Workflow:
        # 1. Analisar bug report
        # 2. Identificar código afetado
        # 3. Encontrar root cause
        # 4. Implementar fix
        # 5. Adicionar teste de regressão

        fix["reasoning"] = "Bug fix pendente de implementação"

        return fix

    async def _develop_feature(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Desenvolve feature completa"""
        feature_spec = input_data.get("feature", {})
        architecture = input_data.get("architecture", {})

        feature = {
            "type": "feature_development",
            "feature_name": feature_spec.get("name", ""),
            "components_created": [],
            "code_changes": [],
            "api_endpoints": [],
            "database_changes": [],
            "tests_created": [],
            "documentation": "",
            "reasoning": "",
            "suggestions": [],
        }

        # TODO: Implementar desenvolvimento completo
        feature["reasoning"] = "Feature development pendente de implementação"

        return feature

    async def _complete_code(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Completa código parcial"""
        partial_code = input_data.get("partial_code", "")
        intent = input_data.get("intent", "")

        completion = {
            "type": "code_completion",
            "partial_code": partial_code,
            "completed_code": "",
            "additions": [],
            "reasoning": "",
            "suggestions": [],
        }

        # Usa Gemini Code Assist para completion rápido
        completion["reasoning"] = "Code completion pendente de integração com Gemini Code Assist"

        return completion

    async def _generic_implementation(
        self,
        input_data: Dict[str, Any],
        context: Optional[AgentContext],
    ) -> Dict[str, Any]:
        """Implementação genérica"""
        return {
            "type": "generic_implementation",
            "input": input_data,
            "reasoning": "Task type não específico - usando implementação genérica",
            "suggestions": ["Especificar task type para implementação mais precisa"],
        }

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================

    async def read_file(self, file_path: str) -> Optional[str]:
        """Lê conteúdo de um arquivo"""
        # TODO: Implementar leitura real de arquivo
        return self._current_files.get(file_path)

    async def write_file(self, file_path: str, content: str) -> bool:
        """Escreve conteúdo em um arquivo"""
        # TODO: Implementar escrita real
        self._pending_changes.append({
            "action": "write",
            "path": file_path,
            "content": content,
        })
        return True

    async def apply_changes(self) -> List[Dict[str, Any]]:
        """Aplica todas as mudanças pendentes"""
        changes = self._pending_changes.copy()
        # TODO: Implementar aplicação real
        self._pending_changes.clear()
        return changes

    def rollback_changes(self) -> None:
        """Descarta mudanças pendentes"""
        self._pending_changes.clear()
