"""
天気データクラスのテスト
"""

import pytest
from datetime import datetime, timezone
from src.data.weather_data import (
    WeatherCondition,
    WindDirection,
    WeatherForecast,
    WeatherForecastCollection,
)


def create_weather_forecast(
    location_id="東京",
    datetime_val=None,
    temperature=20.0,
    weather_condition=WeatherCondition.CLEAR,
    weather_description="晴れ",
    humidity=50.0,
    precipitation=0.0,
    wind_speed=5.0,
    wind_direction=WindDirection.NORTH,
    **kwargs
):
    """テスト用のWeatherForecastを作成するヘルパー関数"""
    if datetime_val is None:
        datetime_val = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    
    return WeatherForecast(
        location_id=location_id,
        datetime=datetime_val,
        temperature=temperature,
        feels_like=kwargs.get("feels_like", temperature),
        humidity=humidity,
        pressure=kwargs.get("pressure", 1013.25),
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        weather_condition=weather_condition,
        weather_description=weather_description,
        precipitation=precipitation,
        cloud_coverage=kwargs.get("cloud_coverage", 0.0),
        visibility=kwargs.get("visibility", 10.0),
        uv_index=kwargs.get("uv_index", 0.0),
        raw_data=kwargs.get("raw_data", {}),
    )


class TestWeatherForecast:
    """WeatherForecast クラスのテスト"""

    def test_weather_forecast_initialization(self):
        """天気予報オブジェクトの初期化テスト"""
        forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            temperature=20.5,
            feels_like=20.5,
            humidity=50.0,
            pressure=1013.25,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
        )

        assert forecast.location_id == "東京"
        assert forecast.temperature == 20.5
        assert forecast.weather_condition == WeatherCondition.CLEAR
        assert forecast.weather_description == "晴れ"
        assert forecast.precipitation == 0.0

    def test_weather_forecast_validation(self):
        """天気予報データの妥当性検証テスト"""
        # 異常な気温
        with pytest.raises(ValueError, match="気温が範囲外"):
            WeatherForecast(
                location_id="東京",
                datetime=datetime.now(timezone.utc),
                temperature=100.0,  # 異常な気温
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
            )

        # 異常な湿度
        with pytest.raises(ValueError, match="湿度が範囲外"):
            WeatherForecast(
                location_id="東京",
                datetime=datetime.now(timezone.utc),
                temperature=20.0,
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
                humidity=150.0,  # 異常な湿度
            )

        # 負の降水量
        with pytest.raises(ValueError, match="降水量が負の値"):
            WeatherForecast(
                location_id="東京",
                datetime=datetime.now(timezone.utc),
                temperature=20.0,
                    weather_condition=WeatherCondition.RAIN,
                weather_description="雨",
                precipitation=-5.0,  # 負の降水量
            )

    def test_is_good_weather(self):
        """良い天気判定のテスト"""
        # 晴れの場合
        clear_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=22.0,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
        )
        assert clear_forecast.is_good_weather() is True

        # 雨の場合
        rainy_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=15.0,
            weather_condition=WeatherCondition.RAIN,
            weather_description="雨",
            precipitation=10.0,
        )
        assert rainy_forecast.is_good_weather() is False

    def test_is_severe_weather(self):
        """悪天候判定のテスト"""
        # 通常の天気
        normal_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=20.0,
            weather_condition=WeatherCondition.CLOUDY,
            weather_description="曇り",
        )
        assert normal_forecast.is_severe_weather() is False

        # 嵐
        storm_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=15.0,
            weather_condition=WeatherCondition.STORM,
            weather_description="嵐",
            wind_speed=25.0,
            precipitation=50.0,
        )
        assert storm_forecast.is_severe_weather() is True

        # 大雨
        heavy_rain_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=18.0,
            weather_condition=WeatherCondition.HEAVY_RAIN,
            weather_description="大雨",
            precipitation=30.0,
        )
        assert heavy_rain_forecast.is_severe_weather() is True

    def test_get_comfort_level(self):
        """快適度判定のテスト"""
        # 快適な条件
        comfortable_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=22.0,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            humidity=50.0,
        )
        assert comfortable_forecast.get_comfort_level() == "快適"

        # 暑い条件
        hot_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=32.0,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            humidity=70.0,
        )
        assert hot_forecast.get_comfort_level() == "不快"

        # 寒い条件
        cold_forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime.now(timezone.utc),
            temperature=5.0,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
        )
        assert cold_forecast.get_comfort_level() == "寒い"

    def test_to_dict(self):
        """辞書変換のテスト"""
        forecast = WeatherForecast(
            location_id="東京",
            datetime=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            temperature=20.0,
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=50.0,
            wind_speed=5.0,
            wind_direction=WindDirection.NORTH,
        )

        result_dict = forecast.to_dict()

        assert result_dict["location_id"] == "東京"
        assert result_dict["temperature"] == 20.0
        assert result_dict["weather_condition"] == "CLEAR"
        assert result_dict["weather_description"] == "晴れ"
        assert result_dict["precipitation"] == 0.0
        assert result_dict["humidity"] == 50.0
        assert result_dict["wind_speed"] == 5.0
        assert result_dict["wind_direction"] == "N"


