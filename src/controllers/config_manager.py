"""設定管理を専門に扱うマネージャー

CommentGenerationControllerから設定管理の責務を分離。
"""

from __future__ import annotations
import logging
from src.config.app_config import AppConfig, get_config
from src.ui.streamlit_utils import load_locations

logger = logging.getLogger(__name__)


class ConfigManager:
    """アプリケーション設定を管理するクラス"""
    
    def __init__(self, config: AppConfig | None = None):
        self._config = config or get_config()
        
    @property
    def config(self) -> AppConfig:
        """設定を取得"""
        return self._config
    
    def get_default_locations(self) -> list[str]:
        """デフォルトの地点リストを取得"""
        return load_locations()
    
    def get_default_llm_provider(self) -> str:
        """デフォルトのLLMプロバイダーを取得"""
        return self.config.ui_settings.default_llm_provider
    
    def get_config_dict(self) -> dict[str, str | int | float | bool]:
        """設定を辞書形式で取得"""
        return self.config.to_dict()
    
    def get_max_llm_workers(self) -> int:
        """最大LLMワーカー数を取得"""
        return self.config.app.max_llm_workers
    
    def is_async_weather_enabled(self) -> bool:
        """非同期天気予報取得が有効かどうか"""
        return self.config.app.use_async_weather
    
    def get_api_timeout(self) -> int:
        """APIタイムアウト時間を取得"""
        return self.config.api.timeout
    
    def get_cache_ttl(self) -> int:
        """キャッシュTTLを取得（分）"""
        return self.config.app.cache_ttl_minutes