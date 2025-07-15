"""天気推移バリデータ - 天気の時系列変化に基づくコメント検証"""

import logging
from typing import from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class WeatherTransitionValidator(BaseValidator):
    """天気の時系列変化に基づいてコメントの適切性を検証"""
    
    # 天気回復を示すフレーズ
    RECOVERY_PHRASES = {
        "天気回復へ", "回復へ", "回復傾向", "回復に向かう",
        "天気が良くなる", "晴れ間が", "雨が止む", "雨が上がる",
        "段々と天気回復", "次第に回復", "徐々に回復"
    }
    
    # 天気悪化を示すフレーズ
    DETERIORATION_PHRASES = {
        "天気下り坂", "下り坂", "崩れる", "悪化",
        "雨が降り出す", "雲が増える", "天気が悪くなる"
    }
    
    def __init__(self):
        super().__init__()
        self.weather_priority = {
            WeatherCondition.CLEAR: 4,      # 晴れ（最良）
            WeatherCondition.PARTLY_CLOUDY: 3,  # 晴れ時々曇り
            WeatherCondition.CLOUDY: 2,     # 曇り
            WeatherCondition.RAIN: 1,       # 雨（最悪）
            WeatherCondition.SNOW: 1,       # 雪
            WeatherCondition.FOG: 1,        # 霧
            WeatherCondition.THUNDER: 0     # 雷（最も危険）
        }
        logger.info("天気推移バリデータを初期化しました")
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """天気の推移に基づいてコメントを検証"""
        comment_text = comment.comment_text
        advice_text = comment.raw_data.get("advice", "")
        full_text = f"{comment_text} {advice_text}"
        
        # 天気回復フレーズのチェック
        for phrase in self.RECOVERY_PHRASES:
            if phrase in full_text:
                # 現在の天気が既に良い場合は不適切
                if weather_data.weather_condition in [WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY]:
                    logger.info(f"既に晴れているのに回復表現: '{comment_text}' - 現在: {weather_data.weather_description}")
                    return False, f"既に{weather_data.weather_description}なのに「{phrase}」は不適切"
                
                # 時系列データがある場合は実際の推移をチェック
                if hasattr(weather_data, 'timeline_forecasts') and weather_data.timeline_forecasts:
                    if not self._is_weather_improving(weather_data):
                        logger.info(f"天気が改善しないのに回復表現: '{comment_text}'")
                        return False, f"天気予報が改善傾向にないのに「{phrase}」は不適切"
        
        # 天気悪化フレーズのチェック
        for phrase in self.DETERIORATION_PHRASES:
            if phrase in full_text:
                # 現在の天気が既に悪い場合は不適切
                if weather_data.weather_condition in [WeatherCondition.RAIN, WeatherCondition.SNOW, WeatherCondition.THUNDER]:
                    logger.info(f"既に悪天候なのに悪化表現: '{comment_text}' - 現在: {weather_data.weather_description}")
                    return False, f"既に{weather_data.weather_description}なのに「{phrase}」は不適切"
                
                # 時系列データがある場合は実際の推移をチェック
                if hasattr(weather_data, 'timeline_forecasts') and weather_data.timeline_forecasts:
                    if not self._is_weather_deteriorating(weather_data):
                        logger.info(f"天気が悪化しないのに悪化表現: '{comment_text}'")
                        return False, f"天気予報が悪化傾向にないのに「{phrase}」は不適切"
        
        return True, "天気推移検証OK"
    
    def _is_weather_improving(self, weather_data: WeatherForecast) -> bool:
        """天気が改善傾向にあるかチェック"""
        if not hasattr(weather_data, 'timeline_forecasts') or not weather_data.timeline_forecasts:
            return False
        
        current_priority = self.weather_priority.get(weather_data.weather_condition, 2)
        
        # 時系列の天気を確認
        future_priorities = []
        for forecast in weather_data.timeline_forecasts:
            if forecast.datetime > weather_data.datetime:
                priority = self.weather_priority.get(forecast.weather_condition, 2)
                future_priorities.append(priority)
        
        if not future_priorities:
            return False
        
        # 改善傾向をチェック（平均が現在より良い）
        avg_future = sum(future_priorities) / len(future_priorities)
        return avg_future > current_priority
    
    def _is_weather_deteriorating(self, weather_data: WeatherForecast) -> bool:
        """天気が悪化傾向にあるかチェック"""
        if not hasattr(weather_data, 'timeline_forecasts') or not weather_data.timeline_forecasts:
            return False
        
        current_priority = self.weather_priority.get(weather_data.weather_condition, 2)
        
        # 時系列の天気を確認
        future_priorities = []
        for forecast in weather_data.timeline_forecasts:
            if forecast.datetime > weather_data.datetime:
                priority = self.weather_priority.get(forecast.weather_condition, 2)
                future_priorities.append(priority)
        
        if not future_priorities:
            return False
        
        # 悪化傾向をチェック（平均が現在より悪い）
        avg_future = sum(future_priorities) / len(future_priorities)
        return avg_future < current_priority