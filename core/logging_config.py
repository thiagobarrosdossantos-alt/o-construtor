"""
Configuração de Logging Estruturado
Sistema centralizado de logging com rotation, formatação JSON e níveis configuráveis
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    Formatter que produz logs em formato JSON estruturado.

    Campos padrão:
    - timestamp: ISO 8601
    - level: INFO, ERROR, etc.
    - logger: Nome do logger
    - message: Mensagem principal
    - module: Módulo Python
    - function: Função que gerou o log
    - line: Linha de código
    - extra: Campos adicionais
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formata record como JSON estruturado"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adicionar exc_info se houver exceção
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Adicionar campos extras personalizados
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter para console com cores e formatação legível.
    """

    # Códigos de cor ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Formata com cores para melhor legibilidade"""
        # Cor baseada no nível
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Formato: [TIMESTAMP] LEVEL [LOGGER] message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        formatted = (
            f"{color}[{timestamp}] "
            f"{record.levelname:8s} "
            f"[{record.name}]{reset} "
            f"{record.getMessage()}"
        )

        # Adicionar exceção se houver
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_prefix: str = "o-construtor"
) -> None:
    """
    Configura sistema de logging completo.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para arquivos de log
        enable_console: Habilita logs no console
        enable_file: Habilita logs em arquivo texto
        enable_json: Habilita logs estruturados JSON
        max_bytes: Tamanho máximo de cada arquivo (rotation)
        backup_count: Número de backups mantidos
        log_prefix: Prefixo dos arquivos de log
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remover handlers existentes
    root_logger.handlers.clear()

    # 1. Console Handler (colorido e legível)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredConsoleFormatter())
        root_logger.addHandler(console_handler)

    # 2. File Handler (texto legível com rotation)
    if enable_file:
        file_path = log_path / f"{log_prefix}.log"
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)

    # 3. JSON Handler (structured logs para análise)
    if enable_json:
        json_path = log_path / f"{log_prefix}.json.log"
        json_handler = RotatingFileHandler(
            filename=json_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)

    # Log de inicialização
    root_logger.info(
        f"Logging system initialized - Level: {level}, "
        f"Console: {enable_console}, File: {enable_file}, JSON: {enable_json}"
    )


def get_logger(name: str, extra_data: Optional[Dict[str, Any]] = None) -> logging.LoggerAdapter:
    """
    Obtém logger configurado com campos extras opcionais.

    Args:
        name: Nome do logger (geralmente __name__)
        extra_data: Dados adicionais para incluir em todos os logs

    Returns:
        LoggerAdapter configurado

    Example:
        >>> logger = get_logger(__name__, {"service": "orchestrator"})
        >>> logger.info("Processing request", extra={"request_id": "123"})
    """
    base_logger = logging.getLogger(name)

    if extra_data:
        return logging.LoggerAdapter(base_logger, {"extra_data": extra_data})

    return logging.LoggerAdapter(base_logger, {})


def log_execution_time(logger: logging.Logger):
    """
    Decorator para logar tempo de execução de funções.

    Usage:
        @log_execution_time(logger)
        async def my_function():
            pass
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed in {elapsed:.2f}s",
                    extra={"extra_data": {"execution_time": elapsed, "function": func.__name__}}
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.2f}s: {e}",
                    extra={"extra_data": {"execution_time": elapsed, "function": func.__name__}},
                    exc_info=True
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed in {elapsed:.2f}s",
                    extra={"extra_data": {"execution_time": elapsed, "function": func.__name__}}
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.2f}s: {e}",
                    extra={"extra_data": {"execution_time": elapsed, "function": func.__name__}},
                    exc_info=True
                )
                raise

        # Detectar se é async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Atalhos para uso rápido
def setup_default_logging():
    """Setup com configurações padrão recomendadas"""
    setup_logging(
        level="INFO",
        log_dir="logs",
        enable_console=True,
        enable_file=True,
        enable_json=True,
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5
    )
