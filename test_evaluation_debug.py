#!/usr/bin/env python3
"""
評価システムのデバッグ用テストスクリプト
実際のスコア計算を詳細に確認する
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.algorithms.comment_evaluator import CommentEvaluator
from src.data.evaluation_criteria import EvaluationCriteria, EvaluationContext
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast


def create_sample_weather() -> WeatherForecast:
    """サンプル天気データを作成"""
    return WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=20.0,
        weather_description="晴れ",
        weather_condition="晴れ",
        humidity=60.0,
        precipitation=0.0,
        wind_speed=3.0,
        wind_direction="北",
        wind_direction_degrees=0.0,
        weather_code="100"
    )


def create_good_comment_pair() -> CommentPair:
    """良いコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="爽やかな晴れの朝ですね！",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="日差しが強いので帽子があると良いですよ",
            comment_type=CommentType.ADVICE,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        similarity_score=0.9,
        selection_reason="天気が一致",
    )


def create_bad_comment_pair() -> CommentPair:
    """悪いコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="最悪の天気で死にそう",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="雨",
            temperature=10.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="もう外出するな",
            comment_type=CommentType.ADVICE,
            weather_condition="雨",
            temperature=10.0,
        ),
        similarity_score=0.2,
        selection_reason="",
    )


def create_typical_comment_pair() -> CommentPair:
    """よくある平凡なコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="いい天気ですね",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="気をつけてください",
            comment_type=CommentType.ADVICE,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        similarity_score=0.7,
        selection_reason="一般的な表現",
    )


def create_contradictory_comment_pair() -> CommentPair:
    """天気と矛盾するコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="晴れて気持ちがいいですね",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="雨",  # 矛盾: 雨なのに晴れのコメント
            temperature=20.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="傘を忘れずに",
            comment_type=CommentType.ADVICE,
            weather_condition="雨",
            temperature=20.0,
        ),
        similarity_score=0.5,
        selection_reason="天気が矛盾",
    )


def create_duplicate_comment_pair() -> CommentPair:
    """重複するコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="暑いので水分補給を",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="晴れ",
            temperature=30.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="暑いので水分補給を忘れずに",  # ほぼ同じ内容
            comment_type=CommentType.ADVICE,
            weather_condition="晴れ",
            temperature=30.0,
        ),
        similarity_score=0.3,
        selection_reason="重複コンテンツ",
    )


def create_extremely_inappropriate_comment_pair() -> CommentPair:
    """極端に不適切なコメントペアを作成"""
    from src.data.past_comment import CommentType
    return CommentPair(
        weather_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="バカみたいな天気で死にたい",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        advice_comment=PastComment(
            location="東京",
            datetime=datetime.now(),
            comment_text="クソったれな外出なんかするな",
            comment_type=CommentType.ADVICE,
            weather_condition="晴れ",
            temperature=20.0,
        ),
        similarity_score=0.1,
        selection_reason="極端に不適切",
    )


