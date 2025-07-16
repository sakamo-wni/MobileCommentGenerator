"""重複チェックバリデーター"""

import logging

from src.constants.validation_constants import SIMILARITY_THRESHOLD
from src.utils.validators.duplication_checker import DuplicationChecker

logger = logging.getLogger(__name__)


class DuplicationValidator:
    """重複チェック関連のバリデーション"""
    
    def __init__(self):
        pass
    
    def is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """天気コメントとアドバイスコメントが重複しているか判定"""
        weather_text = weather_text.strip()
        advice_text = advice_text.strip()
        
        # 6つの判定基準のいずれかに該当したら重複とみなす
        checks = [
            self._check_basic_duplication(weather_text, advice_text),
            self._check_keyword_duplication(weather_text, advice_text),
            self._check_semantic_contradiction(weather_text, advice_text),
            self._check_umbrella_duplication(weather_text, advice_text),
            self._check_similar_expressions(weather_text, advice_text),
            self._check_string_similarity(weather_text, advice_text)
        ]
        
        return any(checks)
    
    def _check_basic_duplication(self, weather_text: str, advice_text: str) -> bool:
        """基本的な重複チェック"""
        return DuplicationChecker.check_basic_duplication(weather_text, advice_text)
    
    def _check_keyword_duplication(self, weather_text: str, advice_text: str) -> bool:
        """キーワードの重複チェック"""
        return DuplicationChecker.check_keyword_duplication(weather_text, advice_text)
    
    def _check_semantic_contradiction(self, weather_text: str, advice_text: str) -> bool:
        """意味的な矛盾チェック"""
        return DuplicationChecker.check_semantic_contradiction(weather_text, advice_text)
    
    def _check_umbrella_duplication(self, weather_text: str, advice_text: str) -> bool:
        """傘に関する重複チェック"""
        return DuplicationChecker.check_umbrella_duplication(weather_text, advice_text)
    
    def _check_similar_expressions(self, weather_text: str, advice_text: str) -> bool:
        """類似表現チェック"""
        return DuplicationChecker.check_similar_expressions(weather_text, advice_text)
    
    def _check_string_similarity(self, weather_text: str, advice_text: str) -> bool:
        """文字列の類似度チェック"""
        return DuplicationChecker.check_string_similarity(weather_text, advice_text, SIMILARITY_THRESHOLD)