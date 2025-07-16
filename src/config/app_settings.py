"""
アプリケーション全体の設定管理

全体の設定を統合管理する
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any
from dotenv import load_dotenv

from .config import get_system_constants, get_weather_config, get_langgraph_config, get_config as get_unified_config

# 定数を取得
_sys_const = get_system_constants()

# 互換性のために既存の変数名を維持
MAX_FORECAST_HOURS = _sys_const.MAX_FORECAST_HOURS
MAX_API_TIMEOUT = _sys_const.MAX_API_TIMEOUT
VALID_LOG_LEVELS = _sys_const.VALID_LOG_LEVELS


@dataclass
class AppConfig:
    """アプリケーション全体の設定クラス（非推奨: 新しいconfigを使用してください）

    Attributes:
        weather: 天気予報設定
        langgraph: LangGraph設定
        debug_mode: デバッグモード
        log_level: ログレベル
    """

    def __init__(self):
        """統一設定から初期化"""
        unified_config = get_unified_config()
        self.weather = unified_config.weather
        self.langgraph = unified_config.langgraph
        self.debug_mode = unified_config.app.debug
        self.log_level = unified_config.app.log_level

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "weather": {
                "wxtech_api_key": "***" if self.weather.default_location else "",
                "default_location": self.weather.default_location,
                "forecast_hours": self.weather.forecast_hours,
                "forecast_hours_ahead": self.weather.forecast_hours_ahead,
                "api_timeout": 30,  # 旧フィールドとの互換性
                "max_retries": 3,   # 旧フィールドとの互換性
                "rate_limit_delay": 0.1,  # 旧フィールドとの互換性
                "cache_ttl": self.weather.cache_ttl_seconds,
                "enable_caching": self.weather.enable_caching,
                "use_optimized_forecast": self.weather.use_optimized_forecast,
                "forecast_cache_retention_days": self.weather.forecast_cache_retention_days,
                "temp_diff_threshold_previous_day": 5.0,  # 旧フィールドとの互換性
                "temp_diff_threshold_12hours": 3.0,  # 旧フィールドとの互換性
                "daily_temp_range_threshold_large": 15.0,  # 旧フィールドとの互換性
                "daily_temp_range_threshold_medium": 10.0,  # 旧フィールドとの互換性
                "temp_threshold_hot": 30.0,  # 旧フィールドとの互換性
                "temp_threshold_warm": 25.0,  # 旧フィールドとの互換性
                "temp_threshold_cool": 10.0,  # 旧フィールドとの互換性
                "temp_threshold_cold": 5.0,  # 旧フィールドとの互換性
            },
            "langgraph": {
                "enable_weather_integration": self.langgraph.enable_weather_integration,
                "auto_location_detection": self.langgraph.auto_location_detection,
                "weather_context_window": self.langgraph.weather_context_window,
                "min_confidence_threshold": self.langgraph.min_confidence_threshold,
            },
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
        }


# グローバル設定インスタンス
_config = None
_env_loaded = False


def get_config() -> AppConfig:
    """グローバル設定インスタンスを取得（非推奨: get_unified_configを使用してください）

    Returns:
        アプリケーション設定
    
    Raises:
        RuntimeError: 設定の読み込みに失敗した場合
    """
    global _config, _env_loaded
    try:
        if not _env_loaded:
            load_dotenv()
            _env_loaded = True
        if _config is None:
            _config = AppConfig()
        return _config
    except Exception as e:
        raise RuntimeError(f"設定の読み込みに失敗しました: {str(e)}")


def reload_config() -> AppConfig:
    """設定を再読み込み

    Returns:
        新しいアプリケーション設定
    """
    global _config, _env_loaded
    load_dotenv(override=True)  # 環境変数を強制再読み込み
    _env_loaded = True
    _config = AppConfig()
    return _config


# 設定検証関数
def validate_config(config: AppConfig) -> dict[str, list[str]]:
    """設定の妥当性を検証

    Args:
        config: 検証するアプリケーション設定

    Returns:
        検証エラーの辞書 {'category': [error_messages]}
    """
    errors: dict[str, list[str]] = {"weather": [], "langgraph": [], "general": []}

    # 天気設定の検証
    try:
        if not config.weather.wxtech_api_key:
            errors["weather"].append("WxTech APIキーが設定されていません")

        if config.weather.forecast_hours > MAX_FORECAST_HOURS:
            errors["weather"].append(f"予報時間数が長すぎます（最大{MAX_FORECAST_HOURS}時間）")

        if config.weather.api_timeout > MAX_API_TIMEOUT:
            errors["weather"].append(f"APIタイムアウトが長すぎます（最大{MAX_API_TIMEOUT}秒）")

    except Exception as e:
        errors["weather"].append(f"天気設定エラー: {str(e)}")

    # LangGraph設定の検証
    try:
        if not 0 <= config.langgraph.min_confidence_threshold <= 1:
            errors["langgraph"].append("信頼度閾値は0.0-1.0の範囲で設定してください")

        if config.langgraph.weather_context_window <= 0:
            errors["langgraph"].append("天気コンテキスト窓は1以上で設定してください")

    except Exception as e:
        errors["langgraph"].append(f"LangGraph設定エラー: {str(e)}")

    # 一般設定の検証
    if config.log_level not in VALID_LOG_LEVELS:
        errors["general"].append(f"無効なログレベル: {config.log_level}")

    return {k: v for k, v in errors.items() if v}  # エラーがあるカテゴリのみ返す


# 環境変数のデフォルト値を設定する関数
def setup_environment_defaults():
    """環境変数のデフォルト値を設定

    開発環境やテスト環境で使用
    """
    defaults = {
        "DEFAULT_WEATHER_LOCATION": "東京",
        "WEATHER_FORECAST_HOURS": "24",
        "WEATHER_FORECAST_HOURS_AHEAD": "12",
        "WEATHER_API_TIMEOUT": "30",
        "WEATHER_API_MAX_RETRIES": "3",
        "WEATHER_API_RATE_LIMIT_DELAY": "0.1",
        "WEATHER_CACHE_TTL": "300",
        "WEATHER_ENABLE_CACHING": "true",
        "FORECAST_CACHE_RETENTION_DAYS": "7",
        "TEMP_DIFF_THRESHOLD_PREVIOUS_DAY": "5.0",
        "TEMP_DIFF_THRESHOLD_12HOURS": "3.0",
        "DAILY_TEMP_RANGE_THRESHOLD_LARGE": "15.0",
        "DAILY_TEMP_RANGE_THRESHOLD_MEDIUM": "10.0",
        "LANGGRAPH_ENABLE_WEATHER": "true",
        "LANGGRAPH_AUTO_LOCATION": "false",
        "LANGGRAPH_WEATHER_CONTEXT_WINDOW": "24",
        "LANGGRAPH_MIN_CONFIDENCE": "0.7",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
    }

    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value