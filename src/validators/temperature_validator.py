"""気温条件検証モジュール - 気温に基づく検証"""

import logging
from typing import Tuple

from src.data.weather_data import WeatherForecast
from src.validators.base_validator import BaseValidator

logger = logging.getLogger(__name__)


class TemperatureValidator(BaseValidator):
    """気温条件に基づく検証クラス"""
    
    def check_temperature_conditions(self, comment_text: str, 
                                   comment_type: str,
                                   weather_data: WeatherForecast) -> Tuple[bool, str]:
        """気温条件に基づいてコメントの適切性をチェック"""
        temp = weather_data.temperature
        
        # 各温度範囲でのチェック
        for condition_name, condition_data in self.temperature_forbidden_words.items():
            ranges = condition_data["ranges"]
            for temp_range in ranges:
                if temp_range[0] <= temp <= temp_range[1]:
                    forbidden_words = condition_data.get(comment_type, [])
                    for word in forbidden_words:
                        if word in comment_text:
                            return False, f"{condition_name}（{temp}°C）時に不適切な表現: '{word}'"
        
        # 熱中症関連のキーワードチェック
        if "熱中症" in comment_text:
            if temp < 25:
                return False, f"気温{temp}°Cで熱中症への言及は不適切"
        
        # 防寒関連のキーワードチェック
        cold_keywords = ["防寒", "厚着", "暖かい格好", "マフラー", "手袋", "コート"]
        if any(keyword in comment_text for keyword in cold_keywords):
            if temp > 20:
                return False, f"気温{temp}°Cで防寒への言及は不適切"
        
        return True, ""
    
    def check_temperature_symptom_contradiction(self, weather_text: str, 
                                              advice_text: str,
                                              weather_data: WeatherForecast) -> Tuple[bool, str]:
        """気温と症状の矛盾チェック"""
        temp = weather_data.temperature
        
        # 熱中症関連
        heatstroke_keywords = ["熱中症", "脱水", "熱射病", "日射病"]
        cold_keywords = ["風邪", "冷え", "体を冷やさない", "温かく"]
        
        # 高温時に寒さ対策
        if temp >= 25:
            for keyword in cold_keywords:
                if keyword in advice_text:
                    return False, f"気温{temp}°Cで寒さ対策「{keyword}」は矛盾"
        
        # 低温時に熱中症対策
        if temp < 20:
            for keyword in heatstroke_keywords:
                if keyword in advice_text:
                    return False, f"気温{temp}°Cで熱中症対策「{keyword}」は矛盾"
        
        # 季節と気温の矛盾チェック
        month = weather_data.date.month
        season = self._get_season_from_month(month)
        
        # 夏なのに防寒対策
        if season == "summer":
            winter_keywords = ["防寒", "厚着", "マフラー", "手袋", "ダウン"]
            for keyword in winter_keywords:
                if keyword in advice_text:
                    return False, f"夏期（{month}月）に冬の対策「{keyword}」は不適切"
        
        # 冬なのに熱中症対策
        elif season == "winter":
            summer_keywords = ["熱中症", "日焼け止め", "紫外線対策", "クーラー"]
            for keyword in summer_keywords:
                if keyword in advice_text:
                    return False, f"冬期（{month}月）に夏の対策「{keyword}」は不適切"
        
        return True, ""