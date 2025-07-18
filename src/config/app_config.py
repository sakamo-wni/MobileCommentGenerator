"""アプリケーション設定の統一管理（非推奨: config.pyを使用してください）"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any
import logging

from .config import (
    get_config as get_new_config,  # 紛らわしい名前を避ける
    get_api_config,
    get_ui_settings,
    get_generation_settings,
    get_data_settings,
    get_app_settings
)

logger = logging.getLogger(__name__)

try:
    from src.utils.secure_config import get_secure_config
except ImportError as e:
    # セキュア設定が利用できない場合のフォールバック
    logger.warning(f"セキュア設定モジュールをインポートできませんでした: {e}")
    get_secure_config = None


@dataclass
class APIKeys:
    """APIキーの管理（非推奨: config.APIConfigを使用してください）"""
    openai_key: str | None = field(default=None)
    gemini_key: str | None = field(default=None)
    anthropic_key: str | None = field(default=None)
    wxtech_key: str | None = field(default=None)
    
    @classmethod
    def from_env(cls) -> "APIKeys":
        """環境変数またはセキュア設定からAPIキーを読み込む"""
        # 統一設定から取得
        api_config = get_api_config()
        
        # セキュア設定が利用可能な場合は優先的に使用
        if get_secure_config:
            secure_config = get_secure_config()
            return cls(
                openai_key=secure_config.get_api_key("openai") or api_config.openai_api_key,
                gemini_key=secure_config.get_api_key("gemini") or api_config.gemini_api_key,
                anthropic_key=secure_config.get_api_key("anthropic") or api_config.anthropic_api_key,
                wxtech_key=secure_config.get_api_key("wxtech") or api_config.wxtech_api_key
            )
        else:
            # フォールバック: 統一設定から
            return cls(
                openai_key=api_config.openai_api_key,
                gemini_key=api_config.gemini_api_key,
                anthropic_key=api_config.anthropic_api_key,
                wxtech_key=api_config.wxtech_api_key
            )
    
    def validate(self) -> dict[str, bool]:
        """APIキーの存在を検証"""
        api_config = get_api_config()
        return api_config.validate_keys()
    
    def get_llm_key(self, provider: str) -> str | None:
        """LLMプロバイダーに対応するAPIキーを取得"""
        api_config = get_api_config()
        return api_config.get_llm_key(provider)


# 互換性のために新しい設定クラスを直接インポート
from src.config.config import UISettings, GenerationSettings, DataSettings


@dataclass
class AppConfig:
    """アプリケーション全体の設定"""
    api_keys: APIKeys = field(default_factory=APIKeys)
    ui_settings: UISettings = field(default_factory=UISettings)
    generation_settings: GenerationSettings = field(default_factory=GenerationSettings)
    data_settings: DataSettings = field(default_factory=DataSettings)
    
    # 環境設定
    env: str = field(default="development")
    debug: bool = field(default=False)
    log_level: str = field(default="INFO")
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """環境変数から設定を読み込む"""
        # 新しい設定システムから取得
        new_config = get_new_config()
        app_settings = new_config.app
        
        config = cls(
            api_keys=APIKeys.from_env(),
            ui_settings=new_config.ui,
            generation_settings=new_config.generation,
            data_settings=new_config.data,
            env=app_settings.env,
            debug=app_settings.debug,
            log_level=app_settings.log_level
        )
        
        return config
    
    def validate(self) -> dict[str, Any]:
        """設定の検証"""
        api_key_validation = self.api_keys.validate()
        validation_results = {
            "api_keys": api_key_validation,
            "environment": self.env,
            "debug_mode": self.debug,
            "data_dir_exists": self.data_settings.data_dir.exists(),
            "locations_file_exists": self.data_settings.locations_file.exists()
        }
        
        # 警告の出力
        if not api_key_validation.get("wxtech", False):
            logger.warning("WXTECH_API_KEY is not set. Weather data fetching will fail.")
        
        return validation_results
    
    def to_dict(self) -> dict[str, Any]:
        """設定を辞書形式に変換（APIキーは除外）"""
        return {
            "environment": self.env,
            "debug": self.debug,
            "log_level": self.log_level,
            "ui_settings": {
                "page_title": self.ui_settings.page_title,
                "layout": self.ui_settings.layout,
                "max_locations": self.ui_settings.max_locations_per_generation,
                "default_provider": self.ui_settings.default_llm_provider
            },
            "generation_settings": {
                "timeout": self.generation_settings.timeout,
                "max_retries": self.generation_settings.max_retries,
                "cache_enabled": self.generation_settings.cache_enabled,
                "batch_size": self.generation_settings.batch_size
            },
            "data_settings": {
                "max_history": self.data_settings.max_history_records
            }
        }


# シングルトンインスタンス
_config_instance: AppConfig | None = None


def get_config() -> AppConfig:
    """設定のシングルトンインスタンスを取得"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.from_env()
        # 設定の検証
        validation_results = _config_instance.validate()
        logger.info(f"Configuration loaded: {_config_instance.to_dict()}")
        logger.debug(f"Validation results: {validation_results}")
    return _config_instance


def reset_config():
    """設定をリセット（テスト用）"""
    global _config_instance
    _config_instance = None