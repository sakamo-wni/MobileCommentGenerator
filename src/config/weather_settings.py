"""
天気予報機能の設定管理（非推奨）

このモジュールは後方互換性のために保持されています。
新しいコードでは src.config.config から get_weather_config() を使用してください。
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any

from .config import get_system_constants, get_weather_constants, get_weather_config

# 定数を取得
_sys_const = get_system_constants()
_weather_const = get_weather_constants()

# 互換性のために既存の変数名を維持
TEMP_DIFF_THRESHOLD_PREVIOUS_DAY = _weather_const.temperature.SIGNIFICANT_DAILY_DIFF
TEMP_DIFF_THRESHOLD_12HOURS = _weather_const.temperature.HOURLY_SIGNIFICANT_DIFF
DAILY_TEMP_RANGE_THRESHOLD_LARGE = _weather_const.temperature.LARGE_DAILY_RANGE
DAILY_TEMP_RANGE_THRESHOLD_MEDIUM = _weather_const.temperature.MEDIUM_DAILY_RANGE
TEMP_THRESHOLD_HOT = _weather_const.temperature.HOT_WEATHER
TEMP_THRESHOLD_WARM = _weather_const.temperature.WARM_WEATHER
TEMP_THRESHOLD_COOL = _weather_const.temperature.COOL_WEATHER
TEMP_THRESHOLD_COLD = _weather_const.temperature.COLD_WEATHER
DEFAULT_API_TIMEOUT = _sys_const.DEFAULT_API_TIMEOUT
DEFAULT_MAX_RETRIES = _sys_const.DEFAULT_MAX_RETRIES
DEFAULT_RATE_LIMIT_DELAY = _sys_const.DEFAULT_RATE_LIMIT_DELAY
DEFAULT_CACHE_TTL = _sys_const.DEFAULT_CACHE_TTL
DEFAULT_FORECAST_HOURS = _sys_const.DEFAULT_FORECAST_HOURS
DEFAULT_FORECAST_HOURS_AHEAD = _sys_const.DEFAULT_FORECAST_HOURS_AHEAD
DEFAULT_FORECAST_CACHE_RETENTION_DAYS = _sys_const.DEFAULT_FORECAST_CACHE_RETENTION_DAYS
MAX_FORECAST_HOURS = _sys_const.MAX_FORECAST_HOURS


# 非推奨: 後方互換性のためのプロキシクラス
class WeatherConfig:
    """天気予報機能の設定クラス（非推奨: get_weather_config()を使用してください）"""
    
    def __new__(cls):
        """新しい統一設定のWeatherConfigを返す"""
        config = get_weather_config()
        from .config import get_api_config
        api_config = get_api_config()
        
        # 既存のコードとの互換性のために追加属性を設定
        config.wxtech_api_key = api_config.wxtech_api_key if api_config else ""
        config.api_timeout = api_config.api_timeout if api_config else DEFAULT_API_TIMEOUT
        config.max_retries = api_config.retry_count if api_config else DEFAULT_MAX_RETRIES
        config.rate_limit_delay = DEFAULT_RATE_LIMIT_DELAY
        config.cache_ttl = config.cache_ttl_seconds
        
        # 温度差閾値設定（weather_constantsから取得）
        config.temp_diff_threshold_previous_day = TEMP_DIFF_THRESHOLD_PREVIOUS_DAY
        config.temp_diff_threshold_12hours = TEMP_DIFF_THRESHOLD_12HOURS
        config.daily_temp_range_threshold_large = DAILY_TEMP_RANGE_THRESHOLD_LARGE
        config.daily_temp_range_threshold_medium = DAILY_TEMP_RANGE_THRESHOLD_MEDIUM
        
        # 温度分類の閾値
        config.temp_threshold_hot = TEMP_THRESHOLD_HOT
        config.temp_threshold_warm = TEMP_THRESHOLD_WARM
        config.temp_threshold_cool = TEMP_THRESHOLD_COOL
        config.temp_threshold_cold = TEMP_THRESHOLD_COLD
        
        return config