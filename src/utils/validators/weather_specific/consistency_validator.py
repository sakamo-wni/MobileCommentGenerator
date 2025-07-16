"""一貫性バリデーター - コメントペアの一貫性を検証"""

import logging
from typing import Any
import re

from src.config.config import get_weather_constants

# 定数を取得
SUNNY_WEATHER_KEYWORDS = get_weather_constants().SUNNY_WEATHER_KEYWORDS
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class ConsistencyValidator:
    """天気コメントとアドバイスの一貫性を検証"""
    
    def __init__(self):
        # 矛盾する表現のペア
        self.contradictory_pairs = {
            "weather_mood": {
                # ポジティブな天気表現
                "positive": ["青空", "晴れ", "快晴", "心地良い", "爽やか", "気持ちいい"],
                # ネガティブな天気表現
                "negative": ["どんより", "じめじめ", "蒸し暑い", "不快", "うっとうしい"]
            },
            "activity": {
                # アウトドア活動
                "outdoor": ["お出かけ", "散歩", "ピクニック", "外出", "レジャー"],
                # インドア活動
                "indoor": ["室内で", "家で", "屋内", "おうち時間"]
            }
        }
    
    def check_weather_reality_contradiction(
        self, 
        weather_comment: str, 
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """天気の現実と表現の矛盾をチェック"""
        weather_desc = weather_data.weather_description.lower()
        temp = weather_data.temperature
        
        # 晴れまたは薄曇りなのに雲が優勢と言っている矛盾
        if any(sunny_word in weather_desc for sunny_word in SUNNY_WEATHER_KEYWORDS):
            cloud_dominant_phrases = [
                "雲が優勢", "雲が多い", "雲に覆われ", "厚い雲", "雲がち",
                "どんより", "曇り空", "灰色の空"
            ]
            for phrase in cloud_dominant_phrases:
                if phrase in weather_comment:
                    return False, f"晴天なのに「{phrase}」は矛盾"
        
        # 雨なのに晴れていると言っている矛盾
        if "雨" in weather_desc or "rain" in weather_desc:
            sunny_phrases = [
                "青空", "晴れ", "快晴", "太陽", "日差し", "陽射し",
                "雲一つない", "澄み渡る空"
            ]
            for phrase in sunny_phrases:
                if phrase in weather_comment:
                    return False, f"雨天なのに「{phrase}」は矛盾"
        
        # 暑いのに寒いと言っている矛盾
        if temp >= 30:
            cold_phrases = ["肌寒い", "冷え込み", "ひんやり", "涼しい", "冷たい風"]
            for phrase in cold_phrases:
                if phrase in weather_comment:
                    return False, f"高温（{temp}°C）なのに「{phrase}」は矛盾"
        
        # 寒いのに暑いと言っている矛盾
        elif temp <= 10:
            hot_phrases = ["蒸し暑い", "汗ばむ", "暑さ", "真夏日", "熱気"]
            for phrase in hot_phrases:
                if phrase in weather_comment:
                    return False, f"低温（{temp}°C）なのに「{phrase}」は矛盾"
        
        return True, "天気と現実の一貫性OK"
    
    def check_content_duplication(
        self,
        weather_comment: str,
        advice_comment: str
    ) -> tuple[bool, str]:
        """重複・類似表現チェック"""
        # 完全一致チェック
        if weather_comment.strip() == advice_comment.strip():
            return False, "天気コメントとアドバイスが完全に同じ"
        
        # 部分的な重複チェック（文の70%以上が同じ）
        if self._is_duplicate_content(weather_comment, advice_comment):
            return False, "天気コメントとアドバイスの内容が重複"
        
        # 傘に関する重複チェック
        umbrella_check = self._check_umbrella_redundancy(weather_comment, advice_comment)
        if not umbrella_check[0]:
            return umbrella_check
        
        return True, "重複チェックOK"
    
    def check_tone_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """矛盾する態度・トーンチェック"""
        # ポジティブ/ネガティブのトーン分析
        weather_positive = self._count_positive_words(weather_comment)
        weather_negative = self._count_negative_words(weather_comment)
        advice_positive = self._count_positive_words(advice_comment)
        advice_negative = self._count_negative_words(advice_comment)
        
        # 天気が良いのに両方ネガティブ
        if self._is_good_weather(weather_data):
            if weather_negative > weather_positive and advice_negative > advice_positive:
                return False, "良い天気なのに両方のコメントがネガティブ"
        
        # 天気が悪いのに両方ポジティブ
        elif self._is_bad_weather(weather_data):
            if weather_positive > weather_negative and advice_positive > advice_negative:
                return False, "悪い天気なのに両方のコメントが過度にポジティブ"
        
        # 極端にトーンが異なる（片方が非常にポジティブ、もう片方が非常にネガティブ）
        tone_diff = abs((weather_positive - weather_negative) - (advice_positive - advice_negative))
        if tone_diff > 3:
            return False, "天気コメントとアドバイスのトーンが大きく異なる"
        
        return True, "トーンの一貫性OK"
    
    def _check_umbrella_redundancy(
        self,
        weather_comment: str,
        advice_comment: str
    ) -> tuple[bool, str]:
        """傘コメントの重複チェック"""
        umbrella_patterns = [
            r"傘[がをは]必要",
            r"傘[がをは]必須",
            r"傘[をは]持って",
            r"傘[をは]忘れずに",
            r"雨具[がをは]必要",
            r"レインコート",
            r"雨対策"
        ]
        
        weather_has_umbrella = any(re.search(pattern, weather_comment) for pattern in umbrella_patterns)
        advice_has_umbrella = any(re.search(pattern, advice_comment) for pattern in umbrella_patterns)
        
        if weather_has_umbrella and advice_has_umbrella:
            return False, "傘に関するコメントが重複"
        
        return True, "傘コメント重複なし"
    
    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """内容の重複を判定（70%以上の単語が共通）"""
        # 句読点・記号を除去
        weather_clean = re.sub(r'[、。！？\s]', '', weather_text)
        advice_clean = re.sub(r'[、。！？\s]', '', advice_text)
        
        # 短いテキストは除外
        if len(weather_clean) < 10 or len(advice_clean) < 10:
            return False
        
        # 文字単位での比較
        weather_chars = set(weather_clean)
        advice_chars = set(advice_clean)
        
        # 共通文字の割合を計算
        common_chars = weather_chars & advice_chars
        total_chars = weather_chars | advice_chars
        
        if len(total_chars) == 0:
            return False
        
        similarity_ratio = len(common_chars) / len(total_chars)
        
        return similarity_ratio > 0.7
    
    def _count_positive_words(self, text: str) -> int:
        """ポジティブな単語をカウント"""
        positive_words = [
            "快適", "心地良い", "爽やか", "気持ちいい", "最高", "素敵",
            "楽しい", "嬉しい", "良い", "素晴らしい", "快晴", "青空",
            "穏やか", "のどか", "過ごしやすい"
        ]
        return sum(1 for word in positive_words if word in text)
    
    def _count_negative_words(self, text: str) -> int:
        """ネガティブな単語をカウント"""
        negative_words = [
            "注意", "警戒", "危険", "不快", "じめじめ", "蒸し暑い",
            "厳しい", "辛い", "大変", "困る", "悪い", "最悪",
            "どんより", "うっとうしい", "憂鬱"
        ]
        return sum(1 for word in negative_words if word in text)
    
    def _is_good_weather(self, weather_data: WeatherForecast) -> bool:
        """良い天気かどうか判定"""
        weather_desc = weather_data.weather_description.lower()
        good_patterns = ["晴", "快晴", "sunny", "clear"]
        bad_patterns = ["雨", "雪", "嵐", "台風"]
        
        has_good = any(pattern in weather_desc for pattern in good_patterns)
        has_bad = any(pattern in weather_desc for pattern in bad_patterns)
        
        return has_good and not has_bad and 15 <= weather_data.temperature <= 28
    
    def _is_bad_weather(self, weather_data: WeatherForecast) -> bool:
        """悪い天気かどうか判定"""
        weather_desc = weather_data.weather_description.lower()
        bad_patterns = ["雨", "雪", "嵐", "台風", "豪雨", "大雨", "暴風"]
        
        return any(pattern in weather_desc for pattern in bad_patterns)