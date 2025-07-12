"""花粉関連のコメント検証"""

import logging
from typing import Tuple
from datetime import datetime

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class PollenValidator(BaseValidator):
    """花粉関連のコメント検証クラス"""
    
    # 花粉飛散期間外の月（6月〜1月）
    NON_POLLEN_MONTHS = [6, 7, 8, 9, 10, 11, 12, 1]
    
    # 花粉関連表現パターン
    POLLEN_PATTERNS = [
        "花粉", "花粉症", "花粉対策", "花粉飛散", "花粉情報",
        "マスクで花粉", "くしゃみ", "鼻水", "目のかゆみ",
        "花粉予報", "花粉量", "スギ花粉", "ヒノキ花粉"
    ]
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """
        花粉関連コメントの妥当性を検証
        
        Args:
            comment: 検証対象のコメント
            weather_data: 天気データ
            
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        
        # 花粉表現が含まれているかチェック
        if not self._contains_pollen_expression(comment_text):
            # 花粉表現が含まれていない場合は検証をパス
            return True, ""
        
        # 1. 季節チェック（花粉飛散期間外）
        season_check = self._check_seasonal_validity(weather_data.datetime)
        if not season_check[0]:
            return season_check
        
        # 2. 天気条件チェック（雨天時）
        weather_check = self._check_weather_validity(weather_data)
        if not weather_check[0]:
            return weather_check
        
        return True, "花粉コメント検証OK"
    
    def _contains_pollen_expression(self, text: str) -> bool:
        """テキストに花粉関連表現が含まれているかチェック"""
        return any(pattern in text for pattern in self.POLLEN_PATTERNS)
    
    def _check_seasonal_validity(self, target_datetime: datetime) -> Tuple[bool, str]:
        """季節的な妥当性をチェック"""
        month = target_datetime.month
        
        if month in self.NON_POLLEN_MONTHS:
            return False, f"{month}月は花粉飛散期間外"
        
        return True, ""
    
    def _check_weather_validity(self, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件での妥当性をチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天時は花粉が飛散しない
        if any(rain in weather_desc for rain in ["雨", "rain"]) or weather_data.precipitation > 0:
            return False, "雨天時は花粉が飛散しない"
        
        return True, ""
    
    def is_inappropriate_pollen_comment(self, comment_text: str, weather_data: WeatherForecast, 
                                       target_datetime: datetime) -> bool:
        """
        花粉コメントが不適切かどうかを判定
        
        Args:
            comment_text: コメントテキスト
            weather_data: 天気データ
            target_datetime: 対象日時
            
        Returns:
            不適切な場合True
        """
        # 花粉表現が含まれていない場合はFalse
        if not self._contains_pollen_expression(comment_text):
            return False
        
        # 季節チェック
        if target_datetime.month in self.NON_POLLEN_MONTHS:
            logger.debug(f"{target_datetime.month}月に不適切な花粉表現検出: '{comment_text}'")
            return True
        
        # 雨天チェック
        weather_desc = weather_data.weather_description.lower()
        if any(rain in weather_desc for rain in ["雨", "rain"]) or weather_data.precipitation > 0:
            logger.debug(f"雨天時に不適切な花粉表現検出: '{comment_text}'")
            return True
        
        return False