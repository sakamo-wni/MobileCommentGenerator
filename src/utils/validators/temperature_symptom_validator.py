"""温度と症状の矛盾を検証するバリデータ"""

from __future__ import annotations
import logging
from functools import lru_cache
from src.data.weather_data import WeatherForecast
from src.config.config import get_weather_constants, get_validator_words

# 定数を取得
_weather_const = get_weather_constants()
HEATSTROKE_WARNING_TEMP = _weather_const.HEATSTROKE_WARNING_TEMP
COLD_WARNING_TEMP = _weather_const.COLD_WARNING_TEMP

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_temperature_symptom_config():
    """温度症状設定を取得（キャッシュ付き）"""
    config = get_validator_words()
    return config.get('temperature_symptom', {})


class TemperatureSymptomValidator:
    """温度と健康症状の矛盾を検証"""
    
    def check_temperature_symptom_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        温度と症状の表現が矛盾していないかチェック
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            weather_data: 天気データ
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        combined_text = weather_comment + " " + advice_comment
        config = _get_temperature_symptom_config()
        
        # 高温時の矛盾チェック
        if weather_data.temperature >= HEATSTROKE_WARNING_TEMP:
            # 高温時に冷え対策は矛盾
            cold_protection = config.get('cold_protection', ["防寒", "厚着", "温かい服装", "カイロ", "マフラー"])
            for expr in cold_protection:
                if expr in combined_text:
                    return False, f"高温時({weather_data.temperature}°C)に不適切な防寒対策: {expr}"
        
        # 低温時の矛盾チェック
        if weather_data.temperature <= COLD_WARNING_TEMP:
            # 低温時に熱中症対策は矛盾
            heat_protection = config.get('heat_protection', ["熱中症", "水分補給", "塩分補給", "日陰で休憩", "クーラー"])
            for expr in heat_protection:
                if expr in combined_text:
                    return False, f"低温時({weather_data.temperature}°C)に不適切な熱中症対策: {expr}"
        
        # 中間温度での極端な表現チェック
        mild_temp_config = config.get('mild_temperature', {'min': 15, 'max': 25})
        mild_temp_min = mild_temp_config.get('min', 15)
        mild_temp_max = mild_temp_config.get('max', 25)
        
        if mild_temp_min <= weather_data.temperature <= mild_temp_max:
            extreme_expressions = config.get('extreme_expressions', ["猛暑", "酷暑", "極寒", "凍える", "熱中症警戒", "防寒必須"])
            for expr in extreme_expressions:
                if expr in combined_text:
                    return False, f"穏やかな気温({weather_data.temperature}°C)で極端な表現: {expr}"
        
        return True, ""