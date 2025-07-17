"""傘関連の重複を検証するバリデータ"""

from __future__ import annotations
import logging
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class UmbrellaRedundancyValidator:
    """傘関連コメントの重複を検証"""
    
    def check_umbrella_redundancy(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        傘に関する表現の重複をチェック
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            weather_data: 天気データ（参考情報）
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # 傘関連の表現パターン
        umbrella_patterns = [
            ("傘をお忘れなく", "傘を持って"),
            ("傘が必要", "傘をお忘れなく"),
            ("傘を持参", "傘を準備"),
            ("雨具を", "傘を"),
            ("レインコート", "雨合羽"),
            ("雨対策", "雨具"),
        ]
        
        # 各パターンをチェック
        for pattern1, pattern2 in umbrella_patterns:
            if pattern1 in weather_comment and pattern2 in advice_comment:
                return False, f"傘・雨具の表現が重複: 「{pattern1}」と「{pattern2}」"
            if pattern2 in weather_comment and pattern1 in advice_comment:
                return False, f"傘・雨具の表現が重複: 「{pattern2}」と「{pattern1}」"
        
        # 同じ傘表現の完全重複チェック
        umbrella_words = ["傘", "雨具", "レインコート", "雨合羽", "雨対策"]
        for word in umbrella_words:
            if word in weather_comment and word in advice_comment:
                # ただし、文脈が異なる場合は許容
                if not self._is_different_context(weather_comment, advice_comment, word):
                    return False, f"「{word}」が両方のコメントで重複"
        
        # 晴天時の傘言及チェック
        if weather_data.precipitation < 0.1 and "晴" in weather_data.weather_description:
            if any(word in weather_comment + advice_comment for word in ["傘", "雨具"]):
                return False, "晴天時に傘・雨具への言及は不適切"
        
        return True, ""
    
    def _is_different_context(self, text1: str, text2: str, word: str) -> bool:
        """
        同じ単語が異なる文脈で使われているかチェック
        
        例：「折り畳み傘」と「日傘」は異なる文脈
        """
        # 文脈を区別するための修飾語
        context_modifiers = {
            "傘": ["折り畳み", "日", "雨", "大きな", "小さな"],
            "雨具": ["簡易", "本格的な", "防水"],
        }
        
        modifiers = context_modifiers.get(word, [])
        context1 = None
        context2 = None
        
        for modifier in modifiers:
            if modifier + word in text1:
                context1 = modifier
            if modifier + word in text2:
                context2 = modifier
        
        # 異なる修飾語があれば異なる文脈
        return context1 != context2 and context1 is not None and context2 is not None