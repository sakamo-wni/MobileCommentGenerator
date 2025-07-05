"""
WxTech APIクライアントのテスト
"""

import pytest
import asyncio
import warnings
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.apis.wxtech_client import WxTechAPIClient, WxTechAPIError
from src.data.weather_data import WeatherCondition, WindDirection
from src.data.location_manager import Location


class TestWxTechAPIClient:
    """WxTechAPIClient クラスのテスト"""

    def test_client_initialization(self):
        """クライアント初期化のテスト"""
        client = WxTechAPIClient("test_api_key")

        assert client.api_key == "test_api_key"
        assert WxTechAPIClient.BASE_URL == "https://wxtech.weathernews.com/openapi/v1"
        assert client.timeout == 30
        assert client.session is not None

    def test_client_initialization_with_custom_params(self):
        """カスタムパラメータでの初期化テスト"""
        client = WxTechAPIClient(api_key="test_key", timeout=60)

        assert client.api_key == "test_key"
        assert client.timeout == 60
        assert client._min_request_interval == 0.1

    @patch("requests.Session.get")
    def test_successful_api_request(self, mock_get):
        """正常なAPIリクエストのテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "wxdata": [
                {
                    "srf": [
                        {
                            "date": "2025-06-05T12:00:00Z",
                            "wx": "100",
                            "temp": 25.0,
                            "prec": 0.0,
                            "rhum": 60.0,
                            "wndspd": 5.0,
                            "wnddir": 1,
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        client = WxTechAPIClient("test_api_key")

        # APIリクエストを実行
        result = client._make_request("ss1wx", {"lat": 35.6762, "lon": 139.6503})

        assert "wxdata" in result
        assert len(result["wxdata"]) > 0

    @patch("requests.Session.get")
    def test_api_error_handling(self, mock_get):
        """APIエラーハンドリングのテスト"""
        # 401エラーのテスト
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_get.return_value = mock_response

        client = WxTechAPIClient("invalid_api_key")

        with pytest.raises(WxTechAPIError, match="認証エラー"):
            client._make_request("ss1wx", {"lat": 35.6762, "lon": 139.6503})

    @patch("requests.Session.get")
    def test_rate_limit_error(self, mock_get):
        """レート制限エラーのテスト"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.ok = False
        mock_get.return_value = mock_response

        client = WxTechAPIClient("test_api_key")

        with pytest.raises(WxTechAPIError, match="レート制限"):
            client._make_request("ss1wx", {"lat": 35.6762, "lon": 139.6503})

    def test_invalid_coordinates(self):
        """無効な座標値のテスト"""
        client = WxTechAPIClient("test_api_key")

        # 緯度が範囲外
        with pytest.raises(ValueError, match="緯度が範囲外"):
            client.get_forecast(100.0, 139.6503)

        # 経度が範囲外
        with pytest.raises(ValueError, match="経度が範囲外"):
            client.get_forecast(35.6762, 200.0)

    @patch.object(WxTechAPIClient, "_make_request")
    def test_forecast_parsing(self, mock_make_request):
        """予報データ解析のテスト"""
        # モックデータの設定
        mock_make_request.return_value = {
            "wxdata": [
                {
                    "srf": [
                        {
                            "date": "2025-06-05T12:00:00Z",
                            "wx": "100",
                            "temp": 25.0,
                            "prec": 0.0,
                            "rhum": 60.0,
                            "wndspd": 5.0,
                            "wnddir": 1,
                        }
                    ]
                }
            ]
        }

        client = WxTechAPIClient("test_api_key")
        forecast_collection = client.get_forecast(35.6762, 139.6503)

        assert forecast_collection.location == "lat:35.6762,lon:139.6503"
        assert len(forecast_collection.forecasts) == 1

        forecast = forecast_collection.forecasts[0]
        assert forecast.temperature == 25.0
        assert forecast.weather_condition == WeatherCondition.CLEAR
        assert forecast.wind_direction == WindDirection.N

    @patch.object(WxTechAPIClient, "_make_request")
    def test_forecast_by_location(self, mock_make_request):
        """Location オブジェクトでの予報取得テスト"""
        mock_make_request.return_value = {
            "wxdata": [
                {
                    "srf": [
                        {
                            "date": "2025-06-05T12:00:00Z",
                            "wx": "100",
                            "temp": 20.0,
                            "prec": 0.0,
                            "rhum": 50.0,
                            "wndspd": 3.0,
                            "wnddir": 2,
                        }
                    ]
                }
            ]
        }

        client = WxTechAPIClient("test_api_key")

        # Location オブジェクトを作成
        tokyo = Location(name="東京", normalized_name="東京", latitude=35.6762, longitude=139.6503)

        forecast_collection = client.get_forecast_by_location(tokyo)

        assert forecast_collection.location == "東京"
        assert len(forecast_collection.forecasts) == 1

    def test_forecast_by_location_without_coordinates(self):
        """座標なしLocationでのエラーテスト"""
        client = WxTechAPIClient("test_api_key")

        # 座標なしのLocation
        location_without_coords = Location(name="未知の地点", normalized_name="未知の地点")

        with pytest.raises(ValueError, match="緯度経度情報がありません"):
            client.get_forecast_by_location(location_without_coords)

    def test_weather_code_conversion(self):
        """天気コード変換のテスト"""
        client = WxTechAPIClient("test_api_key")

        # 晴れ
        assert client._convert_weather_code("100") == WeatherCondition.CLEAR
        # 曇り
        assert client._convert_weather_code("200") == WeatherCondition.CLOUDY
        # 雨
        assert client._convert_weather_code("300") == WeatherCondition.RAIN
        # 雪
        assert client._convert_weather_code("400") == WeatherCondition.SNOW
        # 不明
        assert client._convert_weather_code("999") == WeatherCondition.UNKNOWN

    def test_wind_direction_conversion(self):
        """風向き変換のテスト"""
        client = WxTechAPIClient("test_api_key")

        # 北
        direction, degrees = client._convert_wind_direction(1)
        assert direction == WindDirection.N
        assert degrees == 0

        # 東
        direction, degrees = client._convert_wind_direction(3)
        assert direction == WindDirection.E
        assert degrees == 90

        # 無風
        direction, degrees = client._convert_wind_direction(0)
        assert direction == WindDirection.CALM
        assert degrees == 0

        # 不明
        direction, degrees = client._convert_wind_direction(99)
        assert direction == WindDirection.UNKNOWN
        assert degrees == 0

    def test_context_manager(self):
        """コンテキストマネージャーのテスト"""
        with WxTechAPIClient("test_api_key") as client:
            assert client.api_key == "test_api_key"
            assert client.session is not None

        # コンテキスト終了後はセッションが閉じられる
        # （実際のテストではmockが必要）


