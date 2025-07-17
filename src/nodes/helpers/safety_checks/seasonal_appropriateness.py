"""季節適切性チェックモジュール"""

from __future__ import annotations
import logging
from datetime import datetime
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)

# 季節別の不適切表現
SEASONAL_INAPPROPRIATE = {
    "spring": ["梅雨", "真夏", "猛暑", "師走", "年末", "初雪", "真冬"],  # 3,4,5月
    "summer": ["初雪", "雪", "真冬", "厳寒", "凍結", "霜", "初霜", "紅葉", "落ち葉"],  # 6,7,8月
    "autumn": ["真夏", "猛暑", "梅雨", "初雪", "真冬", "厳寒"],  # 9,10,11月
    "winter": ["猛暑", "真夏", "梅雨", "桜", "新緑", "紅葉"]  # 12,1,2月
}


class SeasonalAppropriatenessChecker:
    """季節と表現の適切性をチェックするクラス"""
    
    def check_seasonal_appropriateness(
        self,
        weather_comment: str,
        state: CommentGenerationState
    ) -> tuple[bool, str, list[str]]:
        """季節と表現の適切性をチェック
        
        Returns:
            (is_inappropriate, pattern_found, inappropriate_patterns)
        """
        if not state or not hasattr(state, 'target_datetime') or not weather_comment:
            return False, "", []
        
        month = state.target_datetime.month
        
        # 残暑チェック（9月以降のみ適切）
        if self._check_late_summer_heat(weather_comment, month):
            return True, "残暑", ["残暑"]
        
        # 季節別の不適切表現チェック
        season = self._get_season(month)
        seasonal_inappropriate = SEASONAL_INAPPROPRIATE.get(season, [])
        
        for word in seasonal_inappropriate:
            if word in weather_comment:
                logger.warning(f"🚨 {month}月に「{word}」は不適切")
                return True, word, seasonal_inappropriate
        
        return False, "", []
    
    def _check_late_summer_heat(self, weather_comment: str, month: int) -> bool:
        """残暑表現の適切性をチェック"""
        if "残暑" not in weather_comment:
            return False
        
        if month not in [9, 10, 11]:
            logger.warning(f"🚨 {month}月に「残暑」は不適切")
            return True
        
        return False
    
    def _get_season(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        elif month in [12, 1, 2]:
            return "winter"
        else:
            return ""
    
    def get_temperature_appropriate_replacement(
        self,
        weather_comment: str,
        month: int
    ) -> str:
        """温度表現の季節に応じた置き換え"""
        if month in [6, 7, 8] and "残暑" in weather_comment:
            return weather_comment.replace("残暑", "暑さ")
        return weather_comment