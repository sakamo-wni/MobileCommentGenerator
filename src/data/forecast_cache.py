"""
天気予報キャッシュシステム（後方互換性のためのラッパー）

このファイルは後方互換性のために保持されています。
新しいコードでは src.data.forecast_cache パッケージを直接インポートしてください。
"""

# 後方互換性のため、すべてのエクスポートを再エクスポート
from src.data.forecast_cache import (
    ForecastCacheEntry,
    ForecastCache,
    get_forecast_cache,
    ensure_jst,
    get_temperature_differences,
    save_forecast_to_cache
)

__all__ = [
    'ForecastCacheEntry',
    'ForecastCache',
    'get_forecast_cache',
    'ensure_jst',
    'get_temperature_differences',
    'save_forecast_to_cache'
]