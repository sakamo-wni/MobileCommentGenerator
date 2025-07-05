"""
CommentEvaluatorクラスのテスト

コメント評価エンジンの動作をテスト
"""

import pytest
from datetime import datetime

from src.data.past_comment import PastComment
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.evaluation_criteria import EvaluationCriteria, EvaluationContext
from src.algorithms.comment_evaluator import CommentEvaluator


class TestCommentEvaluator:
    """評価エンジンのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.evaluator = CommentEvaluator()
        self.sample_weather = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0,
        )
        self.context = EvaluationContext(
            weather_condition="晴れ", location="東京", target_datetime=datetime.now()
        )

    def test_evaluate_comment_pair_good(self):
        """良いコメントペアの評価"""
        good_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="爽やかな晴れの朝ですね！",
                comment_type="weather_comment",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            advice_comment=PastComment(
                comment_text="日差しが強いので帽子があると良いですよ",
                comment_type="advice",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            similarity_score=0.9,
            selection_reason="天気が一致",
        )

        result = self.evaluator.evaluate_comment_pair(good_pair, self.context, self.sample_weather)

        assert result.is_valid is True
        assert result.total_score > 0.7
        assert len(result.passed_criteria) > len(result.failed_criteria)

    def test_evaluate_comment_pair_bad(self):
        """悪いコメントペアの評価"""
        bad_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="最悪",
                comment_type="weather_comment",
                weather_condition="雨",
                temperature=10.0,
            ),
            advice_comment=PastComment(
                comment_text="もう無理",
                comment_type="advice",
                weather_condition="雨",
                temperature=10.0,
            ),
            similarity_score=0.2,
            selection_reason="",
        )

        result = self.evaluator.evaluate_comment_pair(bad_pair, self.context, self.sample_weather)

        assert result.is_valid is False
        assert result.total_score < 0.6
        assert len(result.failed_criteria) > 0
        assert len(result.suggestions) > 0

    def test_criterion_evaluation_relevance(self):
        """関連性評価のテスト"""
        pair = CommentPair(
            weather_comment=PastComment(
                comment_text="晴れて気持ちいいですね",
                comment_type="weather_comment",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            advice_comment=PastComment(
                comment_text="紫外線対策をしましょう",
                comment_type="advice",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            similarity_score=0.8,
            selection_reason="",
        )

        score = self.evaluator._evaluate_relevance(pair, self.context, self.sample_weather)

        assert score.criterion == EvaluationCriteria.RELEVANCE
        assert score.score > 0.7
        assert "天気条件" in score.reason

    def test_criterion_evaluation_appropriateness(self):
        """適切性評価のテスト"""
        # 不適切な表現を含むペア
        inappropriate_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="最悪の天気で死にそう",
                comment_type="weather_comment",
                weather_condition="雨",
                temperature=10.0,
            ),
            advice_comment=PastComment(
                comment_text="もう外出するな",
                comment_type="advice",
                weather_condition="雨",
                temperature=10.0,
            ),
            similarity_score=0.5,
            selection_reason="",
        )

        score = self.evaluator._evaluate_appropriateness(
            inappropriate_pair, self.context, self.sample_weather
        )

        assert score.criterion == EvaluationCriteria.APPROPRIATENESS
        assert score.score < 0.5
        assert "不適切" in score.reason

    def test_evaluation_with_different_weights(self):
        """異なる重みでの評価"""
        custom_weights = {
            EvaluationCriteria.RELEVANCE: 0.8,
            EvaluationCriteria.CREATIVITY: 0.1,
            EvaluationCriteria.NATURALNESS: 0.05,
            EvaluationCriteria.APPROPRIATENESS: 0.05,
            EvaluationCriteria.ENGAGEMENT: 0.0,
            EvaluationCriteria.CLARITY: 0.0,
            EvaluationCriteria.CONSISTENCY: 0.0,
            EvaluationCriteria.ORIGINALITY: 0.0,
        }

        evaluator = CommentEvaluator(weights=custom_weights)

        pair = self.sample_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="晴れですね",
                comment_type="weather_comment",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            advice_comment=PastComment(
                comment_text="いい天気を楽しみましょう",
                comment_type="advice",
                weather_condition="晴れ",
                temperature=20.0,
            ),
            similarity_score=0.7,
            selection_reason="",
        )

        result = evaluator.evaluate_comment_pair(pair, self.context, self.sample_weather)

        # 関連性の重みが高いので、関連性が高ければ合格しやすい
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])