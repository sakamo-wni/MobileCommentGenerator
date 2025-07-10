"""
統一設定管理（非推奨: config.pyを使用してください）

このモジュールは後方互換性のために維持されています。
新しいコードではsrc.config.configを使用してください。
"""

import warnings
from typing import Optional

# 新しい設定システムからインポート
from .config import (
    Config,
    get_config,
    get_api_config as _get_api_config,
    get_weather_config as _get_weather_config,
    get_app_settings as _get_app_settings,
    get_server_config as _get_server_config,
)
from .settings import (
    WeatherConfig,
    ServerConfig,
)
from .unified_config_shim import APIConfigShim as APIConfig, AppConfigShim as AppConfig

# 非推奨警告
warnings.warn(
    "unified_config.py is deprecated. Use src.config.config instead.",
    DeprecationWarning,
    stacklevel=2
)


class UnifiedConfig:
    """統一設定クラス（非推奨）
    
    後方互換性のために維持されています。
    新しいコードではget_config()を使用してください。
    """
    
    _instance: Optional["UnifiedConfig"] = None
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """新しい設定システムへのプロキシとして動作"""
        if not hasattr(self, '_initialized'):
            self._config = get_config()
            self._config_cache = {}  # YAML設定キャッシュ（後方互換性）
            self._initialized = True
    
    @property
    def api(self) -> APIConfig:
        """API設定を取得"""
        return self._config.api
    
    @property
    def weather(self) -> WeatherConfig:
        """天気設定を取得"""
        return self._config.weather
    
    @property  
    def app(self) -> AppConfig:
        """アプリケーション設定を取得"""
        return self._config.app
    
    @property
    def server(self) -> ServerConfig:
        """サーバー設定を取得"""
        return self._config.server
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """APIキーを取得（非推奨）"""
        if provider == "wxtech":
            return self._config.api.wxtech_api_key
        return self._config.api.get_llm_key(provider)
    
    def get_weather_config(self) -> dict:
        """天気設定を辞書形式で取得（非推奨）"""
        return {
            "forecast_hours_ahead": self.weather.forecast_hours_ahead,
            "forecast_days": self.weather.forecast_days,
            "cache_ttl_seconds": self.weather.cache_ttl_seconds,
        }
    
    def validate(self) -> dict:
        """設定の検証（非推奨）"""
        return {
            "environment": self.app.env,
            "api_keys": self.api.validate_keys(),
        }
    
    def to_dict(self) -> dict:
        """設定を辞書形式で返す（非推奨）"""
        return self._config.to_dict()
    
    def is_production(self) -> bool:
        """本番環境かどうかを判定（非推奨）"""
        return self._config.app.env == "production"
    
    def get_cors_origins(self) -> list:
        """CORS許可オリジンのリストを取得（非推奨）"""
        import os
        # 本番環境の場合、CORS_ORIGINS_PRODを使用（後方互換性）
        if self._config.app.env == "production":
            prod_origins = os.getenv("CORS_ORIGINS_PROD", "")
            if prod_origins:
                return [origin.strip() for origin in prod_origins.split(",")]
        return self._config.server.cors_origins


# 互換性のためのシングルトンインスタンス
config = UnifiedConfig()


# 互換性のためのヘルパー関数
def get_unified_config() -> UnifiedConfig:
    """統一設定インスタンスを取得（非推奨）"""
    return config


def get_api_config() -> APIConfig:
    """API設定を取得（非推奨）"""
    return APIConfig()


def get_weather_config() -> WeatherConfig:
    """天気設定を取得（非推奨）"""
    return _get_weather_config()


def get_app_config() -> AppConfig:
    """アプリケーション設定を取得（非推奨）"""
    return AppConfig()


def get_server_config() -> ServerConfig:
    """サーバー設定を取得（非推奨）"""
    return _get_server_config()