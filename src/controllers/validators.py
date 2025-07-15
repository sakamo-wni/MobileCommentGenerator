"""バリデーションモジュール"""

from typing import Any
from src.config.app_config import AppConfig


class ValidationManager:
    """バリデーション管理クラス"""
    
    def __init__(self, config: AppConfig):
        self._config = config
    
    def validate_location_count(self, locations: list[str]) -> tuple[bool, str | None]:
        """地点数の検証"""
        max_locations = self._config.ui_settings.max_locations_per_generation
        
        if len(locations) > max_locations:
            return False, f"選択された地点数が上限（{max_locations}地点）を超えています。"
        
        return True, None
    
    def validate_configuration(self) -> dict[str, bool | str]:
        """設定の検証"""
        return self._config.validate()