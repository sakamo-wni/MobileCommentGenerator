"""
オリジナリティ評価モジュール

コメントの独自性と新規性を評価する
"""

from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class OriginalityEvaluator(BaseEvaluator):
    """
    オリジナリティを評価するクラス
    """
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.ORIGINALITY
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: any, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """オリジナリティを評価"""
        weather_text = comment_pair.weather_comment.comment_text

        # 簡易的な実装（実際は過去データとの比較が必要）
        common_phrases = ["いい天気", "雨ですね", "寒いです", "暑いです"]

        score = 0.8  # ベーススコア
        if any(phrase in weather_text for phrase in common_phrases):
            score = 0.3
            reason = "一般的な表現"
        else:
            reason = "独自性のある表現"

        return CriterionScore(
            criterion=self.criterion,
            score=score,
            weight=self.weight,
            reason=reason,
        )