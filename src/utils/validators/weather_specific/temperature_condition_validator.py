"""温度条件バリデーター - 温度条件に基づいてコメントの適切性を検証"""

import logging
from typing import Any
from src.config.config import get_weather_constants

# 定数を取得
_weather_const = get_weather_constants()
HEATSTROKE_WARNING_TEMP = _weather_const.HEATSTROKE_WARNING_TEMP
HEATSTROKE_SEVERE_TEMP = _weather_const.HEATSTROKE_SEVERE_TEMP
COLD_WARNING_TEMP = _weather_const.COLD_WARNING_TEMP
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class TemperatureConditionValidator:
    """温度条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        # 温度別禁止ワード（詳細な温度範囲に基づく）
        self.temperature_forbidden_words = {
            "moderate_warm": {  # 25-33°C（中程度の暖かさ）
                "weather_comment": [
                    "凍える", "極寒", "厳しい寒さ", "冷え込み", "氷点下",
                    "防寒", "暖房必須", "鍋日和", "こたつ", 
                    # 過度な暑さ表現も不適切
                    "猛暑日", "危険な暑さ", "記録的猛暑", "熱中症警戒アラート発令中"
                ],
                "advice": [
                    "厚着", "マフラー", "手袋", "ホッカイロ", "暖房器具",
                    "こたつ", "鍋", "熱燗",
                    # 過度な暑さ対策も不適切
                    "熱中症厳重警戒", "炎天下を避けて", "危険な暑さ"
                ]
            },
            "hot": {  # 33°C以上（暑い）
                "weather_comment": [
                    "涼しい", "ひんやり", "冷え込み", "肌寒い", "防寒",
                    "秋らしい", "冬の気配", "紅葉", "木枯らし",
                    "爽やか", "過ごしやすい", "快適", "心地良い", "清々しい"
                ],
                "advice": [
                    "長袖", "防寒", "厚着", "暖房", "温かい飲み物",
                    "こたつ", "ストーブ", "鍋"
                ]
            },
            "very_hot": {  # 35°C以上（非常に暑い）
                "weather_comment": [
                    "涼しい", "ひんやり", "冷え込み", "肌寒い", "防寒",
                    "秋", "冬", "紅葉", "木枯らし", "初雪",
                    "爽やか", "過ごしやすい", "快適", "心地良い", "清々しい",
                    "穏やか", "のどか", "気持ちいい", 
                    # 中程度の暑さ表現も不適切
                    "少し暑い", "やや暑い", "暖かい", "汗ばむ"
                ],
                "advice": [
                    "長袖", "防寒", "厚着", "暖房", "温かい飲み物",
                    "こたつ", "ストーブ", "鍋", "おでん",
                    # 不適切な活動
                    "日中の散歩", "外出推奨", "ピクニック"
                ]
            },
            "cool": {  # 10-15°C（涼しい）
                "weather_comment": [
                    "暑い", "蒸し暑い", "真夏", "猛暑", "酷暑",
                    "汗だく", "熱帯夜", "炎天下", "灼熱"
                ],
                "advice": [
                    "熱中症", "冷房", "クーラー", "水分補給必須",
                    "日射病", "熱射病"
                ]
            },
            "cold": {  # 5°C以下（寒い）
                "weather_comment": [
                    "暖かい", "ぽかぽか", "春らしい", "過ごしやすい",
                    "半袖", "汗ばむ", "夏日", "暑い"
                ],
                "advice": [
                    "半袖", "薄着", "冷房", "クーラー", "扇風機",
                    "冷たい飲み物", "アイス", "かき氷"
                ]
            },
            "very_cold": {  # 0°C以下（非常に寒い）
                "weather_comment": [
                    "暖かい", "ぽかぽか", "春", "過ごしやすい", "穏やか",
                    "心地良い", "快適", "爽やか", "温暖", "陽気",
                    "暑い", "蒸し暑い", "汗", "夏"
                ],
                "advice": [
                    "薄着", "半袖", "冷房", "扇風機", "日傘",
                    "冷たい飲み物", "アイス", "プール", "海水浴"
                ]
            }
        }
    
    def check_temperature_conditions(
        self, 
        comment_text: str,
        comment_type: str,
        temperature: float
    ) -> tuple[bool, str]:
        """温度条件に基づく検証"""
        # 気温に基づいて該当する温度カテゴリを決定
        temp_category = self._get_temperature_category(temperature)
        
        if temp_category:
            forbidden_words = self.temperature_forbidden_words.get(temp_category, {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"{temperature}°Cで「{word}」は不適切"
        
        # 追加の温度チェック（極端な表現）
        if temperature >= HEATSTROKE_SEVERE_TEMP:  # 35°C以上
            cold_words = ["寒い", "冷える", "凍える", "肌寒い", "ひんやり", "涼しい"]
            for word in cold_words:
                if word in comment_text:
                    return False, f"高温（{temperature}°C）で「{word}」は不適切"
        
        elif temperature <= COLD_WARNING_TEMP:  # 5°C以下
            hot_words = ["暑い", "蒸し暑い", "汗", "熱中症", "猛暑", "真夏日"]
            for word in hot_words:
                if word in comment_text:
                    return False, f"低温（{temperature}°C）で「{word}」は不適切"
        
        return True, "温度条件チェックOK"
    
    def _get_temperature_category(self, temperature: float) -> str:
        """温度からカテゴリを判定"""
        if temperature >= 35:
            return "very_hot"
        elif temperature >= 33:
            return "hot"
        elif 25 <= temperature < 33:
            return "moderate_warm"
        elif 10 <= temperature < 15:
            return "cool"
        elif 0 < temperature <= 5:
            return "cold"
        elif temperature <= 0:
            return "very_cold"
        else:
            return ""
    
    def check_temperature_symptom_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """温度と症状の矛盾をチェック"""
        temp = weather_data.temperature
        
        # 高温時の矛盾チェック
        if temp >= HEATSTROKE_WARNING_TEMP:
            cold_symptoms = [
                "風邪", "インフルエンザ", "冷え性", "手足が冷える",
                "体を温める", "冷え対策", "乾燥対策", "のどの乾燥"
            ]
            for symptom in cold_symptoms:
                if symptom in weather_comment or symptom in advice_comment:
                    return False, f"高温（{temp}°C）で「{symptom}」は矛盾"
        
        # 低温時の矛盾チェック
        elif temp <= COLD_WARNING_TEMP:
            heat_symptoms = [
                "熱中症", "脱水症状", "日射病", "熱射病", "夏バテ",
                "紫外線対策", "日焼け止め"
            ]
            for symptom in heat_symptoms:
                if symptom in weather_comment or symptom in advice_comment:
                    return False, f"低温（{temp}°C）で「{symptom}」は矛盾"
        
        return True, "温度と症状の一貫性OK"