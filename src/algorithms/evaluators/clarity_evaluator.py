"""
明確性評価モジュール

コメントの明確性と具体性を評価する
"""

import re
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class ClarityEvaluator(BaseEvaluator):
    """
    明確性を評価するクラス
    """
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.CLARITY
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: any, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """明確性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text

        score = 1.0  # 減点方式
        reasons = []

        # 曖昧な表現
        if self._has_ambiguous_expression(weather_text):
            score -= 0.3
            reasons.append("曖昧な表現あり")

        # 主語の欠如
        if not self._has_clear_subject(weather_text):
            score -= 0.2
            reasons.append("主語が不明確")

        # アドバイスの具体性
        if not self._is_advice_specific(advice_text):
            score -= 0.2
            reasons.append("アドバイスが抽象的")

        return CriterionScore(
            criterion=self.criterion,
            score=max(score, 0.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "明確な表現",
        )
    
    def _has_ambiguous_expression(self, text: str) -> bool:
        """曖昧な表現があるかチェック"""
        if "ambiguity_check" not in self.enabled_checks:
            return False
            
        if self.evaluation_mode == "relaxed":
            return False  # 緩和版では基本的にOK
        
        # strict/moderateモードでの曖昧表現チェック
        ambiguous_patterns = [
            "かもしれない",
            "と思われる",
            "のような",
            "みたいな",
            "っぽい",
            "たぶん",
            "おそらく",
        ]
        
        if self.evaluation_mode == "moderate":
            # moderateでは極端な曖昧表現のみ
            extreme_ambiguous = ["たぶん", "おそらく", "かもしれない"]
            return sum(1 for pattern in extreme_ambiguous if pattern in text) >= 2
        
        # strictモード
        return any(pattern in text for pattern in ambiguous_patterns)
    
    def _has_clear_subject(self, text: str) -> bool:
        """明確な主語があるかチェック"""
        if "subject_check" not in self.enabled_checks:
            return True
            
        if self.evaluation_mode == "relaxed":
            return True  # 緩和版では基本的にOK
        
        # 主語となりうる表現
        subjects = ["今日", "本日", "今朝", "今夜", "天気", "空", "気温", "風"]
        has_subject = any(subject in text for subject in subjects)
        
        if self.evaluation_mode == "moderate":
            # moderateでは主語がなくても許容
            return True
        
        # strictモードでは主語を推奨
        return has_subject
    
    def _is_advice_specific(self, text: str) -> bool:
        """アドバイスが具体的かチェック"""
        if "specificity_check" not in self.enabled_checks:
            return True
            
        if self.evaluation_mode == "relaxed":
            return True  # 緩和版では基本的にOK
        
        # 具体的な要素
        specific_elements = [
            # 具体的な物品
            "傘", "日傘", "帽子", "マフラー", "手袋", "サングラス", "日焼け止め",
            # 具体的な行動
            "水分補給", "休憩", "早めに", "ゆっくり", "注意して",
            # 数値
            r"\d+",  # 数字を含む
        ]
        
        has_specific = any(re.search(element, text) for element in specific_elements)
        
        if self.evaluation_mode == "moderate":
            # moderateでは具体性がなくても減点は小さい
            return has_specific or len(text) > 15
        
        # strictモードでは具体性を要求
        return has_specific