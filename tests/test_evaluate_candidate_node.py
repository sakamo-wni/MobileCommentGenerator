"""
コメント候補評価ノードのテスト
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast
from src.data.evaluation_criteria import (
    EvaluationCriteria,
    CriterionScore,
    EvaluationResult,
    EvaluationContext,
)
from src.nodes.evaluate_candidate_node import (
    evaluate_candidate_node,
    _restore_comment_pair,
    _restore_weather_data,
    _get_custom_weights,
)
from src.algorithms.comment_evaluator import CommentEvaluator


class TestEvaluateCandidateNode:
    """EvaluateCandidateNodeのテストスイート"""

    def setup_method(self):
        """テストセットアップ"""
        self.sample_weather = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction="北",
        )

        self.sample_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="今日は爽やかな晴れの日ですね",
                comment_type="weather_comment",
                location="東京",
                weather_condition="晴れ",
                temperature=19.0,
                datetime=datetime.now(),
            ),
            advice_comment=PastComment(
                comment_text="日差しが強いので日焼け止めをお忘れなく",
                comment_type="advice",
                location="東京",
                weather_condition="晴れ",
                temperature=21.0,
                datetime=datetime.now(),
            ),
            similarity_score=0.85,
            selection_reason="天気条件が一致",
        )

    def test_evaluate_candidate_node_success(self):
        """正常系のテスト（評価合格）"""
        state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "weather_data": self.sample_weather.to_dict(),
            "selected_pair": self.sample_pair.to_dict(),
            "retry_count": 0,
        }

        result = evaluate_candidate_node(state)

        assert "validation_result" in result
        assert result["is_valid"] is True
        assert result["validation_result"]["is_valid"] is True
        assert result["validation_result"]["total_score"] > 0.6
        assert result["retry_count"] == 0

    def test_evaluate_candidate_node_failure(self):
        """評価不合格のテスト"""
        # 不適切なコメントペア
        bad_pair = CommentPair(
            weather_comment=PastComment(
                comment_text="最悪な天気",
                comment_type="weather_comment",
                location="東京",
                weather_condition="雨",
                temperature=10.0,
                datetime=datetime.now(),
            ),
            advice_comment=PastComment(
                comment_text="もう嫌になる",
                comment_type="advice",
                location="東京",
                weather_condition="雨",
                temperature=10.0,
                datetime=datetime.now(),
            ),
            similarity_score=0.3,
            selection_reason="天気条件が不一致",
        )

        state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "weather_data": self.sample_weather.to_dict(),
            "selected_pair": bad_pair.to_dict(),
            "retry_count": 0,
        }

        result = evaluate_candidate_node(state)

        assert result["is_valid"] is False
        assert result["retry_count"] == 1
        assert "improvement_suggestions" in result
        assert len(result["improvement_suggestions"]) > 0

    def test_evaluate_candidate_node_no_selected_pair(self):
        """選択ペアがない場合"""
        state = {"location_name": "東京", "weather_data": self.sample_weather.to_dict()}

        result = evaluate_candidate_node(state)

        assert "errors" in result
        assert len(result["errors"]) > 0
        assert result["is_valid"] is True  # エラー時はデフォルトで合格

    def test_evaluate_candidate_node_with_custom_weights(self):
        """カスタム重みを使用した評価"""
        state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "weather_data": self.sample_weather.to_dict(),
            "selected_pair": self.sample_pair.to_dict(),
            "user_preferences": {
                "evaluation_weights": {"relevance": 0.5, "creativity": 0.2, "naturalness": 0.3}
            },
        }

        result = evaluate_candidate_node(state)

        assert "validation_result" in result
        assert result["is_valid"] is True

    def test_restore_comment_pair(self):
        """CommentPair復元のテスト"""
        pair_dict = self.sample_pair.to_dict()
        restored = _restore_comment_pair(pair_dict)

        assert isinstance(restored, CommentPair)
        assert (
            restored.weather_comment.comment_text == self.sample_pair.weather_comment.comment_text
        )
        assert restored.advice_comment.comment_text == self.sample_pair.advice_comment.comment_text
        assert restored.similarity_score == self.sample_pair.similarity_score

    def test_restore_weather_data(self):
        """WeatherForecast復元のテスト"""
        weather_dict = self.sample_weather.to_dict()
        restored = _restore_weather_data(weather_dict)

        assert isinstance(restored, WeatherForecast)
        assert restored.location == self.sample_weather.location
        assert restored.temperature == self.sample_weather.temperature
        assert restored.weather_description == self.sample_weather.weather_description

    def test_get_custom_weights(self):
        """カスタム重み取得のテスト"""
        # 有効な重み設定
        preferences = {"evaluation_weights": {"relevance": 0.5, "creativity": 0.2}}
        weights = _get_custom_weights(preferences)

        assert weights is not None
        assert EvaluationCriteria.RELEVANCE in weights
        assert weights[EvaluationCriteria.RELEVANCE] == 0.5

        # 無効な設定
        invalid_preferences = {"evaluation_weights": {"invalid_criterion": 0.5}}
        weights = _get_custom_weights(invalid_preferences)
        assert weights is None


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
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction="北",
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


class TestEvaluationCriteria:
    """評価基準データクラスのテスト"""

    def test_criterion_score(self):
        """CriterionScoreのテスト"""
        score = CriterionScore(
            criterion=EvaluationCriteria.RELEVANCE, score=0.8, weight=0.25, reason="天気条件が一致"
        )

        assert score.weighted_score == 0.2  # 0.8 * 0.25

        # 無効なスコア
        with pytest.raises(ValueError):
            CriterionScore(criterion=EvaluationCriteria.RELEVANCE, score=1.5, weight=0.25)  # 無効

    def test_evaluation_result(self):
        """EvaluationResultのテスト"""
        scores = [
            CriterionScore(EvaluationCriteria.RELEVANCE, 0.8, 0.25),
            CriterionScore(EvaluationCriteria.NATURALNESS, 0.9, 0.20),
            CriterionScore(EvaluationCriteria.APPROPRIATENESS, 0.5, 0.20),
        ]

        result = EvaluationResult(is_valid=True, total_score=0.75, criterion_scores=scores)

        assert result.average_score == pytest.approx(0.733, 0.01)
        assert result.pass_rate == pytest.approx(0.667, 0.01)
        assert len(result.passed_criteria) == 2
        assert len(result.failed_criteria) == 1

    def test_evaluation_context(self):
        """EvaluationContextのテスト"""
        context = EvaluationContext(
            weather_condition="晴れ",
            location="東京",
            target_datetime=datetime.now(),
            user_preferences={"style": "casual"},
        )

        assert context.get_preference("style") == "casual"
        assert context.get_preference("missing", "default") == "default"

        # 履歴追加
        context.add_history({"score": 0.8})
        assert len(context.history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
