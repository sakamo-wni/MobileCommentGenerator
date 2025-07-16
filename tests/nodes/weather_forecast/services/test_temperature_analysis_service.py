"""TemperatureAnalysisServiceの単体テスト"""

import pytest
from unittest.mock import Mock, patch
from src.nodes.weather_forecast.services.temperature_analysis_service import TemperatureAnalysisService
from src.data.weather_data import WeatherForecast
from datetime import datetime


class TestTemperatureAnalysisService:
    """TemperatureAnalysisServiceのテスト"""
    
    @pytest.fixture
    def service(self):
        """TemperatureAnalysisServiceのインスタンスを作成"""
        return TemperatureAnalysisService()
    
    @pytest.fixture
    def mock_forecast(self):
        """モックの天気予報データを作成"""
        forecast = Mock(spec=WeatherForecast)
        forecast.datetime = datetime(2024, 1, 15, 12, 0)
        forecast.temperature = 20.0
        forecast.weather = "晴れ"
        return forecast
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_calculate_temperature_differences_success(self, mock_get_diffs, service, mock_forecast):
        """気温差計算が成功する場合"""
        # モックの返り値を設定
        expected_diffs = {
            "previous_day_diff": 3.5,
            "twelve_hours_ago_diff": -2.0,
            "daily_range": 10.5
        }
        mock_get_diffs.return_value = expected_diffs
        
        result = service.calculate_temperature_differences(mock_forecast, "東京")
        
        assert result == expected_diffs
        mock_get_diffs.assert_called_once_with(mock_forecast, "東京")
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_calculate_temperature_differences_partial_data(self, mock_get_diffs, service, mock_forecast):
        """一部の気温差データのみが利用可能な場合"""
        # 一部のデータのみを返す
        partial_diffs = {
            "previous_day_diff": 2.0,
            "twelve_hours_ago_diff": None,
            "daily_range": 8.0
        }
        mock_get_diffs.return_value = partial_diffs
        
        result = service.calculate_temperature_differences(mock_forecast, "大阪")
        
        assert result == partial_diffs
        assert result["previous_day_diff"] == 2.0
        assert result["twelve_hours_ago_diff"] is None
        assert result["daily_range"] == 8.0
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_calculate_temperature_differences_empty_data(self, mock_get_diffs, service, mock_forecast):
        """気温差データが空の場合"""
        mock_get_diffs.return_value = {}
        
        result = service.calculate_temperature_differences(mock_forecast, "名古屋")
        
        assert result == {}
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_calculate_temperature_differences_exception(self, mock_get_diffs, service, mock_forecast):
        """例外が発生した場合"""
        mock_get_diffs.side_effect = Exception("API Error")
        
        result = service.calculate_temperature_differences(mock_forecast, "福岡")
        
        # エラーが発生しても空の辞書を返す
        assert result == {}
        mock_get_diffs.assert_called_once_with(mock_forecast, "福岡")
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.logger')
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_logging_with_all_differences(self, mock_get_diffs, mock_logger, service, mock_forecast):
        """全ての気温差がある場合のログ出力"""
        diffs = {
            "previous_day_diff": 2.5,
            "twelve_hours_ago_diff": -1.5,
            "daily_range": 9.0
        }
        mock_get_diffs.return_value = diffs
        
        service.calculate_temperature_differences(mock_forecast, "東京")
        
        # ログ出力を検証
        assert mock_logger.info.call_count == 3
        mock_logger.info.assert_any_call("前日との気温差: 2.5℃")
        mock_logger.info.assert_any_call("12時間前との気温差: -1.5℃")
        mock_logger.info.assert_any_call("日較差: 9.0℃")
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.logger')
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_logging_with_partial_differences(self, mock_get_diffs, mock_logger, service, mock_forecast):
        """一部の気温差のみがある場合のログ出力"""
        diffs = {
            "previous_day_diff": 3.0,
            "twelve_hours_ago_diff": None,
            "daily_range": None
        }
        mock_get_diffs.return_value = diffs
        
        service.calculate_temperature_differences(mock_forecast, "大阪")
        
        # 値がある項目のみログ出力される
        assert mock_logger.info.call_count == 1
        mock_logger.info.assert_called_with("前日との気温差: 3.0℃")
    
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.logger')
    @patch('src.nodes.weather_forecast.services.temperature_analysis_service.get_temperature_differences')
    def test_logging_exception(self, mock_get_diffs, mock_logger, service, mock_forecast):
        """例外発生時のログ出力"""
        error_msg = "Database connection failed"
        mock_get_diffs.side_effect = Exception(error_msg)
        
        service.calculate_temperature_differences(mock_forecast, "京都")
        
        # 警告ログが出力される
        mock_logger.warning.assert_called_once_with(f"気温差の計算に失敗: {error_msg}")