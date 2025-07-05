"""
WxTech API モジュール分割のテスト

新しいモジュール構造が正しく動作することを確認
"""

import pytest
from unittest.mock import MagicMock, patch

from src.apis.wxtech import WxTechAPIClient, WxTechAPIError
from src.apis.wxtech.errors import handle_http_error
from src.apis.wxtech.mappings import convert_weather_code, get_weather_description, convert_wind_direction
from src.apis.wxtech.parser import parse_single_forecast
from src.data.weather_data import WeatherCondition, WindDirection


class TestWxTechErrors:
    """エラーモジュールのテスト"""
    
    def test_wxtech_api_error_creation(self):
        """WxTechAPIErrorが正しく作成されること"""
        error = WxTechAPIError("テストエラー", status_code=404, error_type="not_found")
        assert str(error) == "テストエラー"
        assert error.status_code == 404
        assert error.error_type == "not_found"
    
    def test_handle_http_error_401(self):
        """401エラーのハンドリング"""
        error = handle_http_error(401)
        assert error.status_code == 401
        assert error.error_type == "api_key_invalid"
        assert "APIキーが無効です" in str(error)
    
    def test_handle_http_error_429(self):
        """429エラー（レート制限）のハンドリング"""
        error = handle_http_error(429)
        assert error.status_code == 429
        assert error.error_type == "rate_limit"
        assert "レート制限に達しました" in str(error)
    
    def test_handle_http_error_unknown(self):
        """未知のステータスコードのハンドリング"""
        error = handle_http_error(418)  # I'm a teapot
        assert error.status_code == 418
        assert error.error_type == "http_error"
        assert "ステータスコード 418" in str(error)


class TestWxTechMappings:
    """マッピングモジュールのテスト"""
    
    def test_convert_weather_code_clear(self):
        """晴れの天気コード変換"""
        assert convert_weather_code("100") == WeatherCondition.CLEAR
        assert convert_weather_code("500") == WeatherCondition.CLEAR  # 快晴
    
    def test_convert_weather_code_rain(self):
        """雨の天気コード変換"""
        assert convert_weather_code("300") == WeatherCondition.RAIN
        assert convert_weather_code("306") == WeatherCondition.HEAVY_RAIN  # 大雨
    
    def test_convert_weather_code_snow(self):
        """雪の天気コード変換"""
        assert convert_weather_code("400") == WeatherCondition.SNOW
        assert convert_weather_code("405") == WeatherCondition.HEAVY_SNOW  # 大雪
    
    def test_convert_weather_code_unknown(self):
        """未知の天気コード"""
        assert convert_weather_code("999") == WeatherCondition.UNKNOWN
    
    def test_get_weather_description(self):
        """天気説明の取得"""
        assert get_weather_description("100") == "晴れ"
        assert get_weather_description("300") == "雨"
        assert get_weather_description("400") == "雪"
        assert get_weather_description("999") == "不明"
    
    def test_convert_wind_direction(self):
        """風向き変換"""
        direction, degrees = convert_wind_direction(0)
        assert direction == WindDirection.CALM
        assert degrees == 0
        
        direction, degrees = convert_wind_direction(1)
        assert direction == WindDirection.N
        assert degrees == 0
        
        direction, degrees = convert_wind_direction(2)
        assert direction == WindDirection.NE
        assert degrees == 45
        
        direction, degrees = convert_wind_direction(99)
        assert direction == WindDirection.UNKNOWN
        assert degrees == 0


class TestWxTechParser:
    """パーサーモジュールのテスト"""
    
    def test_parse_single_forecast_hourly(self):
        """時間別予報のパース"""
        test_data = {
            "date": "2024-01-01T12:00:00Z",
            "wx": "100",
            "temp": 15.5,
            "prec": 0.0,
            "rhum": 60.0,
            "wndspd": 5.2,
            "wnddir": 2
        }
        
        forecast = parse_single_forecast(test_data, "東京", is_hourly=True)
        
        assert forecast.location == "東京"
        assert forecast.temperature == 15.5
        assert forecast.weather_code == "100"
        assert forecast.weather_condition == WeatherCondition.CLEAR
        assert forecast.weather_description == "晴れ"
        assert forecast.precipitation == 0.0
        assert forecast.humidity == 60.0
        assert forecast.wind_speed == 5.2
        assert forecast.wind_direction == WindDirection.NE
        assert forecast.wind_direction_degrees == 45
    
    def test_parse_single_forecast_daily(self):
        """日別予報のパース（最高気温使用）"""
        test_data = {
            "date": "2024-01-01T00:00:00Z",
            "wx": "200",
            "maxtemp": 20.0,
            "temp": 15.0,  # 日別では無視される
            "prec": 10.0,
            "rhum": 70.0,
            "wndspd": 3.5,
            "wnddir": 5
        }
        
        forecast = parse_single_forecast(test_data, "大阪", is_hourly=False)
        
        assert forecast.location == "大阪"
        assert forecast.temperature == 20.0  # maxtempが使用される
        assert forecast.weather_code == "200"
        assert forecast.weather_condition == WeatherCondition.CLOUDY
        assert forecast.precipitation == 10.0


class TestBackwardCompatibility:
    """後方互換性のテスト"""
    
    def test_import_from_old_module(self):
        """古いモジュールからのインポートが動作すること"""
        # 警告は出るが、インポートは成功する
        with pytest.warns(DeprecationWarning):
            from src.apis.wxtech_client import WxTechAPIClient as OldClient
            from src.apis.wxtech_client import WxTechAPIError as OldError
        
        # クラスは同じものを参照している
        assert OldClient is WxTechAPIClient
        assert OldError is WxTechAPIError
    
    @patch('src.apis.wxtech.api.WxTechAPI.make_request')
    def test_client_functionality(self, mock_request):
        """クライアントの基本機能が動作すること"""
        # モックレスポンス
        mock_request.return_value = {
            "wxdata": [{
                "srf": [{
                    "date": "2024-01-01T12:00:00Z",
                    "wx": "100",
                    "temp": 15.5,
                    "prec": 0.0,
                    "rhum": 60.0,
                    "wndspd": 5.2,
                    "wnddir": 2
                }],
                "mrf": []
            }]
        }
        
        client = WxTechAPIClient("test_api_key")
        result = client.get_forecast(35.6762, 139.6503)  # 東京
        
        assert result.location == "lat:35.6762,lon:139.6503"
        assert len(result.forecasts) == 1
        assert result.forecasts[0].temperature == 15.5
        assert result.forecasts[0].weather_condition == WeatherCondition.CLEAR