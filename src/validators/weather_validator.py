"""天気条件検証モジュール - 天気状態に基づく検証"""

import logging
from typing import Tuple

from src.data.weather_data import WeatherForecast, WeatherCondition
from src.validators.base_validator import BaseValidator, SUNNY_WEATHER_KEYWORDS

logger = logging.getLogger(__name__)


class WeatherValidator(BaseValidator):
    """天気条件に基づく検証クラス"""
    
    def check_weather_conditions(self, comment_text: str, comment_type: str, 
                               weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づいてコメントの適切性をチェック"""
        weather_str = weather_data.weather.value
        
        # 安定した曇り空の判定
        is_stable_cloudy = self._is_stable_cloudy_weather(weather_data)
        
        # 天気別チェック
        is_sunny = any(keyword in weather_str for keyword in SUNNY_WEATHER_KEYWORDS)
        is_heavy_rain = any(keyword in weather_str for keyword in ["大雨", "豪雨", "暴風雨", "激しい雨", "非常に激しい雨", "嵐", "台風"])
        is_rainy = any(keyword in weather_str for keyword in ["雨", "雪", "みぞれ"])
        is_cloudy = any(keyword in weather_str for keyword in ["曇", "くもり"])
        
        # 大雨・豪雨チェック（最優先）
        if is_heavy_rain:
            forbidden_words = self.weather_forbidden_words.get("heavy_rain", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"大雨・豪雨時に不適切な表現: '{word}'"
        
        # 通常の雨天チェック
        elif is_rainy:
            forbidden_words = self.weather_forbidden_words.get("rain", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"雨天時に不適切な表現: '{word}'"
            
            # 雨天時の矛盾チェック
            is_valid, reason = self._check_rainy_weather_contradictions(
                comment_text, comment_type, weather_data
            )
            if not is_valid:
                return False, reason
        
        # 晴天チェック
        elif is_sunny:
            forbidden_words = self.weather_forbidden_words.get("sunny", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"晴天時に不適切な表現: '{word}'"
        
        # 曇天チェック
        elif is_cloudy:
            # 安定した曇り空の場合の追加チェック
            if is_stable_cloudy:
                if comment_type == "weather_comment":
                    unstable_keywords = ["変わりやすい", "不安定", "変化", "移ろい"]
                    for keyword in unstable_keywords:
                        if keyword in comment_text:
                            return False, f"安定した曇り空時に不適切な表現: '{keyword}'"
            
            forbidden_words = self.weather_forbidden_words.get("cloudy", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"曇天時に不適切な表現: '{word}'"
        
        return True, ""
    
    def _check_rainy_weather_contradictions(self, comment_text: str, 
                                           comment_type: str,
                                           weather_data: WeatherForecast) -> Tuple[bool, str]:
        """雨天時の矛盾チェック"""
        # 雨の強度に応じた表現チェック
        weather_str = weather_data.weather.value
        
        # 大雨・豪雨時の軽微な雨表現チェック
        if any(word in weather_str for word in ["大雨", "豪雨", "激しい雨"]):
            light_rain_words = ["小雨", "ぱらつく", "しとしと", "霧雨"]
            for word in light_rain_words:
                if word in comment_text:
                    return False, f"大雨時に軽微な雨の表現は不適切: '{word}'"
        
        # 小雨時の激しい雨表現チェック
        elif any(word in weather_str for word in ["小雨", "霧雨", "弱い雨"]):
            heavy_rain_words = ["激しい", "強い雨", "大雨", "豪雨", "土砂降り"]
            for word in heavy_rain_words:
                if word in comment_text:
                    return False, f"小雨時に激しい雨の表現は不適切: '{word}'"
        
        return True, ""
    
    def _is_stable_cloudy_weather(self, weather_data: WeatherForecast) -> bool:
        """安定した曇り空かどうかを判定
        
        3時間の天気が全て曇りの場合、安定した曇り空と判定
        """
        weather_str = weather_data.weather.value
        
        # 「曇り」が含まれているかチェック
        if "曇" not in weather_str and "くもり" not in weather_str:
            return False
        
        # 以下の文字が含まれていたら不安定と判定
        unstable_indicators = ["時々", "のち", "一時", "所により", "変わりやすい"]
        for indicator in unstable_indicators:
            if indicator in weather_str:
                return False
        
        # 安定した曇り空のパターン
        stable_patterns = ["曇り", "くもり", "曇天", "本曇り"]
        return any(pattern in weather_str for pattern in stable_patterns)