class TestAsyncFunctions:
    """非同期関数のテスト"""

    @pytest.mark.asyncio
    @patch.object(WxTechAPIClient, "get_forecast")
    async def test_async_forecast(self, mock_get_forecast):
        """非同期予報取得のテスト"""
        from src.apis.wxtech_client import get_japan_1km_mesh_weather_forecast

        # モックの設定
        mock_forecast_collection = Mock()
        mock_forecast_collection.to_dict.return_value = {
            "location": "東京",
            "forecasts": [],
            "summary": {},
        }
        mock_get_forecast.return_value = mock_forecast_collection

        # 非同期関数のテスト
        result = await get_japan_1km_mesh_weather_forecast(35.6762, 139.6503, "test_api_key")

        assert "location" in result
        assert result["location"] == "東京"


class TestModuleImports:
    """モジュールインポートのテスト"""

    def test_wxtech_module_import(self):
        """新しいモジュール構造のインポートテスト"""
        from src.apis.wxtech import WxTechAPIClient, WxTechAPIError
        assert WxTechAPIClient is not None
        assert WxTechAPIError is not None

    def test_deprecated_import_warning(self):
        """非推奨インポートの警告テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # 既にインポート済みなので、モジュールを再読み込み
            import importlib
            import src.apis.wxtech_client
            importlib.reload(src.apis.wxtech_client)
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "非推奨" in str(w[0].message)


if __name__ == "__main__":
    pytest.main([__file__])
