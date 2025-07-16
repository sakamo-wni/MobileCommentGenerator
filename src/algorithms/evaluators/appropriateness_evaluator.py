"""
適切性評価モジュール

コメントの社会的・倫理的な適切性を評価する
"""

from __future__ import annotations
import re
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class AppropriatenessEvaluator(BaseEvaluator):
    """
    適切性を評価するクラス
    """
    
    def __init__(self, weight: float, evaluation_mode: str = "relaxed", 
                 enabled_checks: list[str] = None, inappropriate_patterns: list[str] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            evaluation_mode: 評価モード
            enabled_checks: 有効化するチェック項目
            inappropriate_patterns: 不適切なパターンのリスト
        """
        # EvaluatorConfigを作成してBaseEvaluatorに渡す
        from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
        config = EvaluatorConfig(
            evaluation_mode=evaluation_mode,
            enabled_checks=enabled_checks or [],
            inappropriate_patterns=inappropriate_patterns or []
        )
        super().__init__(weight, config)
        self.inappropriate_patterns = inappropriate_patterns or []
        if self.inappropriate_patterns:
            self.inappropriate_regex = re.compile("|".join(self.inappropriate_patterns), re.IGNORECASE)
        else:
            self.inappropriate_regex = re.compile(r"(?!.*)", re.IGNORECASE)  # 何もマッチしない
    
    @property
    def criterion(self) -> EvaluationCriteria:
        return EvaluationCriteria.APPROPRIATENESS
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """適切性を評価（緩和版）- 極端に不適切な表現のみ不合格"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text

        score = 1.0  # 基本的に適切とみなす
        reasons = []

        # 極端に不適切な表現のみチェック（非常に厳しい基準）
        extreme_inappropriate = [
            r"死|殺|自殺|地獄|絶望|最悪.*死",
            r"危険.*死|警告.*死|やばい.*死",
        ]
        
        for pattern in extreme_inappropriate:
            if re.search(pattern, weather_text) or re.search(pattern, advice_text):
                score = 0.2
                reasons.append("極端に不適切な表現を含む")
                break
        
        # 過度に攻撃的・侮辱的な表現
        offensive_patterns = [
            r"バカ|アホ|クソ|ムカつく|うざい|きもい",
        ]
        
        for pattern in offensive_patterns:
            if re.search(pattern, weather_text) or re.search(pattern, advice_text):
                score = min(score - 0.3, 0.8)
                reasons.append("攻撃的な表現を含む")
                break

        if score == 1.0:
            reasons.append("適切な内容")

        return CriterionScore(
            criterion=self.criterion,
            score=max(score, 0.0),
            weight=self.weight,
            reason="、".join(reasons) if reasons else "適切な内容",
        )
    
    def is_too_negative(self, text: str) -> bool:
        """過度にネガティブかチェック（緩和版）"""
        # 極端にネガティブな表現のみ対象
        extreme_negative = ["死にそう", "地獄", "絶望", "最悪.*死", "殺"]
        return any(re.search(pattern, text) for pattern in extreme_negative)
    
    def is_advice_appropriate(self, text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスが状況に適切かチェック"""
        if self.evaluation_mode == "relaxed":
            # 緩和モードでは極端な不適切さのみチェック
            weather_desc = self.safe_get_weather_desc(weather_data)
            if weather_desc:
                # 晴れの日に「傘を忘れずに」など明らかに不適切な場合のみ
                if "晴" in weather_desc and "傘" in text:
                    return False
                if "雨" in weather_desc and "日焼け止め" in text:
                    return False
            return True
        
        # strict/moderateモードではより詳細にチェック
        weather_desc = self.safe_get_weather_desc(weather_data)
        temp = self.safe_get_temperature(weather_data)
        if weather_desc and temp is not None:
            
            # 天気に応じたアドバイスの適切性
            if "雨" in weather_desc and not any(word in text for word in ["傘", "濡れ", "雨具"]):
                return False
            if temp > 30 and not any(word in text for word in ["暑", "水分", "熱中症", "日差し"]):
                return False
            if temp < 5 and not any(word in text for word in ["寒", "防寒", "暖か"]):
                return False
                
        return True