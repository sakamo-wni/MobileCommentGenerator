"""
Weather information formatter for unified comment generation

天気情報のフォーマット処理
"""

from __future__ import annotations

from typing import Any
from src.constants.weather_constants import TEMP, PRECIP, COMMENT


def format_weather_info(weather_data: Any, 
                       temperature_differences: dict[str, float | None] | None,
                       weather_trend: Any | None) -> str:
    """天気情報を文字列にフォーマット
    
    Args:
        weather_data: 天気データ
        temperature_differences: 気温差データ
        weather_trend: 天気変化傾向
        
    Returns:
        フォーマットされた天気情報文字列
    """
    info = f"{TEMP}: {weather_data.temperature}°C\n"
    info += f"{COMMENT}: {weather_data.weather_description}\n"
    info += f"{PRECIP}: {weather_data.precipitation}mm/h\n"
    info += f"風速: {weather_data.wind_speed}m/s\n"
    info += f"風向: {weather_data.wind_direction.name if weather_data.wind_direction else '不明'}\n"
    info += f"湿度: {weather_data.humidity}%\n"
    
    # 気温差情報
    if temperature_differences:
        if temperature_differences.get("previous_day_diff") is not None:
            info += f"前日との気温差: {temperature_differences['previous_day_diff']:.1f}°C\n"
        if temperature_differences.get("twelve_hours_ago_diff") is not None:
            info += f"12時間前との気温差: {temperature_differences['twelve_hours_ago_diff']:.1f}°C\n"
        if temperature_differences.get("daily_range") is not None:
            info += f"日較差: {temperature_differences['daily_range']:.1f}°C\n"
    
    # 天気変化傾向（WeatherTrendが渡された場合）
    if weather_trend:
        info += f"天気変化傾向: {weather_trend.get_summary()}\n"
        
    return info