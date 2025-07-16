"""
Forecast cache utility functions

予報キャッシュ関連のユーティリティ関数
"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo
from typing import Optional

from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)

# タイムゾーン定義
JST = ZoneInfo("Asia/Tokyo")


@lru_cache(maxsize=1024)
def ensure_jst(dt: datetime) -> datetime:
    """datetimeオブジェクトをJSTとして確実に扱う
    
    Args:
        dt: datetime オブジェクト
        
    Returns:
        JSTタイムゾーン付きのdatetime
    """
    if dt.tzinfo is None:
        # naiveな場合はJSTとして扱う
        return dt.replace(tzinfo=JST)
    elif dt.tzinfo != JST:
        # 他のタイムゾーンの場合はJSTに変換
        return dt.astimezone(JST)
    else:
        # 既にJSTの場合はそのまま返す
        return dt


def get_temperature_differences(current_forecast: WeatherForecast, location_name: str) -> dict[str, Optional[float]]:
    """現在の予報と過去のキャッシュデータを比較して気温差を計算
    
    Args:
        current_forecast: 現在の予報データ
        location_name: 地点名
        
    Returns:
        気温差の辞書:
        - previous_day_diff: 前日同時刻との気温差
        - twelve_hours_ago_diff: 12時間前との気温差
        - daily_range: 日較差（今日の最高気温と最低気温の差）
    """
    from .manager import get_forecast_cache
    cache = get_forecast_cache()
    current_dt = ensure_jst(current_forecast.datetime)
    
    differences = {
        "previous_day_diff": None,
        "twelve_hours_ago_diff": None,
        "daily_range": None
    }
    
    try:
        # 前日同時刻のデータを取得
        previous_day_dt = current_dt - timedelta(days=1)
        previous_day_data = cache.get_forecast_at_time(location_name, previous_day_dt)
        
        if previous_day_data:
            differences["previous_day_diff"] = current_forecast.temperature - previous_day_data.temperature
            logger.info(
                f"前日との気温差: {differences['previous_day_diff']:.1f}℃ "
                f"(今日: {current_forecast.temperature}℃, 昨日: {previous_day_data.temperature}℃)"
            )
        
        # 12時間前のデータを取得
        twelve_hours_ago_dt = current_dt - timedelta(hours=12)
        twelve_hours_ago_data = cache.get_forecast_at_time(location_name, twelve_hours_ago_dt)
        
        if twelve_hours_ago_data:
            differences["twelve_hours_ago_diff"] = current_forecast.temperature - twelve_hours_ago_data.temperature
            logger.info(
                f"12時間前との気温差: {differences['twelve_hours_ago_diff']:.1f}℃ "
                f"(現在: {current_forecast.temperature}℃, 12時間前: {twelve_hours_ago_data.temperature}℃)"
            )
        
        # 今日の日較差を計算
        daily_min_max = cache.get_daily_min_max(location_name, current_dt.date())
        if daily_min_max and daily_min_max["max"] is not None and daily_min_max["min"] is not None:
            differences["daily_range"] = daily_min_max["max"] - daily_min_max["min"]
            logger.info(
                f"日較差: {differences['daily_range']:.1f}℃ "
                f"(最高: {daily_min_max['max']}℃, 最低: {daily_min_max['min']}℃)"
            )
        
    except Exception as e:
        logger.error(f"気温差の計算中にエラーが発生: {e}")
    
    return differences


def save_forecast_to_cache(weather_forecast: WeatherForecast, location_name: str) -> None:
    """予報データをキャッシュに保存（簡易インターフェース）
    
    Args:
        weather_forecast: 天気予報データ
        location_name: 地点名
    """
    from .manager import get_forecast_cache
    cache = get_forecast_cache()
    cache.save_forecast(weather_forecast, location_name)