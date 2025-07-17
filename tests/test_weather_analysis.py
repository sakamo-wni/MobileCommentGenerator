"""weather_analysisのテスト"""

import pytest
from datetime import datetime, timedelta
from src.data.weather_models import WeatherForecast
from src.data.weather_collection import WeatherForecastCollection
from src.data.weather_enums import WeatherCondition, WindDirection
from src.data.weather_analysis import (
    analyze_weather_trend,
    detect_weather_changes,
    WeatherTrendResult
)


class TestWeatherAnalysis:
    """天気分析関数のテスト"""
    
    def create_forecast(self, hours_ahead: int, temperature: float, 
                       condition: WeatherCondition = WeatherCondition.CLEAR,
                       precipitation: float = 0.0) -> WeatherForecast:
        """テスト用の予報データを作成"""
        return WeatherForecast(
            location_id="test",
            datetime=datetime.now() + timedelta(hours=hours_ahead),
            temperature=temperature,
            feels_like=temperature,
            humidity=60.0,
            pressure=1013.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=condition,
            weather_description=condition.get_japanese_name(),
            precipitation=precipitation
        )
    
    def test_analyze_weather_trend_rising_temperature(self):
        """気温上昇トレンドの分析"""
        forecasts = [
            self.create_forecast(0, 20.0),
            self.create_forecast(3, 23.0),
            self.create_forecast(6, 26.0),
            self.create_forecast(9, 28.0),
        ]
        collection = WeatherForecastCollection(forecasts)
        
        result = analyze_weather_trend(collection, hours=12)
        
        assert isinstance(result, dict)  # TypedDictは実行時はdictとして扱われる
        assert result["temperature_trend"] == "rising"
        assert result["min_temperature"] == 20.0
        assert result["max_temperature"] == 28.0
        assert result["precipitation_risk"] == "low"
        assert result["extreme_weather_risk"] is False
    
    def test_analyze_weather_trend_with_rain(self):
        """雨を含むトレンドの分析"""
        forecasts = [
            self.create_forecast(0, 22.0, WeatherCondition.CLEAR),
            self.create_forecast(3, 21.0, WeatherCondition.RAIN, 5.0),
            self.create_forecast(6, 20.0, WeatherCondition.RAIN, 10.0),
            self.create_forecast(9, 19.0, WeatherCondition.HEAVY_RAIN, 20.0),
        ]
        collection = WeatherForecastCollection(forecasts)
        
        result = analyze_weather_trend(collection, hours=12)
        
        assert result["precipitation_risk"] == "high"
        assert result["trend"] == "unstable"
        assert result["total_precipitation"] == 35.0
    
    def test_detect_weather_changes(self):
        """天気変化の検出"""
        forecasts = [
            self.create_forecast(0, 20.0, WeatherCondition.CLEAR),
            self.create_forecast(1, 20.5, WeatherCondition.CLOUDY),  # 天気変化
            self.create_forecast(2, 24.0, WeatherCondition.CLOUDY),  # 気温急変
        ]
        collection = WeatherForecastCollection(forecasts)
        
        changes = detect_weather_changes(collection, hours_ahead=3)
        
        assert len(changes) >= 2
        # 天気の変化
        weather_changes = [c for c in changes if "晴れ → 曇り" in c[1]]
        assert len(weather_changes) == 1
        # 気温の変化
        temp_changes = [c for c in changes if "気温上昇" in c[1]]
        assert len(temp_changes) == 1
    
    def test_empty_collection(self):
        """空のコレクションの処理"""
        collection = WeatherForecastCollection([])
        
        result = analyze_weather_trend(collection)
        
        assert result["trend"] == "unknown"
        assert result["data_points"] == 0
        assert result["min_temperature"] is None
        assert result["max_temperature"] is None