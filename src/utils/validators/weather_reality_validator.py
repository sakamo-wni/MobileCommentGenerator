"""天気と現実の矛盾を検証するバリデータ"""

from __future__ import annotations
import logging
from src.data.weather_data import WeatherForecast
from src.config.config import get_weather_constants

# 定数を取得
SUNNY_WEATHER_KEYWORDS = get_weather_constants().SUNNY_WEATHER_KEYWORDS

logger = logging.getLogger(__name__)


class WeatherRealityValidator:
    """天気コメントと実際の天気データの矛盾を検証"""
    
    def check_weather_reality_contradiction(
        self, 
        weather_comment: str, 
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        天気コメントが実際の天気と矛盾していないかチェック
        
        Args:
            weather_comment: 天気コメント
            weather_data: 実際の天気データ
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # 晴れているのに雨の表現
        if any(keyword in weather_data.weather_description for keyword in SUNNY_WEATHER_KEYWORDS):
            rain_expressions = ["雨", "降水", "傘", "濡れ", "しっとり", "じめじめ"]
            for expr in rain_expressions:
                if expr in weather_comment:
                    return False, f"晴天時に不適切な表現: {expr}"
        
        # 雨なのに晴れの表現
        if "雨" in weather_data.weather_description:
            sunny_expressions = ["快晴", "日差し", "陽射し", "太陽", "青空", "晴天"]
            for expr in sunny_expressions:
                if expr in weather_comment:
                    return False, f"雨天時に不適切な表現: {expr}"
        
        # 高温時に寒さの表現
        if weather_data.temperature > 30:
            cold_expressions = ["寒い", "冷え", "ひんやり", "凍える", "震える"]
            for expr in cold_expressions:
                if expr in weather_comment:
                    return False, f"高温時({weather_data.temperature}°C)に不適切な表現: {expr}"
        
        # 低温時に暑さの表現
        if weather_data.temperature < 10:
            hot_expressions = ["暑い", "猛暑", "酷暑", "うだる", "汗ばむ"]
            for expr in hot_expressions:
                if expr in weather_comment:
                    return False, f"低温時({weather_data.temperature}°C)に不適切な表現: {expr}"
        
        return True, ""