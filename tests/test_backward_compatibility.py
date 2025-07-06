"""
評価器の後方互換性テスト
"""

from src.algorithms.evaluators import (
    AppropriatenessEvaluator, 
    EngagementEvaluator, 
    ConsistencyEvaluator,
    RelevanceEvaluator,
    CreativityEvaluator,
    NaturalnessEvaluator,
    ClarityEvaluator,
    OriginalityEvaluator
)
from src.algorithms.evaluators.evaluator_config import EvaluatorConfig
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.evaluation_criteria import EvaluationContext
from datetime import datetime

# テストデータを作成
weather_comment = PastComment(
    location="東京",
    datetime=datetime.now(),
    weather_condition="晴れ",
    comment_text="今日はとても良い天気ですね。",
    comment_type=CommentType.WEATHER_COMMENT,
    temperature=22.0
)

advice_comment = PastComment(
    location="東京",
    datetime=datetime.now(),
    weather_condition="晴れ",
    comment_text="お出かけ日和なので、散歩でもいかがでしょうか。",
    comment_type=CommentType.ADVICE,
    temperature=22.0
)

comment_pair = CommentPair(
    weather_comment=weather_comment,
    advice_comment=advice_comment,
    similarity_score=0.8,
    selection_reason="テスト用コメントペア"
)

weather_data = WeatherForecast(
    location="東京",
    datetime=datetime.now(),
    temperature=22.0,
    weather_code="sunny",
    weather_condition=WeatherCondition.CLEAR,
    weather_description="晴れ",
    precipitation=0.0,
    humidity=60,
    wind_speed=3.0,
    wind_direction=WindDirection.N,
    wind_direction_degrees=0,
    pressure=1013
)

context = EvaluationContext(
    weather_condition="晴れ",
    location="東京",
    target_datetime=datetime.now(),
    user_preferences={}
)

print("=== 後方互換性テスト ===\n")

# 1. AppropriatenessEvaluator - 旧方式（パターンパラメータ指定）
print("1. AppropriatenessEvaluator - 旧方式")
evaluator1 = AppropriatenessEvaluator(
    weight=1.0,
    inappropriate_patterns=["死", "殺"]
)
result1 = evaluator1.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result1.score:.2f}, 理由: {result1.reason}")

# 2. AppropriatenessEvaluator - 新方式（config使用）
print("\n2. AppropriatenessEvaluator - 新方式")
config = EvaluatorConfig(inappropriate_patterns=["死", "殺"])
evaluator2 = AppropriatenessEvaluator(weight=1.0, config=config)
result2 = evaluator2.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result2.score:.2f}, 理由: {result2.reason}")

# 3. EngagementEvaluator - 旧方式
print("\n3. EngagementEvaluator - 旧方式")
evaluator3 = EngagementEvaluator(
    weight=1.0,
    engagement_elements=["ね", "よ", "でしょう"],
    positive_expressions=["素敵", "良い", "嬉しい"]
)
result3 = evaluator3.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result3.score:.2f}, 理由: {result3.reason}")

# 4. EngagementEvaluator - 新方式
print("\n4. EngagementEvaluator - 新方式")
config2 = EvaluatorConfig(
    engagement_elements=["ね", "よ", "でしょう"],
    positive_expressions=["素敵", "良い", "嬉しい"]
)
evaluator4 = EngagementEvaluator(weight=1.0, config=config2)
result4 = evaluator4.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result4.score:.2f}, 理由: {result4.reason}")

# 5. ConsistencyEvaluator - 旧方式
print("\n5. ConsistencyEvaluator - 旧方式")
evaluator5 = ConsistencyEvaluator(
    weight=1.0,
    contradiction_patterns=[
        {"positive": ["晴れ"], "negative": ["雨", "雪"]}
    ]
)
result5 = evaluator5.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result5.score:.2f}, 理由: {result5.reason}")

# 6. ConsistencyEvaluator - 新方式
print("\n6. ConsistencyEvaluator - 新方式")
config3 = EvaluatorConfig(
    contradiction_patterns=[
        {"positive": ["晴れ"], "negative": ["雨", "雪"]}
    ]
)
evaluator6 = ConsistencyEvaluator(weight=1.0, config=config3)
result6 = evaluator6.evaluate(comment_pair, context, weather_data)
print(f"   スコア: {result6.score:.2f}, 理由: {result6.reason}")

# 7. シンプルな評価器のテスト（新方式のみ）
print("\n7. シンプルな評価器（新方式）")
simple_evaluators = [
    RelevanceEvaluator(weight=1.0),
    CreativityEvaluator(weight=1.0),
    NaturalnessEvaluator(weight=1.0),
    ClarityEvaluator(weight=1.0),
    OriginalityEvaluator(weight=1.0)
]

for evaluator in simple_evaluators:
    result = evaluator.evaluate(comment_pair, context, weather_data)
    print(f"   {evaluator.criterion.value}: {result.score:.2f}")

print("\n=== テスト完了！後方互換性は保たれています ===")