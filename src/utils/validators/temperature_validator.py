"""温度条件バリデータ - 気温に基づくコメント検証"""

import logging
from typing import Tuple, Dict, List

from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    HEATSTROKE_SEVERE_TEMP,
    COLD_WARNING_TEMP,
)
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class TemperatureValidator(BaseValidator):
    """温度条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        super().__init__()
        self._initialize_temperature_forbidden_words()
    
    def _initialize_temperature_forbidden_words(self):
        """温度別禁止ワードの定義（詳細な温度範囲に基づく）"""
        self.temperature_forbidden_words = {
            "moderate_warm": {  # 25-33°C（中程度の暖かさ）
                "forbidden": [
                    "寒い", "冷える", "肌寒い", "防寒", "厚着",
                    # 31°Cで「厳しい暑さ」は過大
                    "厳しい暑さ", "酷暑", "激しい暑さ", "耐え難い暑さ",
                    "猛烈な暑さ", "危険な暑さ"
                ]
            },
            "very_hot": {  # 34°C以上（猛暑日）
                "forbidden": ["寒い", "冷える", "肌寒い", "防寒", "暖かく", "厚着"]
            },
            "extreme_hot": {  # 37°C以上（危険な暑さ）
                "forbidden": ["寒い", "冷える", "肌寒い", "防寒", "暖かく", "厚着"]
            },
            "cold": {  # 12°C未満
                "forbidden": [
                    "暑い", "猛暑", "酷暑", "熱中症", "クーラー", "冷房",
                    "厳しい暑さ", "激しい暑さ"
                ]
            },
            "mild": {  # 12-25°C（快適域）
                "forbidden": [
                    "極寒", "凍える", "猛暑", "酷暑", 
                    "厳しい暑さ", "激しい暑さ", "耐え難い暑さ"
                ]
            }
        }
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """温度条件に基づいてコメントを検証"""
        return self._check_temperature_conditions(
            comment.comment_text, 
            weather_data
        )
    
    def _check_temperature_conditions(self, comment_text: str, 
                                    weather_data: WeatherForecast) -> Tuple[bool, str]:
        """温度条件に基づく検証（詳細な温度範囲）"""
        temp = weather_data.temperature
        
        # 詳細な温度範囲による分類
        if temp >= 37:
            forbidden = self.temperature_forbidden_words["extreme_hot"]["forbidden"]
            temp_category = "危険な暑さ"
        elif temp >= HEATSTROKE_SEVERE_TEMP:
            forbidden = self.temperature_forbidden_words["very_hot"]["forbidden"]
            temp_category = "猛暑日"
        elif temp >= 25:
            forbidden = self.temperature_forbidden_words["moderate_warm"]["forbidden"]
            temp_category = "中程度の暖かさ"
            # 34°C未満で熱中症は控えめに
            if temp < HEATSTROKE_WARNING_TEMP and "熱中症" in comment_text:
                logger.info(
                    f"温度不適切表現除外: '{comment_text}' - 理由: {temp}°C（{HEATSTROKE_WARNING_TEMP}°C未満）で「熱中症」表現は過大"
                )
                return False, f"温度{temp}°C（{HEATSTROKE_WARNING_TEMP}°C未満）で「熱中症」表現は過大"
        elif temp < 12:
            forbidden = self.temperature_forbidden_words["cold"]["forbidden"]
            temp_category = "寒い"
        else:
            forbidden = self.temperature_forbidden_words["mild"]["forbidden"]
            temp_category = "快適域"
        
        for word in forbidden:
            if word in comment_text:
                logger.info(f"温度不適切表現除外: '{comment_text}' - 理由: {temp}°C（{temp_category}）で禁止ワード「{word}」を含む")
                return False, f"温度{temp}°C（{temp_category}）で禁止ワード「{word}」を含む"
        
        return True, "温度条件OK"
    
    def _check_temperature_symptom_contradiction(self, weather_comment: str, 
                                               advice_comment: str,
                                               temperature: float) -> Tuple[bool, str]:
        """温度と症状の矛盾をチェック"""
        # 高温時の体調不良表現
        if temperature >= HEATSTROKE_WARNING_TEMP:
            cold_symptoms = ["風邪", "冷え", "寒気", "凍え"]
            for symptom in cold_symptoms:
                if symptom in weather_comment or symptom in advice_comment:
                    return False, f"高温（{temperature}°C）で寒さ関連の症状「{symptom}」"
        
        # 低温時の体調不良表現
        if temperature <= COLD_WARNING_TEMP:
            heat_symptoms = ["熱中症", "脱水", "熱射病", "日射病"]
            for symptom in heat_symptoms:
                if symptom in weather_comment or symptom in advice_comment:
                    return False, f"低温（{temperature}°C）で暑さ関連の症状「{symptom}」"
        
        return True, ""