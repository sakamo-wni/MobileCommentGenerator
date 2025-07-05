"""weather_settings.pyのテスト"""

import os
import pytest
from unittest import mock

from src.config.weather_settings import WeatherConfig


class TestWeatherConfig:
    """WeatherConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}, clear=True):
            config = WeatherConfig()
            
            assert config.wxtech_api_key == "test_key"
            assert config.default_location == "東京"
            assert config.forecast_hours == 24
            assert config.forecast_hours_ahead == 0  # constants.pyのDEFAULT_FORECAST_HOURS_AHEAD
            assert config.api_timeout == 30
    
    def test_temperature_threshold_validation(self):
        """温度閾値の整合性チェックテスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            # cold >= cool のケース
            with pytest.raises(ValueError, match="temp_threshold_coldはtemp_threshold_coolより小さい必要があります"):
                WeatherConfig(
                    temp_threshold_cold=20.0,
                    temp_threshold_cool=15.0
                )
            
            # cool >= warm のケース
            with pytest.raises(ValueError, match="temp_threshold_coolはtemp_threshold_warmより小さい必要があります"):
                WeatherConfig(
                    temp_threshold_cool=25.0,
                    temp_threshold_warm=20.0
                )
            
            # warm >= hot のケース
            with pytest.raises(ValueError, match="temp_threshold_warmはtemp_threshold_hotより小さい必要があります"):
                WeatherConfig(
                    temp_threshold_warm=35.0,
                    temp_threshold_hot=30.0
                )
    
    def test_forecast_hours_validation(self):
        """予報時間の妥当性検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            # forecast_hours_ahead < 0 のケース
            with mock.patch.dict(os.environ, {"WEATHER_FORECAST_HOURS_AHEAD": "-1"}):
                with pytest.raises(ValueError, match="forecast_hours_aheadは0以上である必要があります"):
                    WeatherConfig()
            
            # 予報期間の合計が168時間を超えるケース
            with mock.patch.dict(os.environ, {
                "WEATHER_FORECAST_HOURS": "100",
                "WEATHER_FORECAST_HOURS_AHEAD": "100"
            }):
                with pytest.raises(ValueError, match="予報期間の合計が168時間を超えています"):
                    WeatherConfig()
    
    def test_api_key_validation(self):
        """APIキーの検証テスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="WXTECH_API_KEY環境変数が設定されていません"):
                WeatherConfig()
    
    def test_forecast_hours_positive_validation(self):
        """予報時間が正の値であることの検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            with pytest.raises(ValueError, match="forecast_hoursは1以上である必要があります"):
                with mock.patch.dict(os.environ, {"WEATHER_FORECAST_HOURS": "0"}):
                    WeatherConfig()
            
            with pytest.raises(ValueError, match="forecast_hoursは1以上である必要があります"):
                with mock.patch.dict(os.environ, {"WEATHER_FORECAST_HOURS": "-5"}):
                    WeatherConfig()
    
    def test_api_timeout_validation(self):
        """APIタイムアウトの検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            with pytest.raises(ValueError, match="api_timeoutは1以上である必要があります"):
                with mock.patch.dict(os.environ, {"WEATHER_API_TIMEOUT": "0"}):
                    WeatherConfig()
            
            with pytest.raises(ValueError, match="api_timeoutは1以上である必要があります"):
                with mock.patch.dict(os.environ, {"WEATHER_API_TIMEOUT": "-1"}):
                    WeatherConfig()
    
    def test_environment_variable_loading(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "WXTECH_API_KEY": "env_test_key",
            "DEFAULT_WEATHER_LOCATION": "大阪",
            "WEATHER_FORECAST_HOURS": "48",
            "WEATHER_FORECAST_HOURS_AHEAD": "12",
            "WEATHER_API_TIMEOUT": "60",
            "WEATHER_API_MAX_RETRIES": "5",
            "WEATHER_API_RATE_LIMIT_DELAY": "0.5",
            "WEATHER_CACHE_TTL": "600",
            "WEATHER_ENABLE_CACHING": "false",
            "FORECAST_CACHE_RETENTION_DAYS": "14",
            "TEMP_DIFF_THRESHOLD_PREVIOUS_DAY": "7.0",
            "TEMP_DIFF_THRESHOLD_12HOURS": "4.0",
            "DAILY_TEMP_RANGE_THRESHOLD_LARGE": "20.0",
            "DAILY_TEMP_RANGE_THRESHOLD_MEDIUM": "12.0",
            "TEMP_THRESHOLD_HOT": "35.0",
            "TEMP_THRESHOLD_WARM": "28.0",
            "TEMP_THRESHOLD_COOL": "12.0",
            "TEMP_THRESHOLD_COLD": "7.0",
        }
        
        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = WeatherConfig()
            
            assert config.wxtech_api_key == "env_test_key"
            assert config.default_location == "大阪"
            assert config.forecast_hours == 48
            assert config.forecast_hours_ahead == 12
            assert config.api_timeout == 60
            assert config.max_retries == 5
            assert config.rate_limit_delay == 0.5
            assert config.cache_ttl == 600
            assert config.enable_caching is False
            assert config.forecast_cache_retention_days == 14
            assert config.temp_diff_threshold_previous_day == 7.0
            assert config.temp_diff_threshold_12hours == 4.0
            assert config.daily_temp_range_threshold_large == 20.0
            assert config.daily_temp_range_threshold_medium == 12.0
            assert config.temp_threshold_hot == 35.0
            assert config.temp_threshold_warm == 28.0
            assert config.temp_threshold_cool == 12.0
            assert config.temp_threshold_cold == 7.0
    
    def test_to_dict_method(self):
        """to_dict()メソッドのテスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_api_key_123456789"}):
            config = WeatherConfig()
            config_dict = config.to_dict()
            
            # APIキーがマスクされていることを確認
            assert config_dict["wxtech_api_key"] == "test_api...6789"
            assert "default_location" in config_dict
            assert "forecast_hours" in config_dict
            assert "temp_threshold_hot" in config_dict
    
    def test_valid_temperature_thresholds(self):
        """正しい温度閾値の設定テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = WeatherConfig(
                temp_threshold_cold=0.0,
                temp_threshold_cool=10.0,
                temp_threshold_warm=20.0,
                temp_threshold_hot=30.0
            )
            
            assert config.temp_threshold_cold < config.temp_threshold_cool
            assert config.temp_threshold_cool < config.temp_threshold_warm
            assert config.temp_threshold_warm < config.temp_threshold_hot