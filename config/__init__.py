"""
O Construtor - Configuration Module
Sistema de configuração centralizada para orquestração de IAs
"""

from config.settings import Settings, get_settings
from config.models import ModelConfig, get_model_for_task

__all__ = ["Settings", "get_settings", "ModelConfig", "get_model_for_task"]
