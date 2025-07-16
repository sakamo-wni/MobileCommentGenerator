"""weather_formatter.pyの単体テスト"""

import pytest
from unittest.mock import Mock
from src.nodes.unified_comment_generation.weather_formatter import format_weather_info


class TestFormatWeatherInfo:
    """format_weather_info関数のテスト"""
    
    def test_basic_weather_formatting(self):
        """基本的な天気情報のフォーマット"""
        # Mock weather data
        weather_data = Mock()
        weather_data.temperature = 25.5
        weather_data.weather_description = "晴れ"
        weather_data.precipitation = 0.0
        weather_data.wind_speed = 3.2
        weather_data.wind_direction = Mock(name="北")
        weather_data.humidity = 65
        
        result = format_weather_info(weather_data, None, None)
        
        assert "25.5°C" in result
        assert "天気: 晴れ" in result
        assert "0.0mm/h" in result
        assert "風速: 3.2m/s" in result
        assert "風向:" in result
        assert "湿度: 65%" in result
    
    def test_with_temperature_differences(self):
        """気温差情報を含む場合のフォーマット"""
        weather_data = Mock()
        weather_data.temperature = 20.0
        weather_data.weather_description = "曇り"
        weather_data.precipitation = 0.0
        weather_data.wind_speed = 2.0
        weather_data.wind_direction = Mock(name="東")
        weather_data.humidity = 70
        
        temp_diffs = {
            "previous_day_diff": -3.5,
            "twelve_hours_ago_diff": 2.0,
            "daily_range": 10.5
        }
        
        result = format_weather_info(weather_data, temp_diffs, None)
        
        assert "前日との気温差: -3.5°C" in result
        assert "12時間前との気温差: 2.0°C" in result
        assert "日較差: 10.5°C" in result
    
    def test_missing_wind_direction(self):
        """風向情報が欠落している場合"""
        weather_data = Mock()
        weather_data.temperature = 22.0
        weather_data.weather_description = "雨"
        weather_data.precipitation = 5.0
        weather_data.wind_speed = 4.0
        weather_data.wind_direction = None
        weather_data.humidity = 80
        
        result = format_weather_info(weather_data, None, None)
        
        assert "風向: 不明" in result
    
    def test_with_weather_trend(self):
        """天気変化傾向を含む場合"""
        weather_data = Mock()
        weather_data.temperature = 18.0
        weather_data.weather_description = "雨"
        weather_data.precipitation = 10.0
        weather_data.wind_speed = 5.0
        weather_data.wind_direction = Mock(name="南")
        weather_data.humidity = 90
        
        weather_trend = Mock()
        weather_trend.get_summary.return_value = "天気は回復傾向"
        
        result = format_weather_info(weather_data, None, weather_trend)
        
        assert "天気変化傾向: 天気は回復傾向" in result
    
    def test_invalid_weather_data(self):
        """不正な天気データの場合"""
        with pytest.raises(ValueError, match="天気データが提供されていません"):
            format_weather_info(None, None, None)
    
    def test_missing_temperature(self):
        """気温データが欠落している場合"""
        weather_data = Mock()
        weather_data.temperature = None
        
        with pytest.raises(ValueError, match="気温データが不足しています"):
            format_weather_info(weather_data, None, None)
    
    def test_partial_temperature_differences(self):
        """一部の気温差情報のみがある場合"""
        weather_data = Mock()
        weather_data.temperature = 20.0
        weather_data.weather_description = "晴れ"
        weather_data.precipitation = 0.0
        weather_data.wind_speed = 2.0
        weather_data.wind_direction = Mock(name="西")
        weather_data.humidity = 60
        
        temp_diffs = {
            "previous_day_diff": 1.5,
            "twelve_hours_ago_diff": None,
            "daily_range": 8.0
        }
        
        result = format_weather_info(weather_data, temp_diffs, None)
        
        assert "前日との気温差: 1.5°C" in result
        assert "12時間前との気温差" not in result
        assert "日較差: 8.0°C" in result