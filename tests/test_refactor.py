"""
簡単なテストスクリプト - リファクタリング後の動作確認
"""

from src.algorithms.comment_evaluator import CommentEvaluator
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from src.data.weather_data import WeatherForecast
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

from src.data.weather_data import WeatherCondition, WindDirection

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

# 評価器を作成して評価を実行
evaluator = CommentEvaluator(evaluation_mode="relaxed")
result = evaluator.evaluate_comment_pair(comment_pair, context, weather_data)

# 結果を表示
print(f"評価結果: {'合格' if result.is_valid else '不合格'}")
print(f"総合スコア: {result.total_score:.2f}")
print("\n各評価基準のスコア:")
for score in result.criterion_scores:
    print(f"  {score.criterion.value}: {score.score:.2f} (理由: {score.reason})")

print("\nリファクタリング成功！")