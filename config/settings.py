"""
O Construtor - Settings
Configurações centralizadas do sistema
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache


@dataclass
class Settings:
    """Configurações globais do O Construtor"""

    # === PROJECT INFO ===
    PROJECT_NAME: str = "O Construtor"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # === GCP / VERTEX AI ===
    GCP_PROJECT_ID: str = field(default_factory=lambda: os.getenv("GCP_PROJECT_ID", "gen-lang-client-0394737170"))
    GCP_REGION: str = field(default_factory=lambda: os.getenv("GCP_REGION", "us-central1"))
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    # === API KEYS ===
    GOOGLE_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    ANTHROPIC_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    GITHUB_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))

    # === DATABASE (SUPABASE) ===
    SUPABASE_URL: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    SUPABASE_KEY: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_KEY"))

    # === REDIS (CACHE & QUEUE) ===
    REDIS_URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))

    # === RATE LIMITING ===
    RATE_LIMIT_REQUESTS: int = 60  # requests per minute
    RATE_LIMIT_TOKENS: int = 100000  # tokens per minute

    # === TIMEOUTS ===
    API_TIMEOUT: int = 120  # seconds
    AGENT_TIMEOUT: int = 300  # seconds for agent tasks
    WORKFLOW_TIMEOUT: int = 1200  # 20 minutes for full workflows

    # === FILE LIMITS ===
    MAX_FILES_PER_ANALYSIS: int = 50
    MAX_LINES_PER_FILE: int = 2000
    MAX_CONTEXT_TOKENS: int = 100000

    # === PRIORITY EXTENSIONS ===
    PRIORITY_EXTENSIONS: tuple = (".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".go", ".rs", ".java")
    OTHER_EXTENSIONS: tuple = (".json", ".yaml", ".yml", ".toml", ".md", ".sql", ".sh")

    # === LOGGING ===
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FORMAT: str = "json"  # json or text

    # === FEATURE FLAGS ===
    ENABLE_CLAUDE_CODE: bool = True
    ENABLE_GEMINI_CODE_ASSIST: bool = True
    ENABLE_AUTO_IMPLEMENT: bool = True
    ENABLE_AUTO_TEST: bool = True
    ENABLE_AUTO_DEPLOY: bool = False  # Manual approval required
    ENABLE_MEMORY_PERSISTENCE: bool = True

    def __post_init__(self):
        """Validações após inicialização"""
        if self.ENVIRONMENT == "production":
            assert self.GOOGLE_API_KEY, "GOOGLE_API_KEY required in production"
            assert self.SUPABASE_URL, "SUPABASE_URL required in production"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações"""
    return Settings()
