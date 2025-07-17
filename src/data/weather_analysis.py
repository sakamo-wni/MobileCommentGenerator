"""
天気データの分析・ビジネスロジック

天気データの分析、パターン検出、意思決定ロジックを提供
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from src.data.weather_models import WeatherForecast
from src.data.weather_collection import WeatherForecastCollection
from src.data.weather_enums import WeatherCondition


def detect_weather_changes(
    collection: WeatherForecastCollection,
    hours_ahead: int = 3
) -> list[tuple[datetime, str]]:
    """天気の変化を検出
    
    Args:
        collection: 天気予報コレクション
        hours_ahead: 何時間先まで見るか
        
    Returns:
        (時刻, 変化内容) のリスト
    """
    changes = []
    
    if len(collection) < 2:
        return changes
    
    current_time = datetime.now()
    future_time = current_time + timedelta(hours=hours_ahead)
    
    relevant_forecasts = collection.get_forecasts_between(current_time, future_time)
    
    if len(relevant_forecasts) < 2:
        return changes
    
    for i in range(1, len(relevant_forecasts)):
        prev = relevant_forecasts[i-1]
        curr = relevant_forecasts[i]
        
        # 天気状況の変化
        if prev.weather_condition != curr.weather_condition:
            change_desc = f"{prev.weather_condition.get_japanese_name()} → {curr.weather_condition.get_japanese_name()}"
            changes.append((curr.datetime, change_desc))
        
        # 大幅な気温変化（3度以上）
        temp_diff = abs(curr.temperature - prev.temperature)
        if temp_diff >= 3.0:
            direction = "上昇" if curr.temperature > prev.temperature else "下降"
            changes.append((curr.datetime, f"気温{direction} ({temp_diff:.1f}度)"))
        
        # 降水の開始/終了
        if not prev.is_rainy and curr.is_rainy:
            changes.append((curr.datetime, "降雨開始"))
        elif prev.is_rainy and not curr.is_rainy:
            changes.append((curr.datetime, "降雨終了"))
    
    return changes


def analyze_weather_trend(
    collection: WeatherForecastCollection,
    hours: int = 12
) -> dict[str, any]:
    """天気の傾向を分析
    
    Args:
        collection: 天気予報コレクション
        hours: 分析対象時間
        
    Returns:
        分析結果の辞書
    """
    current_time = datetime.now()
    future_time = current_time + timedelta(hours=hours)
    
    forecasts = collection.get_forecasts_between(current_time, future_time)
    
    if not forecasts:
        return {
            "trend": "unknown",
            "temperature_trend": "stable",
            "precipitation_risk": "low",
            "extreme_weather_risk": False,
        }
    
    # 気温トレンド
    temperatures = [f.temperature for f in forecasts]
    temp_diff = temperatures[-1] - temperatures[0] if len(temperatures) > 1 else 0
    
    if temp_diff > 3:
        temp_trend = "rising"
    elif temp_diff < -3:
        temp_trend = "falling"
    else:
        temp_trend = "stable"
    
    # 降水リスク
    rain_count = sum(1 for f in forecasts if f.is_rainy)
    rain_percentage = rain_count / len(forecasts) if forecasts else 0
    
    if rain_percentage > 0.7:
        precip_risk = "high"
    elif rain_percentage > 0.3:
        precip_risk = "medium"
    else:
        precip_risk = "low"
    
    # 異常気象リスク
    extreme_weather = any(f.is_extreme_weather for f in forecasts)
    
    # 全体的な傾向
    if extreme_weather:
        overall_trend = "worsening"
    elif precip_risk == "high" or any(f.weather_condition == WeatherCondition.HEAVY_RAIN for f in forecasts):
        overall_trend = "unstable"
    elif temp_trend == "stable" and precip_risk == "low":
        overall_trend = "stable"
    else:
        overall_trend = "changing"
    
    return {
        "trend": overall_trend,
        "temperature_trend": temp_trend,
        "precipitation_risk": precip_risk,
        "extreme_weather_risk": extreme_weather,
        "min_temperature": min(temperatures) if temperatures else None,
        "max_temperature": max(temperatures) if temperatures else None,
        "total_precipitation": sum(f.precipitation for f in forecasts),
        "analysis_period_hours": hours,
        "data_points": len(forecasts),
    }


def find_optimal_outdoor_time(
    collection: WeatherForecastCollection,
    start_hour: int = 6,
    end_hour: int = 18
) -> Optional[datetime]:
    """外出に最適な時間を探す
    
    Args:
        collection: 天気予報コレクション
        start_hour: 検索開始時刻（時）
        end_hour: 検索終了時刻（時）
        
    Returns:
        最適な時刻、見つからない場合はNone
    """
    current_time = datetime.now()
    today_start = current_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    today_end = current_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    # 現在時刻より前は除外
    if today_start < current_time:
        today_start = current_time
    
    candidates = collection.get_forecasts_between(today_start, today_end)
    
    if not candidates:
        return None
    
    # スコアリング（低いほど良い）
    def score_forecast(forecast: WeatherForecast) -> float:
        score = 0.0
        
        # 降水ペナルティ
        score += forecast.precipitation * 10
        
        # 天気状況ペナルティ
        score += forecast.weather_condition.priority * 2
        
        # 気温ペナルティ（快適温度から離れるほど高い）
        if forecast.temperature < 15:
            score += (15 - forecast.temperature) * 0.5
        elif forecast.temperature > 28:
            score += (forecast.temperature - 28) * 0.5
        
        # 風速ペナルティ
        if forecast.is_strong_wind:
            score += 5
        
        return score
    
    # 最もスコアの低い時間を選択
    best_forecast = min(candidates, key=score_forecast)
    
    # スコアが高すぎる場合は適切な時間なし
    if score_forecast(best_forecast) > 20:
        return None
    
    return best_forecast.datetime


def calculate_clothing_index(forecast: WeatherForecast) -> int:
    """服装指数を計算（0-5: 0=真夏の服装, 5=真冬の服装）
    
    Args:
        forecast: 天気予報
        
    Returns:
        服装指数
    """
    # 体感温度を基準に
    base_temp = forecast.feels_like
    
    # 基本指数
    if base_temp >= 28:
        index = 0  # 真夏
    elif base_temp >= 23:
        index = 1  # 夏
    elif base_temp >= 18:
        index = 2  # 春秋（薄手）
    elif base_temp >= 13:
        index = 3  # 春秋（厚手）
    elif base_temp >= 8:
        index = 4  # 冬
    else:
        index = 5  # 真冬
    
    # 雨による調整
    if forecast.is_rainy and index < 5:
        index += 0.5
    
    # 風による調整
    if forecast.is_strong_wind and base_temp < 20:
        index += 0.5
    
    # 0-5の範囲に収める
    return max(0, min(5, round(index)))