def detailed_test_evaluation_system():
    """評価システムをテスト"""
    print("=" * 60)
    print("評価システムの詳細テスト")
    print("=" * 60)
    
    # テストデータ準備
    evaluator = CommentEvaluator()
    weather_data = create_sample_weather()
    context = EvaluationContext(
        weather_condition="晴れ",
        location="東京", 
        target_datetime=datetime.now()
    )
    
    print(f"デフォルト評価重み:")
    for criterion, weight in evaluator.weights.items():
        print(f"  {criterion.value}: {weight}")
    print()
    
    # テストケース1: 良いコメント
    print("【テストケース1: 良いコメント】")
    good_pair = create_good_comment_pair()
    print(f"天気コメント: '{good_pair.weather_comment.comment_text}'")
    print(f"アドバイス: '{good_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(good_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    print()
    
    # テストケース2: 悪いコメント
    print("【テストケース2: 悪いコメント】")
    bad_pair = create_bad_comment_pair()
    print(f"天気コメント: '{bad_pair.weather_comment.comment_text}'")
    print(f"アドバイス: '{bad_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(bad_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    if result.suggestions:
        print("改善提案:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")
    print()
    
    # テストケース3: 平凡なコメント
    print("【テストケース3: 平凡なコメント】")
    typical_pair = create_typical_comment_pair()
    print(f"天気コメント: '{typical_pair.weather_comment.comment_text}'")
    print(f"アドバイス: '{typical_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(typical_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    print()
    
    # テストケース4: 天気矛盾コメント
    print("【テストケース4: 天気矛盾コメント】")
    contradictory_pair = create_contradictory_comment_pair()
    print(f"天気コメント: '{contradictory_pair.weather_comment.comment_text}' (実際の天気: 雨)")
    print(f"アドバイス: '{contradictory_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(contradictory_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    print()
    
    # テストケース5: 重複コメント
    print("【テストケース5: 重複コメント】")
    duplicate_pair = create_duplicate_comment_pair()
    print(f"天気コメント: '{duplicate_pair.weather_comment.comment_text}'")
    print(f"アドバイス: '{duplicate_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(duplicate_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    print()
    
    # テストケース6: 極端に不適切なコメント
    print("【テストケース6: 極端に不適切なコメント】")
    extreme_pair = create_extremely_inappropriate_comment_pair()
    print(f"天気コメント: '{extreme_pair.weather_comment.comment_text}'")
    print(f"アドバイス: '{extreme_pair.advice_comment.comment_text}'")
    
    result = evaluator.evaluate_comment_pair(extreme_pair, context, weather_data)
    print(f"総合スコア: {result.total_score:.3f}")
    print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
    print("詳細スコア:")
    for score in result.criterion_scores:
        print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
        if score.reason:
            print(f"    理由: {score.reason}")
    print()


def test_evaluation_system():
    """評価システムをテスト"""
    print("=" * 60)
    print("評価システムの詳細テスト（緩和版）")
    print("=" * 60)
    
    # テストデータ準備
    evaluator = CommentEvaluator()
    weather_data = create_sample_weather()
    context = EvaluationContext(
        weather_condition="晴れ",
        location="東京", 
        target_datetime=datetime.now()
    )
    
    print(f"緩和版評価重み:")
    for criterion, weight in evaluator.weights.items():
        print(f"  {criterion.value}: {weight}")
    print()
    
    # テストケース一覧
    test_cases = [
        ("良いコメント", create_good_comment_pair, context, weather_data),
        ("悪いコメント(ネガティブ)", create_bad_comment_pair, context, weather_data),
        ("平凡なコメント", create_typical_comment_pair, context, weather_data),
        ("天気矛盾コメント", create_contradictory_comment_pair,
         EvaluationContext(weather_condition="雨", location="東京", target_datetime=datetime.now()),
         WeatherForecast(
             location="東京", datetime=datetime.now(), temperature=15.0,
             weather_description="雨", weather_condition="雨", humidity=80.0,
             precipitation=5.0, wind_speed=4.0, wind_direction="南",
             wind_direction_degrees=180.0, weather_code="200"
         )),
        ("重複コメント", create_duplicate_comment_pair, context, weather_data),
        ("極端に不適切なコメント", create_extremely_inappropriate_comment_pair, context, weather_data),
    ]
    
    for i, (test_name, create_func, test_context, test_weather) in enumerate(test_cases, 1):
        print(f"【テストケース{i}: {test_name}】")
        comment_pair = create_func()
        print(f"天気コメント: '{comment_pair.weather_comment.comment_text}'")
        print(f"アドバイス: '{comment_pair.advice_comment.comment_text}'")
        if test_name == "天気矛盾コメント":
            print(f"実際の天気: {test_weather.weather_condition}")
        
        result = evaluator.evaluate_comment_pair(comment_pair, test_context, test_weather)
        print(f"総合スコア: {result.total_score:.3f}")
        print(f"合格判定: {'✓ 合格' if result.is_valid else '✗ 不合格'}")
        print("詳細スコア:")
        for score in result.criterion_scores:
            print(f"  {score.criterion.value}: {score.score:.3f} (重み付き: {score.weighted_score:.3f})")
            if score.reason:
                print(f"    理由: {score.reason}")
        if result.suggestions:
            print("改善提案:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        print()


if __name__ == "__main__":
    test_evaluation_system()
