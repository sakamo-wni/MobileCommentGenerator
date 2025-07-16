"""
統計関連のユーティリティ関数

履歴データからの統計情報生成など
"""

from typing import Any
from datetime import datetime, date
from collections import Counter
import pandas as pd


def get_statistics(history: list[dict[str, Any]]) -> dict[str, Any]:
    """
    履歴データから統計情報を生成

    Args:
        history: 履歴データリスト

    Returns:
        統計情報の辞書
    """
    if not history:
        return {
            "total_generations": 0,
            "successful_generations": 0,
            "success_rate": 0,
            "average_execution_time": 0,
            "locations_count": 0,
            "most_used_location": None,
            "provider_usage": {},
            "weather_conditions": {},
            "time_periods": {},
            "daily_generations": {},
            "today_count": 0,
            "latest_generation": None,
        }

    # 基本統計
    total = len(history)
    successful = sum(1 for item in history if item.get("success", False))
    success_rate = (successful / total * 100) if total > 0 else 0

    # 実行時間の平均
    execution_times = [
        item.get("generation_metadata", {}).get("execution_time_ms", 0)
        for item in history
        if item.get("generation_metadata", {}).get("execution_time_ms")
    ]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

    # 地点別統計
    locations = [item.get("location", "") for item in history if item.get("location")]
    location_counter = Counter(locations)
    most_used_location = location_counter.most_common(1)[0] if location_counter else (None, 0)

    # プロバイダー別統計
    providers = [item.get("llm_provider", "") for item in history if item.get("llm_provider")]
    provider_counter = Counter(providers)

    # 天気条件別統計
    weather_conditions = [
        item.get("generation_metadata", {}).get("weather_condition", "")
        for item in history
        if item.get("generation_metadata", {}).get("weather_condition")
    ]
    weather_counter = Counter(weather_conditions)

    # 時間帯別統計
    time_periods = []
    for item in history:
        try:
            timestamp = datetime.fromisoformat(item.get("timestamp", ""))
            hour = timestamp.hour
            if 5 <= hour < 12:
                period = "morning"
            elif 12 <= hour < 17:
                period = "afternoon"
            elif 17 <= hour < 21:
                period = "evening"
            else:
                period = "night"
            time_periods.append(period)
        except (ValueError, TypeError, AttributeError):
            pass
    time_counter = Counter(time_periods)

    # 日別生成数
    daily_counts = {}
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_count = 0
    
    for item in history:
        try:
            timestamp = datetime.fromisoformat(item.get("timestamp", ""))
            date_str = timestamp.strftime("%Y-%m-%d")
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
            # 今日のカウント
            if date_str == today_str:
                today_count += 1
        except (ValueError, TypeError, AttributeError):
            pass
    
    # 最新生成日時
    latest_generation = None
    if history:
        try:
            # タイムスタンプでソートして最新を取得
            sorted_history = sorted(
                history,
                key=lambda x: datetime.fromisoformat(x.get("timestamp", "")),
                reverse=True
            )
            if sorted_history:
                latest_generation = sorted_history[0].get("timestamp")
        except (ValueError, TypeError, AttributeError):
            pass

    return {
        "total_generations": total,
        "successful_generations": successful,
        "success_rate": round(success_rate, 1),
        "average_execution_time": round(avg_execution_time, 0),
        "locations_count": len(location_counter),
        "most_used_location": most_used_location,
        "provider_usage": dict(provider_counter),
        "weather_conditions": dict(weather_counter),
        "time_periods": dict(time_counter),
        "daily_generations": daily_counts,
        "today_count": today_count,
        "latest_generation": latest_generation,
    }