"""湿度条件検証モジュール - 湿度に基づく検証"""

import logging
from typing import Tuple, Optional

from src.data.weather_data import WeatherForecast
from src.validators.base_validator import BaseValidator

logger = logging.getLogger(__name__)


class HumidityValidator(BaseValidator):
    """湿度条件に基づく検証クラス"""
    
    def check_humidity_conditions(self, comment_text: str, 
                                comment_type: str,
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """湿度条件に基づいてコメントの適切性をチェック"""
        humidity = self._get_humidity_value(weather_data)
        
        # 湿度データがない場合はチェックをスキップ
        if humidity is None:
            return True, ""
        
        # 高湿度チェック（70%以上）
        if humidity >= 70:
            forbidden_words = self.humidity_forbidden_words.get("high", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"高湿度（{humidity}%）時に不適切な表現: '{word}'"
        
        # 低湿度チェック（40%未満）
        elif humidity < 40:
            forbidden_words = self.humidity_forbidden_words.get("low", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"低湿度（{humidity}%）時に不適切な表現: '{word}'"
        
        return True, ""
    
    def _get_humidity_value(self, weather_data: WeatherForecast) -> Optional[int]:
        """WeatherForecastから湿度値を取得
        
        注: 実際のWeatherForecastクラスの実装に応じて調整が必要
        """
        # WeatherForecastに湿度属性がある場合
        if hasattr(weather_data, 'humidity'):
            return weather_data.humidity
        
        # なければNoneを返す
        return None