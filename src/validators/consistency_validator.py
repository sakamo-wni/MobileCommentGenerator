"""一貫性検証モジュール - 天気コメントとアドバイスの一貫性検証"""

import logging
from typing import Tuple, Optional
import re

from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.validators.base_validator import BaseValidator

logger = logging.getLogger(__name__)


class ConsistencyValidator(BaseValidator):
    """天気コメントとアドバイスの一貫性を検証するクラス"""
    
    def validate_comment_pair_consistency(self, comment_pair: CommentPair, 
                                        weather_data: WeatherForecast,
                                        location: Optional[str] = None) -> Tuple[bool, str]:
        """天気コメントとアドバイスの一貫性をチェック"""
        if not comment_pair.weather_comment or not comment_pair.advice_comment:
            return True, ""
        
        weather_text = comment_pair.weather_comment.text
        advice_text = comment_pair.advice_comment.text
        
        # 各種一貫性チェック
        checks = [
            self._check_weather_reality_contradiction(weather_text, advice_text),
            self._check_content_duplication(weather_text, advice_text),
            self._check_tone_contradiction(weather_text, advice_text),
            self._check_umbrella_redundancy(weather_text, advice_text),
        ]
        
        # すべてのチェックを実行
        for is_valid, reason in checks:
            if not is_valid:
                return False, reason
        
        return True, ""
    
    def _check_weather_reality_contradiction(self, weather_text: str, 
                                           advice_text: str) -> Tuple[bool, str]:
        """天気の現実とアドバイスの矛盾をチェック"""
        # 晴れ関連
        sunny_weather_words = ["晴れ", "快晴", "日差し", "青空", "太陽"]
        rainy_advice_words = ["傘", "雨具", "レインコート", "濡れ"]
        
        # 晴れなのに雨対策
        if any(word in weather_text for word in sunny_weather_words):
            if any(word in advice_text for word in rainy_advice_words):
                return False, "晴天時に雨具のアドバイスは矛盾"
        
        # 雨関連
        rainy_weather_words = ["雨", "降水", "降り"]
        sunny_advice_words = ["日焼け止め", "日傘", "サングラス", "紫外線"]
        
        # 雨なのに日焼け対策
        if any(word in weather_text for word in rainy_weather_words):
            if any(word in advice_text for word in sunny_advice_words):
                return False, "雨天時に日焼け対策のアドバイスは矛盾"
        
        # 暑さ・寒さの矛盾
        hot_weather_words = ["暑い", "猛暑", "酷暑", "真夏日", "熱帯夜"]
        cold_advice_words = ["防寒", "厚着", "暖かく", "マフラー", "手袋"]
        
        if any(word in weather_text for word in hot_weather_words):
            if any(word in advice_text for word in cold_advice_words):
                return False, "暑い天気で防寒対策は矛盾"
        
        cold_weather_words = ["寒い", "冷え", "厳しい寒さ", "氷点下"]
        hot_advice_words = ["熱中症", "水分補給", "クーラー", "冷房"]
        
        if any(word in weather_text for word in cold_weather_words):
            if any(word in advice_text for word in hot_advice_words):
                return False, "寒い天気で熱中症対策は矛盾"
        
        return True, ""
    
    def _check_content_duplication(self, weather_text: str, 
                                 advice_text: str) -> Tuple[bool, str]:
        """天気説明とアドバイスの内容重複をチェック"""
        # より厳密な重複チェック
        if self._is_duplicate_content(weather_text, advice_text):
            return False, "天気説明とアドバイスが重複"
        
        # 同じフレーズの繰り返しチェック
        weather_words = set(weather_text.replace("。", "").replace("、", "").split())
        advice_words = set(advice_text.replace("。", "").replace("、", "").split())
        
        # 共通単語が多すぎる場合（50%以上）
        if len(weather_words) > 0 and len(advice_words) > 0:
            common_words = weather_words & advice_words
            similarity_ratio = len(common_words) / min(len(weather_words), len(advice_words))
            if similarity_ratio > 0.5:
                return False, f"内容の重複が多い（類似度: {similarity_ratio:.0%}）"
        
        return True, ""
    
    def _check_tone_contradiction(self, weather_text: str, 
                                advice_text: str) -> Tuple[bool, str]:
        """トーンの矛盾をチェック"""
        # ポジティブ・ネガティブなトーンの判定
        positive_weather_words = [
            "快晴", "爽やか", "心地良い", "穏やか", "気持ちいい",
            "過ごしやすい", "快適", "さわやか"
        ]
        negative_weather_words = [
            "厳しい", "激しい", "荒れ", "悪天候", "警戒",
            "危険", "注意", "警報"
        ]
        
        urgent_advice_words = [
            "警戒", "注意", "危険", "避難", "厳重",
            "必ず", "絶対", "要注意"
        ]
        casual_advice_words = [
            "楽しんで", "のんびり", "ゆったり", "リラックス",
            "お出かけ", "散歩"
        ]
        
        # ポジティブな天気で緊急性の高いアドバイス
        is_positive_weather = any(word in weather_text for word in positive_weather_words)
        has_urgent_advice = any(word in advice_text for word in urgent_advice_words)
        
        if is_positive_weather and has_urgent_advice:
            return False, "穏やかな天気で緊急性の高いアドバイスは不適切"
        
        # ネガティブな天気でカジュアルなアドバイス
        is_negative_weather = any(word in weather_text for word in negative_weather_words)
        has_casual_advice = any(word in advice_text for word in casual_advice_words)
        
        if is_negative_weather and has_casual_advice:
            return False, "厳しい天気でカジュアルなアドバイスは不適切"
        
        return True, ""
    
    def _check_umbrella_redundancy(self, weather_text: str, 
                                  advice_text: str) -> Tuple[bool, str]:
        """傘に関する冗長性チェック"""
        # 天気コメントで既に傘について言及している場合
        weather_umbrella_patterns = [
            "傘.*必要", "傘.*持って", "傘.*忘れ", "傘.*用意",
            "雨具.*必要", "雨具.*持って"
        ]
        
        advice_umbrella_patterns = [
            "傘", "雨具", "レインコート", "レイングッズ"
        ]
        
        # 天気コメントで傘に言及
        weather_mentions_umbrella = any(
            re.search(pattern, weather_text) for pattern in weather_umbrella_patterns
        )
        
        # アドバイスでも傘に言及
        advice_mentions_umbrella = any(
            word in advice_text for word in advice_umbrella_patterns
        )
        
        if weather_mentions_umbrella and advice_mentions_umbrella:
            # より詳細なチェック
            if "傘" in weather_text and "傘" in advice_text:
                return False, "傘への言及が重複"
        
        return True, ""
    
    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """内容の重複を判定する詳細なロジック"""
        # 句読点を除去して比較
        weather_clean = weather_text.replace("。", "").replace("、", "").strip()
        advice_clean = advice_text.replace("。", "").replace("、", "").strip()
        
        # 完全一致
        if weather_clean == advice_clean:
            return True
        
        # 部分一致（一方が他方を含む）
        if weather_clean in advice_clean or advice_clean in weather_clean:
            return True
        
        # キーフレーズの重複チェック
        # 3文字以上の共通フレーズを探す
        min_phrase_length = 3
        for i in range(len(weather_clean) - min_phrase_length + 1):
            phrase = weather_clean[i:i + min_phrase_length]
            if phrase in advice_clean:
                # より長いフレーズをチェック
                j = min_phrase_length
                while i + j <= len(weather_clean) and weather_clean[i:i + j] in advice_clean:
                    j += 1
                
                # 5文字以上の共通フレーズがあれば重複と判定
                if j - 1 >= 5:
                    return True
        
        return False