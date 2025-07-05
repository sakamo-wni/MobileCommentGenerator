"""
エンゲージメント評価モジュール

ユーザーとのエンゲージメントを促進する要素を評価する
"""

import re
from typing import List
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class EngagementEvaluator(BaseEvaluator):
    """
    エンゲージメントを評価するクラス
    """
    
    def __init__(self, weight: float, evaluation_mode: str = "relaxed", 
                 enabled_checks: List[str] = None, engagement_elements: List[str] = None,
                 positive_expressions: List[str] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            evaluation_mode: 評価モード
            enabled_checks: 有効化するチェック項目
            engagement_elements: エンゲージメント要素のリスト
            positive_expressions: ポジティブな表現のリスト
        """
        super().__init__(weight, evaluation_mode, enabled_checks)
        self.engagement_elements = engagement_elements or []
        self.positive_expressions = positive_expressions or []
        
        if self.engagement_elements:
            self.engagement_regex = re.compile("|".join(self.engagement_elements))
        else:
            self.engagement_regex = re.compile(r"(?!.*)")  # 何もマッチしない
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.ENGAGEMENT
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: any, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """エンゲージメントを評価"""
        weather_text = comment_pair.weather_comment.comment_text

        score = 0.0
        reasons = []

        # エンゲージメント要素の存在
        if self.engagement_regex.search(weather_text):
            score += 0.3
            reasons.append("親しみやすい表現要素")

        # ポジティブな表現
        positive_count = sum(1 for expr in self.positive_expressions if expr in weather_text)
        if positive_count > 0:
            score += min(0.3 * positive_count, 0.4)
            reasons.append("ポジティブな表現を使用")

        # 共感を誘う表現
        if self._has_empathy_element(weather_text):
            score += 0.3
            reasons.append("共感を誘う表現")

        return CriterionScore(
            criterion=self.criterion,
            score=min(score, 1.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "標準的なエンゲージメント",
        )
    
    def _has_empathy_element(self, text: str) -> bool:
        """共感要素を含むかチェック"""
        empathy_patterns = ["ですね", "でしょう", "ますよね"]
        return any(pattern in text for pattern in empathy_patterns)