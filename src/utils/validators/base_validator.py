"""ベースバリデータクラス - 共通の検証機能を提供"""

import logging
from typing import Any, , 
from abc import ABC, abstractmethod

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType

logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """全てのバリデータの基底クラス"""
    
    def __init__(self):
        self.validation_results: list[tuple[bool, str]] = []
    
    @abstractmethod
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """検証を実行する抽象メソッド"""
        pass
    
    def _contains_forbidden_words(self, text: str, forbidden_words: list[str]) -> bool:
        """テキストに禁止ワードが含まれているかチェック"""
        text_lower = text.lower()
        for word in forbidden_words:
            if word.lower() in text_lower:
                return True
        return False
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "春"
        elif month == 6:
            return "梅雨"
        elif month in [7, 8]:
            return "夏"
        elif month == 9:
            return "台風"
        elif month in [10, 11]:
            return "秋"
        else:  # 12, 1, 2
            return "冬"
    
    def _log_validation_result(self, is_valid: bool, reason: str, comment_id: str | None = None):
        """検証結果をログに記録"""
        if not is_valid:
            logger.debug(f"Comment {comment_id} rejected: {reason}")
        else:
            logger.debug(f"Comment {comment_id} passed validation")