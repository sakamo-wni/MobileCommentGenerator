"""
evaluate_candidate_node関数のテスト

コメント候補評価ノードの機能テスト
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
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


class TestEvaluateCandidateNode:
    """EvaluateCandidateNodeのテストスイート"""

    def setup_method(self):
        """テストセットアップ"""
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
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now(),
            weather_data=self.sample_weather.to_dict(),
            selected_pair=self.sample_pair.to_dict(),
            retry_count=0,
        )

        result = evaluate_candidate_node(state)

        assert result.validation_result is not None
        assert result.validation_result.is_valid is True
        assert result.validation_result.total_score > 0.6
        assert result.retry_count == 0

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

        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now(),
            weather_data=self.sample_weather.to_dict(),
            selected_pair=bad_pair.to_dict(),
            retry_count=0,
        )

        result = evaluate_candidate_node(state)

        assert result.validation_result is not None
        assert result.validation_result.is_valid is False
        assert result.retry_count == 1
        assert "improvement_suggestions" in result.generation_metadata
        assert len(result.generation_metadata["improvement_suggestions"]) > 0

    def test_evaluate_candidate_node_no_selected_pair(self):
        """選択ペアがない場合"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now(),
            weather_data=self.sample_weather.to_dict()
        )

        result = evaluate_candidate_node(state)

        assert len(result.errors) > 0
        assert result.validation_result is not None  # エラー時でも評価結果は設定される

    def test_evaluate_candidate_node_with_custom_weights(self):
        """カスタム重みを使用した評価"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now(),
            weather_data=self.sample_weather.to_dict(),
            selected_pair=self.sample_pair.to_dict(),
            retry_count=0,
        )
        # user_preferencesはメタデータとして設定
        state.generation_metadata["user_preferences"] = {
            "evaluation_weights": {"relevance": 0.5, "creativity": 0.2, "naturalness": 0.3}
        }

        result = evaluate_candidate_node(state)

        assert result.validation_result is not None
        assert result.validation_result.is_valid is True

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])