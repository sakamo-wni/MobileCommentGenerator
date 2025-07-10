"""
unified_config.pyとの互換性のためのシムクラス
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from .config import get_config


@dataclass
class APIConfigShim:
    """旧APIConfigとの互換性クラス"""
    
    def __post_init__(self):
        self._config = get_config()
    
    @property
    def wxtech_api_key(self) -> str:
        return self._config.api.wxtech_api_key
    
    @property
    def openai_api_key(self) -> str:
        return self._config.api.openai_api_key
    
    @property
    def anthropic_api_key(self) -> str:
        return self._config.api.anthropic_api_key
    
    @property
    def gemini_api_key(self) -> str:
        return self._config.api.gemini_api_key
    
    @property
    def gemini_model(self) -> str:
        """旧unified_config.pyとの互換性のため、LLMConfigからgemini_modelを取得"""
        return self._config.llm.gemini_model


@dataclass  
class AppConfigShim:
    """旧AppConfigとの互換性クラス"""
    
    def __post_init__(self):
        self._config = get_config()
    
    @property
    def env(self) -> str:
        return self._config.app.env
    
    @property
    def log_level(self) -> str:
        return self._config.app.log_level
    
    @property
    def data_dir(self) -> Path:
        return self._config.app.data_dir
    
    @property
    def cache_dir(self) -> Path:
        """旧unified_config.pyとの互換性のため、WeatherConfigからcache_dirを取得"""
        return self._config.weather.cache_dir