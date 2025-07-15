"""
一貫性評価モジュール

コメント間の一貫性と整合性を評価する
"""

from typing import Any
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class ConsistencyEvaluator(BaseEvaluator):
    """
    一貫性を評価するクラス
    """
    
    def __init__(self, weight: float, evaluation_mode: str = "relaxed", 
                 enabled_checks: list[str] = None, contradiction_patterns: list[dict[str, List[str]]] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            evaluation_mode: 評価モード
            enabled_checks: 有効化するチェック項目
            contradiction_patterns: 矛盾パターンのリスト
        """
        # EvaluatorConfigを作成してBaseEvaluatorに渡す
        from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
        config = EvaluatorConfig(
            evaluation_mode=evaluation_mode,
            enabled_checks=enabled_checks or [],
            contradiction_patterns=contradiction_patterns or []
        )
        super().__init__(weight, config)
        self.contradiction_patterns = contradiction_patterns or []
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.CONSISTENCY
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """一貫性を評価（緩和版）- 重複・矛盾チェックに重点"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text

        score = 1.0
        reasons = []

        # 重複コンテンツのチェック（最重要）
        if self._has_significant_overlap(weather_text, advice_text):
            score -= 0.6
            reasons.append("コメントとアドバイスで同じ内容を繰り返している")

        # 明らかな矛盾のチェック
        if self._has_obvious_contradiction(weather_text, advice_text):
            score -= 0.5
            reasons.append("内容に明らかな矛盾がある")

        # トーンの不一致は軽微な減点のみ
        if not self._has_consistent_tone(weather_text, advice_text):
            score -= 0.1
            reasons.append("トーンがやや不一致")

        return CriterionScore(
            criterion=self.criterion,
            score=max(score, 0.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "一貫性あり",
        )
    
    def _has_significant_overlap(self, text1: str, text2: str) -> bool:
        """重複コンテンツの有無をチェック"""
        # 文字数が短い場合は重複を許可
        if len(text1) < 5 or len(text2) < 5:
            return False
            
        # 完全一致または大部分の重複をチェック
        if text1 == text2:
            return True
            
        # 長い共通部分文字列をチェック
        words1 = set(text1.replace('、', '').replace('。', '').split())
        words2 = set(text2.replace('、', '').replace('。', '').split())
        
        if len(words1) > 0 and len(words2) > 0:
            overlap_ratio = len(words1 & words2) / min(len(words1), len(words2))
            return overlap_ratio > 0.8
        
        return False
    
    def _has_obvious_contradiction(self, text1: str, text2: str) -> bool:
        """明らかな矛盾の有無をチェック"""
        # 設定から矛盾パターンを使用
        if not self.contradiction_patterns:
            return False
            
        for pattern in self.contradiction_patterns:
            positive_words = pattern.get("positive", [])
            negative_words = pattern.get("negative", [])
            has_positive = any(word in text1 or word in text2 for word in positive_words)
            has_negative = any(word in text1 or word in text2 for word in negative_words)
            if has_positive and has_negative:
                return True
        
        return False
    
    def _has_consistent_tone(self, text1: str, text2: str) -> bool:
        """一貫したトーンかチェック"""
        if "tone_consistency_check" not in self.enabled_checks:
            return True
            
        if self.evaluation_mode == "relaxed":
            return True  # 緩和版では基本的にOK
        
        # トーン要素の抽出
        casual_endings = ["ね", "よ", "かな", "でしょ"]
        formal_endings = ["ます", "です", "ございます"]
        
        text1_casual = any(text1.endswith(ending) or text1.endswith(ending + "。") for ending in casual_endings)
        text1_formal = any(text1.endswith(ending) or text1.endswith(ending + "。") for ending in formal_endings)
        text2_casual = any(text2.endswith(ending) or text2.endswith(ending + "。") for ending in casual_endings)
        text2_formal = any(text2.endswith(ending) or text2.endswith(ending + "。") for ending in formal_endings)
        
        if self.evaluation_mode == "moderate":
            # moderateでは極端な不一致のみ問題視
            return not (text1_casual and text2_formal) and not (text1_formal and text2_casual)
        
        # strictモードでは一貫性を厳密にチェック
        return (text1_casual == text2_casual) and (text1_formal == text2_formal)