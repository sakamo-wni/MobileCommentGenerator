"""
統一設定管理（非推奨: config.pyを使用してください）

このモジュールは後方互換性のために維持されています。
新しいコードではsrc.config.configを使用してください。
"""

from __future__ import annotations
import warnings
from typing import Any

# 新しい設定システムからインポート
from .config import (
    Config,
    get_config,
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
    
    _instance: "UnifiedConfig" | None = None
    
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
            self._api_config = None  # APIConfigのキャッシュ
            self._app_config = None  # AppConfigのキャッシュ
            self._initialized = True
    
    @property
    def api(self) -> APIConfig:
        """API設定を取得"""
        if self._api_config is None:
            self._api_config = APIConfig()  # APIConfigShimのインスタンス
        return self._api_config
    
    @property
    def weather(self) -> WeatherConfig:
        """天気設定を取得"""
        return self._config.weather
    
    @property  
    def app(self) -> AppConfig:
        """アプリケーション設定を取得"""
        if self._app_config is None:
            self._app_config = AppConfig()  # AppConfigShimのインスタンス
        return self._app_config
    
    @property
    def server(self) -> ServerConfig:
        """サーバー設定を取得"""
        return self._config.server
    
    def get_api_key(self, provider: str) -> str | None:
        """APIキーを取得（非推奨）"""
        if provider == "wxtech":
            return self._config.api.wxtech_api_key
        key = self._config.api.get_llm_key(provider)
        return key if key else None
    
    def get_weather_config(self) -> dict[str, Any]:
        """天気設定を辞書形式で取得（非推奨）"""
        return {
            "forecast_hours_ahead": self.weather.forecast_hours_ahead,
            "forecast_days": self.weather.forecast_days,
            "cache_ttl_seconds": self.weather.cache_ttl_seconds,
        }
    
    def validate(self) -> dict[str, Any]:
        """設定の検証（非推奨）"""
        return {
            "environment": self.app.env,
            "api_keys": self.api.validate_keys(),
        }
    
    def to_dict(self) -> dict[str, Any]:
        """設定を辞書形式で返す（非推奨）"""
        return self._config.to_dict()
    
    def is_production(self) -> bool:
        """本番環境かどうかを判定（非推奨）"""
        return self._config.app.env == "production"
    
    def get_cors_origins(self) -> list[str]:
        """CORS許可オリジンのリストを取得（非推奨）"""
        # 新しい設定システムで処理されるため、単に返すだけ
        return self._config.server.cors_origins
    
    def get_yaml_config(self, config_name: str) -> dict[str, Any]:
        """YAML設定を取得（未実装・非推奨）"""
        # 将来的な実装のためのスタブ
        return {}


# 互換性のためのシングルトンインスタンス
config = UnifiedConfig()


# 互換性のためのヘルパー関数
def get_unified_config() -> UnifiedConfig:
    """統一設定インスタンスを取得（非推奨）"""
    warnings.warn(
        "get_unified_config() is deprecated. Use get_config() from src.config.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config


def get_api_config() -> APIConfig:
    """API設定を取得（非推奨）"""
    warnings.warn(
        "get_api_config() is deprecated. Use get_config().api from src.config.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config.api


def get_weather_config() -> WeatherConfig:
    """天気設定を取得（非推奨）"""
    warnings.warn(
        "get_weather_config() is deprecated. Use get_config().weather from src.config.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config.weather


def get_app_config() -> AppConfig:
    """アプリケーション設定を取得（非推奨）"""
    warnings.warn(
        "get_app_config() is deprecated. Use get_config().app from src.config.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config.app


def get_server_config() -> ServerConfig:
    """サーバー設定を取得（非推奨）"""
    warnings.warn(
        "get_server_config() is deprecated. Use get_config().server from src.config.config instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config.server