class TestWeatherForecastCollection:
    """WeatherForecastCollection クラスのテスト"""

    def test_collection_initialization(self):
        """コレクション初期化のテスト"""
        forecasts = [
            WeatherForecast(
                location_id="東京",
                datetime=datetime(2024, 1, 1, i, 0, tzinfo=timezone.utc),
                temperature=20.0 + i,
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
            )
            for i in range(3)
        ]

        collection = WeatherForecastCollection(location_id="東京", forecasts=forecasts)

        assert collection.location_id == "東京"
        assert len(collection.forecasts) == 3
        assert collection.created_at is not None

    def test_get_current_forecast(self):
        """現在の予報取得テスト"""
        now = datetime.now(timezone.utc)
        forecasts = [
            WeatherForecast(
                location_id="東京",
                datetime=now.replace(hour=h),
                temperature=20.0,
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
            )
            for h in range(0, 24, 3)
        ]

        collection = WeatherForecastCollection(location_id="東京", forecasts=forecasts)

        current = collection.get_current_forecast()
        assert current is not None
        # 現在時刻に最も近い予報が返される

    def test_get_daily_summary(self):
        """日次サマリー取得テスト"""
        forecasts = [
            WeatherForecast(
                location_id="東京",
                datetime=datetime(2024, 1, 1, h, 0, tzinfo=timezone.utc),
                temperature=15.0 + (h / 2),  # 温度変化
                weather_condition=WeatherCondition.CLEAR if h < 12 else WeatherCondition.CLOUDY,
                weather_description="晴れ" if h < 12 else "曇り",
                precipitation=0.0 if h < 18 else 5.0,
            )
            for h in range(24)
        ]

        collection = WeatherForecastCollection(location_id="東京", forecasts=forecasts)

        summary = collection.get_daily_summary()

        assert "max_temperature" in summary
        assert "min_temperature" in summary
        assert "total_precipitation" in summary
        assert summary["max_temperature"] > summary["min_temperature"]
        assert summary["total_precipitation"] > 0

    def test_filter_by_time_range(self):
        """時間範囲フィルタリングテスト"""
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        forecasts = [
            WeatherForecast(
                location_id="東京",
                datetime=base_time.replace(hour=h),
                temperature=20.0,
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
            )
            for h in range(24)
        ]

        collection = WeatherForecastCollection(location_id="東京", forecasts=forecasts)

        # 6時間分をフィルタリング
        start_time = base_time.replace(hour=6)
        end_time = base_time.replace(hour=12)
        filtered = collection.filter_by_time_range(start_time, end_time)

        assert len(filtered.forecasts) == 6
        assert all(start_time <= f.datetime < end_time for f in filtered.forecasts)

    def test_to_dict(self):
        """コレクションの辞書変換テスト"""
        forecasts = [
            WeatherForecast(
                location_id="東京",
                datetime=datetime(2024, 1, 1, i, 0, tzinfo=timezone.utc),
                temperature=20.0,
                    weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
            )
            for i in range(3)
        ]

        collection = WeatherForecastCollection(location_id="東京", forecasts=forecasts)

        result_dict = collection.to_dict()

        assert result_dict["location_id"] == "東京"
        assert len(result_dict["forecasts"]) == 3
        assert "created_at" in result_dict
        assert "summary" in result_dict
