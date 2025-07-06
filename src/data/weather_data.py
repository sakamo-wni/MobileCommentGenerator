"""
天気データ関連の後方互換性モジュール

既存のインポートとの互換性を保つため、weatherパッケージからすべてを再エクスポート
"""

# 後方互換性のため、weatherパッケージからすべてをインポート
from src.data.weather import (
    WeatherForecast,
    WeatherCondition,
    WindDirection,
    WeatherForecastCollection,
    WeatherValidator
)

__all__ = [
    "WeatherForecast",
    "WeatherCondition",
    "WindDirection",
    "WeatherForecastCollection",
    "WeatherValidator"
]