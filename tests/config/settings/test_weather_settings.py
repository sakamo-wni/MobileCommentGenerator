"""天気関連設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch
from pathlib import Path

from src.config.settings.weather_settings import (
    WeatherConfig,
    TemperatureThresholds,
    HumidityThresholds,
    PrecipitationThresholds,
    WindSpeedThresholds,
    WeatherConstants
)


class TestWeatherConfig:
    """WeatherConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = WeatherConfig()
            
            assert config.default_location == "東京"
            assert config.forecast_hours == 24
            assert config.forecast_days == 3
            assert config.cache_ttl_seconds == 3600
            assert config.cache_dir == Path("data/forecast_cache")
            assert config.enable_caching is True
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "DEFAULT_WEATHER_LOCATION": "大阪",
            "WEATHER_FORECAST_HOURS": "48",
            "WEATHER_FORECAST_DAYS": "5",
            "WEATHER_CACHE_TTL": "7200",
            "WEATHER_CACHE_DIR": "/tmp/weather_cache",
            "WEATHER_ENABLE_CACHING": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            config = WeatherConfig()
            
            assert config.default_location == "大阪"
            assert config.forecast_hours == 48
            assert config.forecast_days == 5
            assert config.cache_ttl_seconds == 7200
            assert config.cache_dir == Path("/tmp/weather_cache")
            assert config.enable_caching is False
    
    def test_temperature_thresholds(self):
        """温度閾値設定のテスト"""
        env_vars = {
            "TEMP_DIFF_THRESHOLD_PREVIOUS_DAY": "7.0",
            "TEMP_DIFF_THRESHOLD_12HOURS": "5.0",
            "DAILY_TEMP_RANGE_THRESHOLD_LARGE": "20.0",
            "DAILY_TEMP_RANGE_THRESHOLD_MEDIUM": "12.0"
        }
        
        with patch.dict(os.environ, env_vars):
            config = WeatherConfig()
            
            assert config.temp_diff_threshold_previous_day == 7.0
            assert config.temp_diff_threshold_12hours == 5.0
            assert config.daily_temp_range_threshold_large == 20.0
            assert config.daily_temp_range_threshold_medium == 12.0
    
    def test_directory_path_configuration(self, tmp_path):
        """ディレクトリパスの設定テスト"""
        cache_dir = tmp_path / "test_cache"
        
        with patch.dict(os.environ, {"WEATHER_CACHE_DIR": str(cache_dir)}):
            config = WeatherConfig()
            
            # ディレクトリパスが正しく設定されていることを確認
            # （実際の作成はConfig.ensure_directories()で行われる）
            assert config.cache_dir == cache_dir
            # ディレクトリはまだ作成されていない（遅延実行パターン）
            assert not cache_dir.exists()


class TestTemperatureThresholds:
    """TemperatureThresholdsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            thresholds = TemperatureThresholds()
            
            assert thresholds.HOT_WEATHER == 30.0
            assert thresholds.WARM_WEATHER == 25.0
            assert thresholds.COOL_WEATHER == 10.0
            assert thresholds.COLD_WEATHER == 5.0
            assert thresholds.COLD_COMMENT_THRESHOLD == 12.0
    
    def test_env_override(self):
        """環境変数オーバーライドのテスト"""
        env_vars = {
            "TEMP_HOT_WEATHER_THRESHOLD": "35.0",
            "TEMP_WARM_WEATHER_THRESHOLD": "28.0",
            "TEMP_COOL_WEATHER_THRESHOLD": "15.0",
            "TEMP_COLD_WEATHER_THRESHOLD": "8.0"
        }
        
        with patch.dict(os.environ, env_vars):
            thresholds = TemperatureThresholds()
            
            assert thresholds.HOT_WEATHER == 35.0
            assert thresholds.WARM_WEATHER == 28.0
            assert thresholds.COOL_WEATHER == 15.0
            assert thresholds.COLD_WEATHER == 8.0


class TestHumidityThresholds:
    """HumidityThresholdsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            thresholds = HumidityThresholds()
            
            assert thresholds.HIGH_HUMIDITY == 80.0
            assert thresholds.LOW_HUMIDITY == 30.0
            assert thresholds.VERY_HIGH_HUMIDITY == 90.0
            assert thresholds.VERY_LOW_HUMIDITY == 20.0
    
    def test_env_override(self):
        """環境変数オーバーライドのテスト"""
        env_vars = {
            "HUMIDITY_HIGH_THRESHOLD": "85.0",
            "HUMIDITY_LOW_THRESHOLD": "35.0"
        }
        
        with patch.dict(os.environ, env_vars):
            thresholds = HumidityThresholds()
            
            assert thresholds.HIGH_HUMIDITY == 85.0
            assert thresholds.LOW_HUMIDITY == 35.0


class TestPrecipitationThresholds:
    """PrecipitationThresholdsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            thresholds = PrecipitationThresholds()
            
            assert thresholds.LIGHT_RAIN == 1.0
            assert thresholds.MODERATE_RAIN == 5.0
            assert thresholds.HEAVY_RAIN == 10.0
            assert thresholds.VERY_HEAVY_RAIN == 30.0
    
    def test_env_override(self):
        """環境変数オーバーライドのテスト"""
        env_vars = {
            "PRECIP_LIGHT_RAIN_THRESHOLD": "2.0",
            "PRECIP_MODERATE_RAIN_THRESHOLD": "15.0",
            "PRECIP_HEAVY_RAIN_THRESHOLD": "20.0"
        }
        
        with patch.dict(os.environ, env_vars):
            thresholds = PrecipitationThresholds()
            
            assert thresholds.LIGHT_RAIN == 2.0
            assert thresholds.MODERATE_RAIN == 15.0
            assert thresholds.HEAVY_RAIN == 20.0


class TestWindSpeedThresholds:
    """WindSpeedThresholdsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            thresholds = WindSpeedThresholds()
            
            assert thresholds.LIGHT_BREEZE == 3.0
            assert thresholds.MODERATE_BREEZE == 7.0
            assert thresholds.STRONG_BREEZE == 12.0
            assert thresholds.GALE == 20.0
    
    def test_env_override(self):
        """環境変数オーバーライドのテスト"""
        env_vars = {
            "WIND_LIGHT_BREEZE_THRESHOLD": "5.0",
            "WIND_MODERATE_BREEZE_THRESHOLD": "10.0",
            "WIND_STRONG_BREEZE_THRESHOLD": "18.0"
        }
        
        with patch.dict(os.environ, env_vars):
            thresholds = WindSpeedThresholds()
            
            assert thresholds.LIGHT_BREEZE == 5.0
            assert thresholds.MODERATE_BREEZE == 10.0
            assert thresholds.STRONG_BREEZE == 18.0


class TestWeatherConstants:
    """WeatherConstantsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            constants = WeatherConstants()
            
            assert constants.HEATSTROKE_WARNING_TEMP == 34.0
            assert constants.HEATSTROKE_SEVERE_TEMP == 35.0
            assert constants.COLD_WARNING_TEMP == 15.0
            assert constants.WEATHER_CHANGE_THRESHOLD == 2
    
    def test_weather_type_keywords(self):
        """天気タイプキーワードのテスト"""
        constants = WeatherConstants()
        
        assert "晴" in constants.WEATHER_TYPE_KEYWORDS["sunny"]
        assert "曇" in constants.WEATHER_TYPE_KEYWORDS["cloudy"]
        assert "雨" in constants.WEATHER_TYPE_KEYWORDS["rainy"]