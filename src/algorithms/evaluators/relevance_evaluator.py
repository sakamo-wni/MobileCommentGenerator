"""
関連性評価モジュール

天気条件との関連性を評価する
"""

from typing import List, Tuple, Optional
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class RelevanceEvaluator(BaseEvaluator):
    """
    関連性を評価するクラス
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
        return EvaluationCriteria.RELEVANCE
    
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """関連性を評価（緩和版）- 基本的な妥当性のみチェック"""
        score = 0.5  # ベーススコア（中立）
        reasons = []

        weather_comment = comment_pair.weather_comment.comment_text
        advice_comment = comment_pair.advice_comment.comment_text
        weather_desc = self.safe_get_weather_desc(weather_data)

        # 明らかに矛盾する天気表現のチェック
        weather_contradictions = [
            ("晴れ", ["雨", "雪", "嵐"]),
            ("雨", ["晴れ", "快晴"]), 
            ("雪", ["暑い", "蒸し暑い"]),
            ("暑い", ["雪", "寒い"]),
        ]
        
        has_contradiction = False
        for weather_type, contradictions in weather_contradictions:
            if weather_type in weather_desc.lower():
                for contradiction in contradictions:
                    if contradiction in weather_comment or contradiction in advice_comment:
                        has_contradiction = True
                        break
        
        if has_contradiction:
            score = 0.2
            reasons.append("天気条件と明らかに矛盾する表現")
        else:
            score = 0.8
            reasons.append("天気条件との矛盾なし")

        # 天気に関連する表現があればボーナス
        if self.is_weather_related(weather_comment, weather_desc):
            score = min(score + 0.1, 1.0)
            reasons.append("天気関連の表現を含む")
        
        # 気温関連のチェック
        temp = self.safe_get_temperature(weather_data)
        if temp is not None and self.is_temperature_relevant(weather_comment, temp):
            score = min(score + 0.05, 1.0)
            reasons.append("気温に適した表現")
        
        # 時間帯関連のチェック
        hour = context.target_datetime.hour
        if self.is_time_relevant(weather_comment, hour):
            score = min(score + 0.05, 1.0)
            reasons.append("時間帯に適した表現")

        return CriterionScore(
            criterion=self.criterion,
            score=score,
            weight=self.weight,
            reason="、".join(reasons) if reasons else "基本的な関連性あり",
        )
    
    def is_weather_related(self, text: str, weather_desc: str) -> bool:
        """天気関連かチェック"""
        weather_keywords = ["天気", "空", "雲", "晴", "雨", "雪"]
        return any(keyword in text for keyword in weather_keywords)
    
    def is_temperature_relevant(self, text: str, temp: float) -> bool:
        """気温に関連するかチェック"""
        if temp >= 28:
            hot_words = ["暑", "熱", "汗", "蒸し"]
            return any(word in text for word in hot_words)
        elif temp <= 10:
            cold_words = ["寒", "冷", "凍"]
            return any(word in text for word in cold_words)
        return True
    
    def is_time_relevant(self, text: str, hour: int) -> bool:
        """時間帯に関連するかチェック"""
        if 5 <= hour <= 11:
            morning_words = ["朝", "午前", "モーニング"]
            return any(word in text for word in morning_words) or True
        elif 18 <= hour <= 23:
            evening_words = ["夕", "夜", "イブニング"]
            return any(word in text for word in evening_words) or True
        return True
    
    def is_advice_relevant(self, text: str, weather_desc: str, temp: float) -> bool:
        """アドバイスが関連するかチェック"""
        # 天気に応じた基本的なアドバイスの妥当性チェック
        if "雨" in weather_desc and any(word in text for word in ["傘", "雨具", "濡れ"]):
            return True
        if "晴" in weather_desc and any(word in text for word in ["日差し", "紫外線", "日焼け"]):
            return True
        if temp and temp > 28 and any(word in text for word in ["水分", "熱中症", "涼し"]):
            return True
        if temp and temp < 10 and any(word in text for word in ["防寒", "暖か", "寒さ対策"]):
            return True
        return True  # その他の場合も基本的にOK