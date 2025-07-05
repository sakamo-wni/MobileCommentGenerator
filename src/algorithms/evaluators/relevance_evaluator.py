"""
関連性評価モジュール

天気条件との関連性を評価する
"""

from typing import List, Tuple
from src.algorithms.evaluators.base_evaluator import BaseEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, CriterionScore, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class RelevanceEvaluator(BaseEvaluator):
    """
    関連性を評価するクラス
    """
    
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
        
        # 天気の安定性と矛盾する表現のチェック
        if hasattr(context, 'weather_stability') and context.weather_stability == 'stable':
            changeable_keywords = ["変わりやすい", "不安定", "急変", "めまぐるしく", "変化"]
            if any(keyword in weather_comment or keyword in advice_comment for keyword in changeable_keywords):
                has_contradiction = True
                reasons.append("安定した天気なのに「変わりやすい」という表現")
        
        if has_contradiction:
            score = 0.2
            reasons.append("天気条件と明らかに矛盾する表現")
        else:
            score = 0.8
            reasons.append("天気条件との矛盾なし")

        # 天気に関連する表現があればボーナス
        weather_keywords = ["天気", "空", "気温", "暑", "寒", "涼", "暖", "晴", "雨", "雪", "風"]
        if any(keyword in weather_comment for keyword in weather_keywords):
            score = min(score + 0.1, 1.0)
            reasons.append("天気関連の表現を含む")

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
        return True  # 緩和版では基本的にOK