"""
自然さ評価モジュール

コメントの文法的・言語的な自然さを評価する
"""

import re
from typing import Optional
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class NaturalnessEvaluator(BaseEvaluator):
    """
    自然さを評価するクラス
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
        return EvaluationCriteria.NATURALNESS
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """自然さを評価"""
        weather_text = comment_pair.weather_comment.comment_text

        score = 1.0  # 減点方式
        reasons = []

        # 文法的な違和感
        if self._has_grammatical_issues(weather_text):
            score -= 0.3
            reasons.append("文法的な違和感あり")

        # 不自然な敬語
        if self._has_unnatural_honorifics(weather_text):
            score -= 0.2
            reasons.append("敬語が不自然")

        # 口語的すぎる/堅すぎる
        tone_score = self._evaluate_tone_balance(weather_text)
        if tone_score < 0.5:
            score -= 0.2
            reasons.append("トーンバランスが不適切")

        # 文の長さ
        if len(weather_text) > 50 or len(weather_text) < 5:
            score -= 0.1
            reasons.append("文の長さが不適切")

        return CriterionScore(
            criterion=self.criterion,
            score=max(score, 0.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "自然な表現",
        )
    
    def _has_grammatical_issues(self, text: str) -> bool:
        """文法的な問題があるかチェック"""
        if "grammar_check" not in self.enabled_checks:
            return False
            
        # 極端な文法エラーのみチェック
        extreme_patterns = [
            r"。。",  # 二重句点
            r"、、",  # 二重読点
            r"[ぁぃぅぇぉゃゅょゎ]{2,}",  # 小文字連続
            r"っっ",  # 促音連続
        ]
        
        for pattern in extreme_patterns:
            if re.search(pattern, text):
                return True
        
        # strictモードの場合は追加チェック
        if self.evaluation_mode == "strict" and "basic_grammar_check" in self.enabled_checks:
            # より詳細な文法チェック
            if re.search(r"[。、]$", text):  # 文末が句読点
                return True
                
        return False
    
    def _has_unnatural_honorifics(self, text: str) -> bool:
        """不自然な敬語があるかチェック"""
        if "honorific_check" not in self.enabled_checks:
            return False
            
        # 極端に不自然な敬語のみチェック
        extreme_patterns = [
            r"お.*お",  # 二重敬語
            r"させていただきます.*させていただきます",  # 過剰な敬語
            r"申し上げます.*申し上げます",  # 重複
        ]
        
        for pattern in extreme_patterns:
            if re.search(pattern, text):
                return True
                
        return False
    
    def _evaluate_tone_balance(self, text: str) -> float:
        """トーンのバランスを評価"""
        if self.evaluation_mode == "relaxed":
            return 0.8  # 緩和版では基本的に良好
        elif self.evaluation_mode == "moderate":
            # 極端にカジュアルまたはフォーマルな場合のみ減点
            extreme_casual = ["っす", "ヤバい", "マジで", "めっちゃ"]
            extreme_formal = ["申し上げます", "恐れ入りますが", "拝啓"]
            
            if any(word in text for word in extreme_casual):
                return 0.5
            if any(word in text for word in extreme_formal):
                return 0.5
            return 0.8
        else:  # strict
            # より詳細なトーンバランスチェック
            casual_count = sum(1 for word in ["ね", "よ", "でしょ", "かな"] if word in text)
            formal_count = sum(1 for word in ["ます", "です", "ございます"] if word in text)
            
            # バランスを評価
            if casual_count > 3 or formal_count > 5:
                return 0.4
            if abs(casual_count - formal_count) > 2:
                return 0.6
            return 0.9