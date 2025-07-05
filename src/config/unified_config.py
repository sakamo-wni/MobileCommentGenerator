"""Unified configuration management to reduce duplication"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env files
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env.shared", override=False)

@dataclass
class APIConfig:
    """API configuration settings"""
    wxtech_api_key: str = field(default_factory=lambda: os.getenv("WXTECH_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

@dataclass
class WeatherConfig:
    """Weather-related configuration"""
    forecast_hours_ahead: int = field(default_factory=lambda: int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", "12")))
    forecast_days: int = 3
    cache_ttl_seconds: int = 3600  # 1 hour

@dataclass
class AppConfig:
    """Application-wide configuration"""
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    data_dir: Path = field(default_factory=lambda: Path("output"))
    cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))

@dataclass
class ServerConfig:
    """Server configuration for different environments"""
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    frontend_port: int = field(default_factory=lambda: int(os.getenv("FRONTEND_PORT", "3000")))
    cors_origins: list[str] = field(default_factory=lambda: 
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173").split(",")
    )

class UnifiedConfig:
    """Centralized configuration manager"""
    
    _instance: Optional["UnifiedConfig"] = None
    _config_cache: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration from various sources"""
        self.api = APIConfig()
        self.weather = WeatherConfig()
        self.app = AppConfig()
        self.server = ServerConfig()
        
        # Load YAML configs
        self._load_yaml_configs()
    
    def _load_yaml_configs(self):
        """Load configuration from YAML files"""
        config_dir = Path(__file__).parent
        
        yaml_configs = {
            "expression_rules": "expression_rules.yaml",
            "llm_config": "llm_config.yaml",
            "ng_words": "ng_words.yaml",
            "weather_thresholds": "weather_thresholds.yaml",
            "comment_restrictions": "comment_restrictions.yaml",
            "evaluation_config": "evaluation_config.yaml"
        }
        
        for key, filename in yaml_configs.items():
            file_path = config_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._config_cache[key] = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to load {filename}: {e}")
                    self._config_cache[key] = {}
                except Exception as e:
                    logger.error(f"Unexpected error loading {filename}: {e}")
                    self._config_cache[key] = {}
            else:
                logger.debug(f"Config file not found: {filename}")
                self._config_cache[key] = {}
    
    def get_yaml_config(self, config_name: str) -> Dict[str, Any]:
        """Get cached YAML configuration"""
        return self._config_cache.get(config_name, {})
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        provider_map = {
            "openai": self.api.openai_api_key,
            "anthropic": self.api.anthropic_api_key,
            "gemini": self.api.gemini_api_key,
            "wxtech": self.api.wxtech_api_key,
        }
        return provider_map.get(provider.lower())
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app.env == "production"
    
    def get_cors_origins(self) -> list[str]:
        """Get CORS origins based on environment"""
        if self.is_production():
            prod_origins = os.getenv("CORS_ORIGINS_PROD", "https://your-production-domain.com")
            return prod_origins.split(",")
        return self.server.cors_origins

# Global singleton instance
config = UnifiedConfig()

# Convenience functions for backward compatibility
def get_unified_config() -> UnifiedConfig:
    """Get the unified configuration instance"""
    return config

def get_api_config() -> APIConfig:
    """Get API configuration"""
    return config.api

def get_weather_config() -> WeatherConfig:
    """Get weather configuration"""
    return config.weather

def get_app_config() -> AppConfig:
    """Get app configuration"""
    return config.app

def get_server_config() -> ServerConfig:
    """Get server configuration"""
    return config.server