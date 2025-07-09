"""
統一された設定管理システム

すべての設定を一元管理し、環境変数の読み込みと検証を行う
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env.shared", override=False)


@dataclass
class APIConfig:
    """API関連の設定"""
    # API Keys
    wxtech_api_key: str = field(default="")
    openai_api_key: str = field(default="")
    anthropic_api_key: str = field(default="")
    gemini_api_key: str = field(default="")
    
    # API Settings
    gemini_model: str = field(default="gemini-1.5-flash")
    api_timeout: int = field(default=30)  # seconds
    retry_count: int = field(default=3)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.wxtech_api_key = os.getenv("WXTECH_API_KEY", self.wxtech_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        self.api_timeout = int(os.getenv("API_TIMEOUT", str(self.api_timeout)))


@dataclass
class WeatherConfig:
    """天気予報関連の設定"""
    forecast_hours_ahead: int = field(default=12)
    forecast_days: int = field(default=3)
    cache_ttl_seconds: int = field(default=3600)  # 1 hour
    cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))
    
    # 閾値設定
    high_temp_threshold: float = field(default=30.0)
    low_temp_threshold: float = field(default=10.0)
    heavy_rain_threshold: float = field(default=30.0)
    strong_wind_threshold: float = field(default=15.0)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.forecast_hours_ahead = int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", str(self.forecast_hours_ahead)))
        self.forecast_days = int(os.getenv("WEATHER_FORECAST_DAYS", str(self.forecast_days)))
        self.cache_ttl_seconds = int(os.getenv("WEATHER_CACHE_TTL", str(self.cache_ttl_seconds)))
        self.cache_dir = Path(os.getenv("WEATHER_CACHE_DIR", str(self.cache_dir)))


@dataclass
class AppSettings:
    """アプリケーション全体の設定"""
    env: str = field(default="development")
    debug: bool = field(default=False)
    log_level: str = field(default="INFO")
    
    # データ設定
    data_dir: Path = field(default_factory=lambda: Path("output"))
    csv_dir: Path = field(default_factory=lambda: Path("output"))
    
    # バッチ処理設定
    batch_concurrent_limit: int = field(default=3)
    batch_request_timeout: int = field(default=120000)  # milliseconds
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.env = os.getenv("APP_ENV", self.env)
        self.debug = os.getenv("DEBUG", str(self.debug)).lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.data_dir)))
        self.csv_dir = Path(os.getenv("CSV_DIR", str(self.csv_dir)))


@dataclass
class ServerConfig:
    """サーバー関連の設定"""
    api_host: str = field(default="0.0.0.0")
    api_port: int = field(default=8000)
    frontend_port: int = field(default=3000)
    cors_origins: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", str(self.api_port)))
        self.frontend_port = int(os.getenv("FRONTEND_PORT", str(self.frontend_port)))
        
        # CORS origins
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            self.cors_origins = [origin.strip() for origin in cors_env.split(",")]
        else:
            # デフォルトのCORS origins
            self.cors_origins = [
                f"http://localhost:{self.frontend_port}",
                f"http://127.0.0.1:{self.frontend_port}",
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]


@dataclass
class LLMConfig:
    """LLM関連の設定"""
    default_provider: str = field(default="gemini")
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=1000)
    
    # プロバイダー別の設定
    openai_model: str = field(default="gpt-4o-mini")
    anthropic_model: str = field(default="claude-3-haiku-20240307")
    gemini_model: str = field(default="gemini-1.5-flash")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", self.default_provider)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(self.temperature)))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", str(self.max_tokens)))
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.anthropic_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)


@dataclass
class Config:
    """統一された設定クラス"""
    api: APIConfig = field(default_factory=APIConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    app: AppSettings = field(default_factory=AppSettings)
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    def __post_init__(self):
        """設定の検証"""
        self._validate()
        
        # ログレベルの設定
        logging.basicConfig(level=getattr(logging, self.app.log_level))
        
        if self.app.debug:
            logger.debug("Debug mode is enabled")
            logger.debug(f"Configuration loaded: {self.to_dict()}")
    
    def _validate(self):
        """設定の検証"""
        # 必須APIキーの確認（開発環境以外）
        if self.app.env != "development":
            if not self.api.wxtech_api_key:
                logger.warning("WXTECH_API_KEY is not set")
            
            # 少なくとも1つのLLM APIキーが必要
            llm_keys = [
                self.api.openai_api_key,
                self.api.anthropic_api_key,
                self.api.gemini_api_key
            ]
            if not any(llm_keys):
                logger.warning("No LLM API keys are set")
        
        # ディレクトリの作成
        self.app.data_dir.mkdir(parents=True, exist_ok=True)
        self.app.csv_dir.mkdir(parents=True, exist_ok=True)
        self.weather.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "api": {
                "wxtech_api_key": "***" if self.api.wxtech_api_key else "",
                "openai_api_key": "***" if self.api.openai_api_key else "",
                "anthropic_api_key": "***" if self.api.anthropic_api_key else "",
                "gemini_api_key": "***" if self.api.gemini_api_key else "",
                "gemini_model": self.api.gemini_model,
                "api_timeout": self.api.api_timeout,
                "retry_count": self.api.retry_count,
            },
            "weather": {
                "forecast_hours_ahead": self.weather.forecast_hours_ahead,
                "forecast_days": self.weather.forecast_days,
                "cache_ttl_seconds": self.weather.cache_ttl_seconds,
                "cache_dir": str(self.weather.cache_dir),
            },
            "app": {
                "env": self.app.env,
                "debug": self.app.debug,
                "log_level": self.app.log_level,
                "data_dir": str(self.app.data_dir),
                "csv_dir": str(self.app.csv_dir),
                "batch_concurrent_limit": self.app.batch_concurrent_limit,
                "batch_request_timeout": self.app.batch_request_timeout,
            },
            "server": {
                "api_host": self.server.api_host,
                "api_port": self.server.api_port,
                "frontend_port": self.server.frontend_port,
                "cors_origins": self.server.cors_origins,
            },
            "llm": {
                "default_provider": self.llm.default_provider,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "openai_model": self.llm.openai_model,
                "anthropic_model": self.llm.anthropic_model,
                "gemini_model": self.llm.gemini_model,
            }
        }


# シングルトンパターンで設定インスタンスを管理
@lru_cache(maxsize=1)
def get_config() -> Config:
    """設定インスタンスを取得"""
    return Config()


# 互換性のためのヘルパー関数
def get_api_config() -> APIConfig:
    """API設定を取得"""
    return get_config().api


def get_weather_config() -> WeatherConfig:
    """天気設定を取得"""
    return get_config().weather


def get_app_settings() -> AppSettings:
    """アプリケーション設定を取得"""
    return get_config().app


def get_server_config() -> ServerConfig:
    """サーバー設定を取得"""
    return get_config().server


def get_llm_config() -> LLMConfig:
    """LLM設定を取得"""
    return get_config().llm