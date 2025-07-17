"""コメント安全性チェックモジュール（リファクタリング版）"""

from __future__ import annotations
from typing import Any
import logging
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from .safety_checks import (
    WeatherConsistencyChecker,
    SeasonalAppropriatenessChecker,
    RainContextChecker,
    AlternativeCommentFinder
)

logger = logging.getLogger(__name__)


def check_and_fix_weather_comment_safety(
    weather_data: WeatherForecast,
    weather_comment: str,
    advice_comment: str,
    state: CommentGenerationState
) -> tuple[str, str]:
    """コメントの安全性をチェックし、必要に応じて修正する
    
    Args:
        weather_data: 天気予報データ
        weather_comment: 天気コメント
        advice_comment: アドバイスコメント
        state: コメント生成状態
        
    Returns:
        (修正後の天気コメント, 修正後のアドバイスコメント)のタプル
    """
    logger.info(f"🚨 最終安全チェック開始: 天気='{weather_data.weather_description}', 気温={weather_data.temperature}°C")
    logger.info(f"🚨 選択されたコメント: 天気='{weather_comment}', アドバイス='{advice_comment}'")
    
    # チェッカーのインスタンス化
    weather_checker = WeatherConsistencyChecker()
    seasonal_checker = SeasonalAppropriatenessChecker()
    rain_checker = RainContextChecker()
    alternative_finder = AlternativeCommentFinder()
    
    # 1. 晴天時の一貫性チェック
    is_inappropriate, pattern, patterns = weather_checker.check_sunny_weather_consistency(
        weather_data, weather_comment
    )
    if is_inappropriate:
        weather_comment = alternative_finder.find_alternative_weather_comment(
            weather_data, state.past_comments, patterns, state
        )
    
    # 2. 雨天時の一貫性チェック
    is_inappropriate, pattern, patterns = weather_checker.check_rainy_weather_consistency(
        weather_data, weather_comment, advice_comment
    )
    if is_inappropriate:
        if pattern == "熱中症":
            advice_comment = alternative_finder.find_rain_advice(
                state.past_comments, advice_comment
            )
        elif pattern == "ムシムシ":
            weather_comment = alternative_finder.find_storm_weather_comment(
                state.past_comments, weather_comment
            )
        else:
            weather_comment = alternative_finder.find_rain_weather_comment(
                state.past_comments, weather_comment, weather_data
            )
    
    # 3. 曇天時の一貫性チェック
    is_inappropriate, pattern, patterns = weather_checker.check_cloudy_weather_consistency(
        weather_data, weather_comment
    )
    if is_inappropriate:
        weather_comment = alternative_finder.find_cloudy_weather_comment(
            state.past_comments, weather_comment
        )
    
    # 4. 連続雨チェック
    is_inappropriate, pattern, patterns = rain_checker.check_continuous_rain_context(
        weather_comment, state
    )
    if is_inappropriate:
        weather_comment = alternative_finder.find_rain_weather_comment(
            state.past_comments, weather_comment, weather_data, avoid_shower=True
        )
    
    # 5. 天気の安定性チェック
    is_inappropriate, pattern, patterns = weather_checker.check_weather_stability(
        weather_comment, state
    )
    if is_inappropriate:
        weather_comment = alternative_finder.find_alternative_weather_comment(
            weather_data, state.past_comments, patterns, state
        )
    
    # 6. 季節の適切性チェック
    is_inappropriate, pattern, patterns = seasonal_checker.check_seasonal_appropriateness(
        weather_comment, state
    )
    if is_inappropriate:
        # 残暑の場合は単純置換を試みる
        if pattern == "残暑" and state.target_datetime.month in [6, 7, 8]:
            weather_comment = seasonal_checker.get_temperature_appropriate_replacement(
                weather_comment, state.target_datetime.month
            )
        else:
            weather_comment = alternative_finder.find_alternative_weather_comment(
                weather_data, state.past_comments, patterns, state
            )
    
    return weather_comment, advice_comment