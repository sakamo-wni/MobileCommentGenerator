"""
天気データ関連のデータクラスと型定義

WxTech APIからの天気予報データを標準化して扱うためのクラス群

このモジュールは後方互換性のために維持されています。
新しいコードでは、以下のモジュールから直接インポートすることを推奨します：
- src.data.weather_enums: WeatherCondition, WindDirection
- src.data.weather_models: WeatherForecast
- src.data.weather_collection: WeatherForecastCollection
- src.data.weather_analysis: 分析関数群
"""

# 後方互換性のための再エクスポート
from src.data.weather_enums import WeatherCondition, WindDirection
from src.data.weather_models import WeatherForecast
# 互換性ラッパーを使用
from src.data.weather_data_compat import WeatherForecastCollection

# 分析関数も再エクスポート（必要に応じて）
from src.data.weather_analysis import (
    detect_weather_changes,
    analyze_weather_trend,
    find_optimal_outdoor_time,
    calculate_clothing_index,
)

__all__ = [
    'WeatherCondition',
    'WindDirection',
    'WeatherForecast',
    'WeatherForecastCollection',
    'detect_weather_changes',
    'analyze_weather_trend',
    'find_optimal_outdoor_time',
    'calculate_clothing_index',
]