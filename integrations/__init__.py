"""
O Construtor - Integrations Module
Integrações com serviços externos e IDEs
"""

from integrations.claude_code_client import ClaudeCodeClient
from integrations.gemini_code_assist import GeminiCodeAssistClient
from integrations.vertex_ai_client import VertexAIClient
from integrations.github_client import GitHubClient

__all__ = [
    "ClaudeCodeClient",
    "GeminiCodeAssistClient",
    "VertexAIClient",
    "GitHubClient",
]
