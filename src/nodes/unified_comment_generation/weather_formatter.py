"""
Weather information formatter for unified comment generation

天気情報のフォーマット処理
"""

from __future__ import annotations

import logging
from typing import Any
from src.constants.weather_constants import TEMP, PRECIP, COMMENT

logger = logging.getLogger(__name__)


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
        
    Raises:
        ValueError: 天気データが不正な場合
    """
    try:
        if not weather_data:
            raise ValueError("天気データが提供されていません")
        
        # 必須フィールドの確認と安全な取得
        temperature = getattr(weather_data, 'temperature', None)
        if temperature is None:
            raise ValueError("気温データが不足しています")
            
        weather_description = getattr(weather_data, 'weather_description', '不明')
        precipitation = getattr(weather_data, 'precipitation', 0)
        wind_speed = getattr(weather_data, 'wind_speed', 0)
        humidity = getattr(weather_data, 'humidity', 0)
        
        info = f"{TEMP}: {temperature}°C\n"
        info += f"天気: {weather_description}\n"
        info += f"{PRECIP}: {precipitation}mm/h\n"
        info += f"風速: {wind_speed}m/s\n"
        
        # 風向の安全な処理
        wind_direction = getattr(weather_data, 'wind_direction', None)
        if wind_direction and hasattr(wind_direction, 'name'):
            info += f"風向: {wind_direction.name}\n"
        else:
            info += f"風向: 不明\n"
            
        info += f"湿度: {humidity}%\n"
        
        # 気温差情報の安全な処理
        if temperature_differences:
            try:
                if temperature_differences.get("previous_day_diff") is not None:
                    info += f"前日との気温差: {temperature_differences['previous_day_diff']:.1f}°C\n"
                if temperature_differences.get("twelve_hours_ago_diff") is not None:
                    info += f"12時間前との気温差: {temperature_differences['twelve_hours_ago_diff']:.1f}°C\n"
                if temperature_differences.get("daily_range") is not None:
                    info += f"日較差: {temperature_differences['daily_range']:.1f}°C\n"
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"気温差情報の処理でエラー: {e}")
        
        # 天気変化傾向の安全な処理
        if weather_trend:
            try:
                if hasattr(weather_trend, 'get_summary'):
                    info += f"天気変化傾向: {weather_trend.get_summary()}\n"
                else:
                    logger.warning("weather_trendにget_summaryメソッドがありません")
            except Exception as e:
                logger.warning(f"天気変化傾向の処理でエラー: {e}")
        
        return info
        
    except Exception as e:
        logger.error(f"天気情報のフォーマット処理でエラー: {e}")
        raise ValueError(f"天気情報のフォーマットに失敗しました: {e}") from e