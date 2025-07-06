"""天気データ選択ロジックのテスト"""

import pytest
from datetime import datetime, timedelta
import pytz
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.nodes.weather_forecast.data_validator import WeatherDataValidator


class TestWeatherDataSelection:
    """天気データ選択のテストクラス"""
    
    def setup_method(self):
        """テストのセットアップ"""
        self.validator = WeatherDataValidator()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.base_time = self.jst.localize(datetime(2025, 7, 7, 15, 0))  # 15:00 JST
    
    def create_forecast(self, hour: int, temp: float, weather: str, condition: WeatherCondition) -> WeatherForecast:
        """テスト用の予報データを作成"""
        from src.data.weather_data import WindDirection
        
        dt = self.jst.localize(datetime(2025, 7, 7, hour, 0))
        return WeatherForecast(
            location="テスト地点",
            datetime=dt,
            temperature=temp,
            weather_code="test",
            weather_condition=condition,
            weather_description=weather,
            precipitation=0.0,
            humidity=70,
            wind_speed=2.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        )
    
    def test_select_forecast_by_time_exact_match(self):
        """指定時刻と完全一致する予報の選択"""
        forecasts = [
            self.create_forecast(9, 29.0, "うすぐもり", WeatherCondition.CLOUDY),
            self.create_forecast(12, 33.0, "くもり", WeatherCondition.CLOUDY),
            self.create_forecast(15, 34.0, "くもり", WeatherCondition.CLOUDY),  # ターゲット
            self.create_forecast(18, 30.0, "くもり", WeatherCondition.CLOUDY),
        ]
        
        selected = self.validator.select_forecast_by_time(forecasts, self.base_time)
        
        assert selected.datetime.hour == 15
        assert selected.temperature == 34.0
        assert selected.weather_description == "くもり"
    
    def test_select_forecast_by_time_closest(self):
        """最も近い時刻の予報を選択"""
        target_time = self.jst.localize(datetime(2025, 7, 7, 14, 0))  # 14:00
        
        forecasts = [
            self.create_forecast(9, 29.0, "うすぐもり", WeatherCondition.CLOUDY),
            self.create_forecast(12, 33.0, "くもり", WeatherCondition.CLOUDY),
            self.create_forecast(15, 34.0, "くもり", WeatherCondition.CLOUDY),  # 最も近い
            self.create_forecast(18, 30.0, "くもり", WeatherCondition.CLOUDY),
        ]
        
        selected = self.validator.select_forecast_by_time(forecasts, target_time)
        
        assert selected.datetime.hour == 15  # 14:00に最も近いのは15:00
        assert selected.temperature == 34.0
    
    def test_select_forecast_by_time_with_extreme_heat(self):
        """猛暑日でも指定時刻のデータを選択"""
        forecasts = [
            self.create_forecast(9, 29.0, "晴れ", WeatherCondition.CLEAR),
            self.create_forecast(12, 35.0, "晴れ", WeatherCondition.EXTREME_HEAT),  # 猛暑
            self.create_forecast(15, 34.0, "くもり", WeatherCondition.CLOUDY),  # ターゲット
            self.create_forecast(18, 30.0, "くもり", WeatherCondition.CLOUDY),
        ]
        
        selected = self.validator.select_forecast_by_time(forecasts, self.base_time)
        
        # 35℃の猛暑があっても、15:00が指定されていれば34℃のデータを選択
        assert selected.datetime.hour == 15
        assert selected.temperature == 34.0
        assert selected.weather_description == "くもり"
    
    def test_select_priority_forecast_vs_time_based(self):
        """優先度ベースと時刻ベースの選択の違い"""
        forecasts = [
            self.create_forecast(9, 29.0, "晴れ", WeatherCondition.CLEAR),
            self.create_forecast(12, 35.0, "晴れ", WeatherCondition.EXTREME_HEAT),  # 優先度高
            self.create_forecast(15, 34.0, "くもり", WeatherCondition.CLOUDY),
            self.create_forecast(18, 30.0, "小雨", WeatherCondition.RAIN),
        ]
        
        # 優先度ベースの選択
        priority_selected = self.validator.select_priority_forecast(forecasts)
        assert priority_selected.temperature == 35.0  # 猛暑が選択される
        
        # 時刻ベースの選択
        time_selected = self.validator.select_forecast_by_time(forecasts, self.base_time)
        assert time_selected.temperature == 34.0  # 15:00のデータが選択される
    
    def test_empty_forecast_list(self):
        """空の予報リストでエラー"""
        with pytest.raises(ValueError, match="指定時刻の天気予報データが取得できませんでした"):
            self.validator.select_forecast_by_time([], self.base_time)