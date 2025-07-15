"""重複チェック共通ユーティリティ"""

import logging
from typing import Tuple, Set

from src.constants.validation_constants import (
    PUNCTUATION_PATTERN,
    REPETITIVE_PATTERNS,
    DUPLICATE_KEYWORDS,
    CRITICAL_DUPLICATE_KEYWORDS,
    UMBRELLA_EXPRESSIONS,
    CONTRADICTION_PATTERNS,
    SIMILARITY_PATTERNS
)

logger = logging.getLogger(__name__)


class DuplicationChecker:
    """重複チェックの共通ロジックを提供するユーティリティクラス"""
    
    # パターンの事前処理（パフォーマンス最適化）
    _repetitive_pattern_cache = {
        pattern["concept"]: pattern["expressions"] 
        for pattern in REPETITIVE_PATTERNS
    }
    
    @staticmethod
    def check_repetitive_concepts(weather_text: str, advice_text: str) -> bool:
        """
        同じ概念の繰り返しをチェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            重複が検出された場合True
        """
        for concept, expressions in DuplicationChecker._repetitive_pattern_cache.items():
            weather_expressions = [expr for expr in expressions if expr in weather_text]
            advice_expressions = [expr for expr in expressions if expr in advice_text]
            
            if weather_expressions and advice_expressions:
                logger.debug(f"同一概念の繰り返し検出 [{concept}]: 天気={weather_expressions}, アドバイス={advice_expressions}")
                return True
        
        return False

    @staticmethod
    def check_text_similarity(weather_text: str, advice_text: str) -> bool:
        """
        テキストの類似性をチェック（完全一致・ほぼ一致）
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            類似性が高い場合True
        """
        # 完全一致
        if weather_text == advice_text:
            return True
            
        # ほぼ同じ内容の検出（語尾の微差を無視）
        weather_normalized = weather_text.replace("です", "").replace("だ", "").replace("である", "").replace("。", "").strip()
        advice_normalized = advice_text.replace("です", "").replace("だ", "").replace("である", "").replace("。", "").strip()
        
        if weather_normalized == advice_normalized:
            logger.debug(f"ほぼ完全一致検出: '{weather_text}' ≈ '{advice_text}'")
            return True
            
        # 句読点や助詞の差のみの場合も検出
        weather_core = PUNCTUATION_PATTERN.sub('', weather_text)
        advice_core = PUNCTUATION_PATTERN.sub('', advice_text)
        
        if weather_core == advice_core:
            logger.debug(f"句読点差のみ検出: '{weather_text}' ≈ '{advice_text}'")
            return True
        
        return False

    @staticmethod
    def check_keyword_duplication(weather_text: str, advice_text: str) -> bool:
        """
        重要キーワードの重複をチェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            重要キーワードの重複が検出された場合True
        """
        weather_keywords = []
        advice_keywords = []
        
        for keyword in DUPLICATE_KEYWORDS:
            if keyword in weather_text:
                weather_keywords.append(keyword)
            if keyword in advice_text:
                advice_keywords.append(keyword)
        
        common_keywords = set(weather_keywords) & set(advice_keywords)
        if common_keywords:
            if any(keyword in CRITICAL_DUPLICATE_KEYWORDS for keyword in common_keywords):
                logger.debug(f"重複キーワード検出: {common_keywords}")
                return True
        
        return False

    @staticmethod
    def check_semantic_contradiction(weather_text: str, advice_text: str) -> bool:
        """
        意味的矛盾パターンをチェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            意味的矛盾が検出された場合True
        """
        for positive_patterns, negative_patterns in CONTRADICTION_PATTERNS:
            has_positive = any(pattern in weather_text for pattern in positive_patterns)
            has_negative = any(pattern in advice_text for pattern in negative_patterns)
            
            has_positive_advice = any(pattern in advice_text for pattern in positive_patterns)
            has_negative_weather = any(pattern in weather_text for pattern in negative_patterns)
            
            if (has_positive and has_negative) or (has_positive_advice and has_negative_weather):
                logger.debug(f"意味的矛盾検出: ポジティブ={positive_patterns}, ネガティブ={negative_patterns}")
                logger.debug(f"天気コメント: '{weather_text}', アドバイス: '{advice_text}'")
                return True
        
        return False

    @staticmethod
    def check_similar_expressions(weather_text: str, advice_text: str) -> bool:
        """
        類似表現パターンをチェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            類似表現が検出された場合True
        """
        for weather_patterns, advice_patterns in SIMILARITY_PATTERNS:
            weather_match = any(pattern in weather_text for pattern in weather_patterns)
            advice_match = any(pattern in advice_text for pattern in advice_patterns)
            if weather_match and advice_match:
                logger.debug(f"類似表現検出: 天気パターン={weather_patterns}, アドバイスパターン={advice_patterns}")
                return True
        
        return False

    @staticmethod
    def check_umbrella_duplication(weather_text: str, advice_text: str) -> bool:
        """
        傘関連の重複を特別チェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            
        Returns:
            傘関連の重複が検出された場合True
        """
        weather_has_umbrella = any(expr in weather_text for expr in UMBRELLA_EXPRESSIONS) or "傘" in weather_text
        advice_has_umbrella = any(expr in advice_text for expr in UMBRELLA_EXPRESSIONS) or "傘" in advice_text
        
        if weather_has_umbrella and advice_has_umbrella:
            logger.debug(f"傘関連の重複候補検出: 天気='{weather_text}', アドバイス='{advice_text}'")
            
            similar_umbrella_meanings = [
                ["必須", "お守り", "必要", "忘れずに", "お忘れなく", "携帯", "準備", "活躍", "安心"],
            ]
            
            for meaning_group in similar_umbrella_meanings:
                weather_meanings = [m for m in meaning_group if m in weather_text]
                advice_meanings = [m for m in meaning_group if m in advice_text]
                
                if weather_meanings and advice_meanings:
                    logger.debug(f"傘関連の意味的重複検出: 天気側={weather_meanings}, アドバイス側={advice_meanings}")
                    return True
        
        return False

    @staticmethod
    def check_character_similarity(weather_text: str, advice_text: str, threshold: float = 0.7) -> bool:
        """
        短いテキストの文字列類似度をチェック
        
        Args:
            weather_text: 天気コメントテキスト
            advice_text: アドバイステキスト
            threshold: 類似度の闾値（デフォルト: 0.7）
            
        Returns:
            類似度が闾値を超えた場合True
        """
        if len(weather_text) <= 10 and len(advice_text) <= 10:
            min_length = min(len(weather_text), len(advice_text))
            if min_length == 0:
                return False
                
            max_length = max(len(weather_text), len(advice_text))
            if max_length / min_length > 2.0:
                return False
            
            common_chars = set(weather_text) & set(advice_text)
            similarity_ratio = len(common_chars) / max_length
            
            if similarity_ratio > threshold:
                logger.debug(f"高い文字列類似度検出: {similarity_ratio:.2f}")
                return True
        
        return False