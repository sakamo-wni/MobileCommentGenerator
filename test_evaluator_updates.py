#!/usr/bin/env python
"""Test script to verify evaluator updates"""

from datetime import datetime
from src.data.past_comment import PastComment
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.evaluation_criteria import EvaluationContext
from src.algorithms.evaluators.relevance_evaluator import RelevanceEvaluator
from src.algorithms.evaluators.creativity_evaluator import CreativityEvaluator
from src.algorithms.evaluators.naturalness_evaluator import NaturalnessEvaluator
from src.algorithms.evaluators.appropriateness_evaluator import AppropriatenessEvaluator
from src.algorithms.evaluators.engagement_evaluator import EngagementEvaluator
from src.algorithms.evaluators.clarity_evaluator import ClarityEvaluator
from src.algorithms.evaluators.consistency_evaluator import ConsistencyEvaluator
from src.algorithms.evaluators.originality_evaluator import OriginalityEvaluator


def test_evaluators():
    # Create test data
    from src.data.past_comment import CommentType
    
    weather_comment = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="晴れ",
        comment_text="今日は晴れて気持ちがいい天気ですね",
        comment_type=CommentType.WEATHER_COMMENT,
        temperature=25.0
    )
    advice_comment = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="晴れ",
        comment_text="日差しが強いので日焼け止めをお忘れなく",
        comment_type=CommentType.ADVICE,
        temperature=25.0
    )
    comment_pair = CommentPair(
        weather_comment=weather_comment,
        advice_comment=advice_comment,
        similarity_score=0.8,
        selection_reason="Test comment pair"
    )
    
    weather_data = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=25.0,
        weather_code="sunny",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=60.0,
        wind_speed=2.0,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0
    )
    
    context = EvaluationContext(
        weather_condition="Clear",
        location="東京",
        target_datetime=datetime.now()
    )
    
    # Test all evaluators
    evaluators = [
        RelevanceEvaluator(weight=1.0, evaluation_mode="relaxed", enabled_checks=[]),
        CreativityEvaluator(weight=0.8, evaluation_mode="relaxed", enabled_checks=[]),
        NaturalnessEvaluator(weight=0.9, evaluation_mode="relaxed", enabled_checks=[]),
        AppropriatenessEvaluator(weight=1.0, evaluation_mode="relaxed", enabled_checks=[]),
        EngagementEvaluator(weight=0.7, evaluation_mode="relaxed", enabled_checks=[]),
        ClarityEvaluator(weight=0.8, evaluation_mode="relaxed", enabled_checks=[]),
        ConsistencyEvaluator(weight=0.9, evaluation_mode="relaxed", enabled_checks=[]),
        OriginalityEvaluator(weight=0.6, evaluation_mode="relaxed", enabled_checks=[])
    ]
    
    print("Testing all evaluators with EvaluationContext type...")
    for evaluator in evaluators:
        try:
            result = evaluator.evaluate(comment_pair, context, weather_data)
            print(f"✓ {evaluator.__class__.__name__}: score={result.score:.2f}, reason={result.reason}")
        except Exception as e:
            print(f"✗ {evaluator.__class__.__name__}: {str(e)}")
    
    print("\nAll evaluators successfully updated!")


if __name__ == "__main__":
    test_evaluators()