"""weather_modelsのテスト"""

import pytest
from datetime import datetime
import warnings
from src.data.weather_models import WeatherForecast
from src.data.weather_enums import WeatherCondition, WindDirection


class TestWeatherForecast:
    """WeatherForecastクラスのテスト"""
    
    def test_valid_creation(self):
        """正常なインスタンス作成"""
        now = datetime.now()
        forecast = WeatherForecast(
            location_id="tokyo",
            datetime=now,
            temperature=25.0,
            feels_like=26.0,
            humidity=60.0,
            pressure=1013.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0
        )
        assert forecast.location_id == "tokyo"
        assert forecast.temperature == 25.0
        assert forecast.is_comfortable_temperature is True
    
    def test_temperature_out_of_range(self):
        """温度が範囲外の場合のエラー"""
        now = datetime.now()
        with pytest.raises(ValueError) as exc_info:
            WeatherForecast(
                location_id="tokyo",
                datetime=now,
                temperature=100.0,  # 範囲外
                feels_like=26.0,
                humidity=60.0,
                pressure=1013.0,
                wind_speed=5.0,
                wind_direction=WindDirection.NORTH,
                weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ"
            )
        assert "-50.0°C - 60.0°C" in str(exc_info.value)
    
    def test_location_backward_compatibility(self):
        """locationプロパティの後方互換性"""
        now = datetime.now()
        forecast = WeatherForecast(
            location_id="tokyo",
            datetime=now,
            temperature=25.0,
            feels_like=26.0,
            humidity=60.0,
            pressure=1013.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ"
        )
        
        # DeprecationWarningが発生することを確認
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            location = forecast.location
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "location_id" in str(w[0].message)
        
        assert location == "tokyo"
    
    def test_weather_code_backward_compatibility(self):
        """weather_codeプロパティの後方互換性"""
        now = datetime.now()
        forecast = WeatherForecast(
            location_id="tokyo",
            datetime=now,
            temperature=25.0,
            feels_like=26.0,
            humidity=60.0,
            pressure=1013.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=WeatherCondition.RAIN,
            weather_description="雨"
        )
        
        # DeprecationWarningが発生することを確認
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            code = forecast.weather_code
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "weather_condition" in str(w[0].message)
        
        assert code == 300  # RAINのコード
    
    def test_is_rainy(self):
        """雨天判定のテスト"""
        now = datetime.now()
        rain_forecast = WeatherForecast(
            location_id="tokyo",
            datetime=now,
            temperature=20.0,
            feels_like=19.0,
            humidity=80.0,
            pressure=1010.0,
            wind_speed=3.0,
            wind_direction=WindDirection.EAST,
            weather_condition=WeatherCondition.RAIN,
            weather_description="雨",
            precipitation=5.0
        )
        assert rain_forecast.is_rainy is True
        
        clear_forecast = WeatherForecast(
            location_id="tokyo",
            datetime=now,
            temperature=25.0,
            feels_like=26.0,
            humidity=60.0,
            pressure=1013.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0
        )
        assert clear_forecast.is_rainy is False