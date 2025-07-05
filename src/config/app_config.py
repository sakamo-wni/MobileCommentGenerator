"""アプリケーション設定の統一管理"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging

from .unified_config import get_unified_config, get_api_config, get_app_config as get_unified_app_config

try:
    from src.utils.secure_config import get_secure_config
except ImportError:
    # セキュア設定が利用できない場合のフォールバック
    get_secure_config = None

logger = logging.getLogger(__name__)


@dataclass
class APIKeys:
    """APIキーの管理"""
    openai_key: Optional[str] = field(default=None)
    gemini_key: Optional[str] = field(default=None)
    anthropic_key: Optional[str] = field(default=None)
    wxtech_key: Optional[str] = field(default=None)
    aws_access_key_id: Optional[str] = field(default=None)
    aws_secret_access_key: Optional[str] = field(default=None)
    aws_region: str = field(default="ap-northeast-1")
    
    @classmethod
    def from_env(cls) -> "APIKeys":
        """環境変数またはセキュア設定からAPIキーを読み込む"""
        # 統一設定から取得
        unified_config = get_unified_config()
        api_config = unified_config.api
        
        # セキュア設定が利用可能な場合は優先的に使用
        if get_secure_config:
            secure_config = get_secure_config()
            return cls(
                openai_key=secure_config.get_api_key("openai") or api_config.openai_api_key,
                gemini_key=secure_config.get_api_key("gemini") or api_config.gemini_api_key,
                anthropic_key=secure_config.get_api_key("anthropic") or api_config.anthropic_api_key,
                wxtech_key=secure_config.get_api_key("wxtech") or api_config.wxtech_api_key,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_region=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
            )
        else:
            # フォールバック: 統一設定から
            return cls(
                openai_key=api_config.openai_api_key,
                gemini_key=api_config.gemini_api_key,
                anthropic_key=api_config.anthropic_api_key,
                wxtech_key=api_config.wxtech_api_key,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_region=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
            )
    
    def validate(self) -> Dict[str, bool]:
        """APIキーの存在を検証"""
        return {
            "openai": bool(self.openai_key),
            "gemini": bool(self.gemini_key),
            "anthropic": bool(self.anthropic_key),
            "wxtech": bool(self.wxtech_key),
            "aws": bool(self.aws_access_key_id and self.aws_secret_access_key)
        }
    
    def get_llm_key(self, provider: str) -> Optional[str]:
        """LLMプロバイダーに対応するAPIキーを取得"""
        provider_map = {
            "openai": self.openai_key,
            "gemini": self.gemini_key,
            "anthropic": self.anthropic_key
        }
        return provider_map.get(provider.lower())


@dataclass
class UISettings:
    """UI関連の設定"""
    page_title: str = field(default="天気コメント生成システム")
    page_icon: str = field(default="☀️")
    layout: str = field(default="wide")
    sidebar_state: str = field(default="expanded")
    theme: str = field(default="light")
    
    # コンポーネント設定
    max_locations_per_generation: int = field(default=30)
    default_llm_provider: str = field(default="gemini")
    show_debug_info: bool = field(default=False)
    
    # 表示設定
    date_format: str = field(default="%Y年%m月%d日 %H時%M分")
    timezone: str = field(default="Asia/Tokyo")


@dataclass
class GenerationSettings:
    """コメント生成関連の設定"""
    # タイムアウト設定
    generation_timeout: int = field(default=300)  # 秒
    api_timeout: int = field(default=60)  # 秒 - 長野県などの山間部対応
    
    # リトライ設定
    max_retries: int = field(default=3)
    retry_delay: float = field(default=1.0)
    
    # キャッシュ設定
    cache_enabled: bool = field(default=True)
    cache_ttl: int = field(default=3600)  # 秒
    
    # バッチ処理設定
    batch_size: int = field(default=5)
    concurrent_requests: int = field(default=3)
    
    # 品質設定
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=200)
    
    # NGワード設定
    ng_words_file: str = field(default="config/ng_words.yaml")
    expression_rules_file: str = field(default="config/expression_rules.yaml")


@dataclass
class DataSettings:
    """データ関連の設定"""
    # パス設定
    data_dir: str = field(default="data")
    forecast_cache_dir: str = field(default="data/forecast_cache")
    generation_history_file: str = field(default="data/generation_history.json")
    locations_file: str = field(default="src/data/Chiten.csv")
    
    # CSVファイル設定
    csv_output_dir: str = field(default="output")
    use_local_csv: bool = field(default=True)
    
    # データ保持設定
    max_history_records: int = field(default=1000)
    history_retention_days: int = field(default=30)


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
        # 統一設定から取得
        unified_config = get_unified_config()
        unified_app = unified_config.app
        
        config = cls(
            api_keys=APIKeys.from_env(),
            ui_settings=UISettings(),
            generation_settings=GenerationSettings(),
            data_settings=DataSettings(),
            env=unified_app.env,
            debug=unified_app.env == "development",
            log_level=unified_app.log_level
        )
        
        # 環境変数でオーバーライド可能な設定
        if os.getenv("MAX_LOCATIONS_PER_GENERATION"):
            config.ui_settings.max_locations_per_generation = int(os.getenv("MAX_LOCATIONS_PER_GENERATION"))
        
        if os.getenv("DEFAULT_LLM_PROVIDER"):
            config.ui_settings.default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER")
        
        return config
    
    def validate(self) -> Dict[str, Any]:
        """設定の検証"""
        validation_results = {
            "api_keys": self.api_keys.validate(),
            "environment": self.env,
            "debug_mode": self.debug,
            "data_dir_exists": os.path.exists(self.data_settings.data_dir),
            "locations_file_exists": os.path.exists(self.data_settings.locations_file)
        }
        
        # 警告の出力
        if not validation_results["api_keys"]["wxtech"]:
            logger.warning("WXTECH_API_KEY is not set. Weather data fetching will fail.")
        
        return validation_results
    
    def to_dict(self) -> Dict[str, Any]:
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
                "timeout": self.generation_settings.generation_timeout,
                "max_retries": self.generation_settings.max_retries,
                "cache_enabled": self.generation_settings.cache_enabled,
                "batch_size": self.generation_settings.batch_size
            },
            "data_settings": {
                "max_history": self.data_settings.max_history_records
            }
        }


# シングルトンインスタンス
_config_instance: Optional[AppConfig] = None


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