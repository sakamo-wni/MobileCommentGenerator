"""
既存コードとの互換性レイヤー

既存の設定クラスから新しい統一設定への移行を支援
"""

import warnings
import logging
from typing import Any
from functools import wraps

from .config import get_config, get_api_config, get_weather_config, get_app_settings

logger = logging.getLogger(__name__)


def deprecated(message: str):
    """非推奨警告デコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__module__}.{func.__name__} is deprecated. {message}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class UnifiedConfigCompatibility:
    """unified_config.pyとの互換性クラス"""
    
    @property
    @deprecated("Use get_config().api instead")
    def api(self):
        return get_api_config()
    
    @property
    @deprecated("Use get_config().weather instead")
    def weather(self):
        return get_weather_config()
    
    @property
    @deprecated("Use get_config().app instead")
    def app(self):
        return get_app_settings()
    
    @property
    @deprecated("Use get_config().server instead")
    def server(self):
        return get_config().server


@deprecated("Use get_config() instead of get_unified_config()")
def get_unified_config():
    """unified_config.get_unified_config()との互換性"""
    return UnifiedConfigCompatibility()


class AppConfigCompatibility:
    """app_config.pyとの互換性クラス"""
    
    @staticmethod
    @deprecated("Use get_config().api instead")
    def from_env():
        """APIKeys.from_env()との互換性"""
        config = get_config()
        
        # 既存のAPIKeysクラスと同じ構造を返す
        class APIKeys:
            openai_key = config.api.openai_api_key
            gemini_key = config.api.gemini_api_key
            anthropic_key = config.api.anthropic_api_key
            wxtech_key = config.api.wxtech_api_key
            # AWS/S3機能は現在使用されていないため、互換性のためにNoneを返す
            # TODO: UIのsettings_panel.pyからAWS設定を削除する
            aws_access_key_id = None  # 廃止済み
            aws_secret_access_key = None  # 廃止済み
            aws_region = "ap-northeast-1"  # 廃止済み
        
        return APIKeys()


class AppSettingsCompatibility:
    """app_settings.pyとの互換性クラス"""
    
    def __init__(self):
        self._config = get_config()
    
    @property
    @deprecated("Use get_config().weather instead")
    def weather(self):
        return self._config.weather
    
    @property
    @deprecated("Use get_config().llm instead")
    def langgraph(self):
        # LangGraphConfigをLLMConfigにマッピング
        class LangGraphConfig:
            def __init__(self, llm_config):
                self._llm = llm_config
            
            @property
            def llm_provider(self):
                return self._llm.default_provider
            
            @property
            def model_name(self):
                if self._llm.default_provider == "openai":
                    return self._llm.openai_model
                elif self._llm.default_provider == "anthropic":
                    return self._llm.anthropic_model
                else:
                    return self._llm.gemini_model
            
            def to_dict(self):
                return {
                    "llm_provider": self.llm_provider,
                    "model_name": self.model_name,
                }
        
        return LangGraphConfig(self._config.llm)
    
    @property
    def debug_mode(self):
        return self._config.app.debug
    
    @property
    def log_level(self):
        return self._config.app.log_level
    
    def to_dict(self):
        return {
            "weather": self._config.weather.__dict__,
            "langgraph": self.langgraph.to_dict(),
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
        }


# 既存のインポートとの互換性
@deprecated("Use get_config() from src.config.config instead")
def load_config():
    """既存のload_config()との互換性"""
    return AppSettingsCompatibility()


# weather_settings.pyとの互換性
@deprecated("Use get_config().weather from src.config.config instead")
def get_weather_settings():
    """weather_settings.get_weather_settings()との互換性"""
    return get_weather_config()


# app_config.pyのAPIKeysとの互換性
APIKeys = AppConfigCompatibility


# 環境変数の移行ガイド
def print_migration_guide():
    """移行ガイドを出力"""
    guide = """
    ========================================
    設定システム移行ガイド
    ========================================
    
    1. 新しいインポート方法:
       ```python
       from src.config.config import get_config
       
       config = get_config()
       api_key = config.api.wxtech_api_key
       ```
    
    2. 既存コードの移行例:
       - 旧: from src.config.unified_config import get_unified_config
         新: from src.config.config import get_config
       
       - 旧: config = get_unified_config()
         新: config = get_config()
       
       - 旧: config.api.wxtech_api_key
         新: config.api.wxtech_api_key (同じ)
    
    3. 環境変数の変更:
       - 新しい環境変数スキーマは src/config/env_schema.py を参照
       - .env.template は `python -m src.config.env_schema` で生成可能
    
    4. 非推奨警告の抑制:
       互換性レイヤーを使用すると非推奨警告が表示されます。
       warnings.filterwarnings("ignore", category=DeprecationWarning)
       で抑制できますが、早めの移行を推奨します。
    """
    print(guide)


if __name__ == "__main__":
    print_migration_guide()