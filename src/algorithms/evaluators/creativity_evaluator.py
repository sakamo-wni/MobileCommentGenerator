"""
創造性評価モジュール

コメントの創造性と独創性を評価する
"""

from typing import Optional
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class CreativityEvaluator(BaseEvaluator):
    """
    創造性を評価するクラス
    """
    
    def __init__(self, weight: float, config: Optional[EvaluatorConfig] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            config: 評価器の設定
        """
        super().__init__(weight, config)
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.CREATIVITY
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """創造性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text

        score = 0.0
        reasons = []

        # 比喩や擬人化の使用
        if self._has_metaphor(weather_text):
            score += 0.3
            reasons.append("比喩表現を使用")

        # 独創的な表現
        if self._is_unique_expression(weather_text):
            score += 0.3
            reasons.append("独創的な表現")

        # 感情的な要素
        if self._has_emotional_element(weather_text):
            score += 0.2
            reasons.append("感情を込めた表現")

        # 予想外のアドバイス
        if self._is_creative_advice(advice_text):
            score += 0.2
            reasons.append("創造的なアドバイス")

        return CriterionScore(
            criterion=self.criterion,
            score=min(score, 1.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "標準的な表現",
        )
    
    def _has_metaphor(self, text: str) -> bool:
        """比喩表現を含むかチェック"""
        metaphor_patterns = ["ような", "みたい", "らしい", "のよう"]
        return any(pattern in text for pattern in metaphor_patterns)
    
    def _is_unique_expression(self, text: str) -> bool:
        """独創的な表現かチェック"""
        common_phrases = ["いい天気", "雨ですね", "寒いです", "暑いです"]
        return not any(phrase in text for phrase in common_phrases)
    
    def _has_emotional_element(self, text: str) -> bool:
        """感情的な要素を含むかチェック"""
        emotional_words = ["嬉しい", "楽しい", "気持ちいい", "爽やか", "素敵"]
        return any(word in text for word in emotional_words)
    
    def _is_creative_advice(self, text: str) -> bool:
        """創造的なアドバイスかチェック"""
        common_advice = ["気をつけて", "ご注意", "お忘れなく"]
        creative_elements = ["おすすめ", "楽しんで", "素敵な", "ぜひ"]
        
        if any(advice in text for advice in common_advice):
            return any(elem in text for elem in creative_elements)
        return True