"""
評価基準データクラスのテスト

評価基準関連のデータ構造をテスト
"""

import pytest
from datetime import datetime

from src.data.evaluation_criteria import (
    EvaluationCriteria,
    CriterionScore,
    EvaluationResult,
    EvaluationContext,
)


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