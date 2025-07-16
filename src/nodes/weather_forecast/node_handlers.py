"""天気予報ノードのハンドラー関数

fetch_weather_forecast_nodeの処理を責務ごとに分割
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from src.config.config import get_config, get_comment_config
from src.config.config_loader import load_config
from src.nodes.weather_forecast.service_factory import WeatherForecastServiceFactory

logger = logging.getLogger(__name__)


class WeatherForecastNodeHandler:
    """天気予報ノードの処理を管理するハンドラー"""
    
    def __init__(self, service_factory: WeatherForecastServiceFactory | None = None):
        self.service_factory = service_factory
        self._api_key = None
        self._services_initialized = False
    
    def initialize_services(self, state) -> None:
        """サービスの初期化"""
        if self.service_factory is None:
            # APIキーの取得
            self._api_key = os.getenv("WXTECH_API_KEY")
            if not self._api_key:
                error_msg = (
                    "WXTECH_API_KEY環境変数が設定されていません。\n"
                    "設定方法: export WXTECH_API_KEY='your-api-key' または .envファイルに記載"
                )
                logger.error(error_msg)
                state.add_error(error_msg, "weather_forecast")
                raise ValueError(error_msg)
            
            # サービスファクトリーの初期化
            self.service_factory = WeatherForecastServiceFactory()
            self.service_factory.set_api_key(self._api_key)
        
        self._services_initialized = True
    
    def process_location(self, state) -> tuple:
        """地点情報の処理
        
        Returns:
            (location, lat, lon)
        """
        location_service = self.service_factory.get_location_service()
        
        # 地点名と座標を分離
        location_name_raw = state.location_name
        if not location_name_raw:
            raise ValueError("location_name is required")
        
        location_name, provided_lat, provided_lon = location_service.parse_location_string(
            location_name_raw
        )
        
        # 地点情報を取得
        try:
            location = location_service.get_location_with_coordinates(
                location_name, 
                provided_lat, 
                provided_lon
            )
        except ValueError as e:
            logger.error(str(e))
            state.add_error(str(e), "weather_forecast")
            raise
        
        return location, location.latitude, location.longitude
    
    def fetch_weather_data(self, state, lat: float, lon: float, location_name: str) -> Any:
        """天気予報データの取得"""
        # 事前取得した天気データがある場合はそれを使用
        if state.get("pre_fetched_weather"):
            logger.info(f"事前取得した天気データを使用: {location_name}")
            pre_fetched = state.get("pre_fetched_weather")
            forecast_collection = pre_fetched.get("forecast_collection")
            if not forecast_collection:
                error_msg = "事前取得した天気データが不正です"
                logger.error(error_msg)
                state.add_error(error_msg, "weather_forecast")
                raise ValueError(error_msg)
            return forecast_collection
        
        # 通常の天気予報取得
        weather_api_service = self.service_factory.get_weather_api_service()
        try:
            return weather_api_service.fetch_forecast_with_retry(lat, lon, location_name)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"天気予報取得エラー: {error_msg}")
            state.add_error(error_msg, "weather_forecast")
            raise
    
    def process_forecast_data(self, state, forecast_collection, location_name: str) -> tuple:
        """予報データの処理
        
        Returns:
            (selected_forecast, period_forecasts, weather_trend)
        """
        forecast_processing_service = self.service_factory.get_forecast_processing_service()
        
        # 設定の読み込み
        config = get_config()
        weather_config = load_config('weather_thresholds', validate=False)
        date_boundary_hour = weather_config.get('generation', {}).get('date_boundary_hour', 6)
        
        import pytz
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        target_date = forecast_processing_service.get_target_date(now_jst, date_boundary_hour)
        
        logger.info(f"対象日: {target_date} (現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M')})")
        
        # 指定時刻の予報を抽出
        period_forecasts = forecast_processing_service.extract_period_forecasts(
            forecast_collection,
            target_date
        )
        
        # period_forecastsが空でないことを確認
        if not period_forecasts:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(f"{error_msg} - period_forecasts is empty")
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)
        
        # 優先度に基づいて予報を選択
        logger.info("優先度ベースの予報選択を開始")
        selected_forecast = forecast_processing_service.select_priority_forecast(period_forecasts)
        
        if selected_forecast:
            logger.info(
                f"優先度選択結果: {selected_forecast.datetime.strftime('%H:%M')} - "
                f"{selected_forecast.weather_description}, {selected_forecast.temperature}°C, "
                f"降水量{selected_forecast.precipitation}mm"
            )
        else:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)
        
        # 気象変化傾向の分析
        weather_trend = forecast_processing_service.analyze_weather_trend(period_forecasts)
        
        return selected_forecast, period_forecasts, weather_trend
    
    def update_state(self, state, location, selected_forecast, forecast_collection, 
                     period_forecasts, weather_trend, lat: float, lon: float, location_name: str) -> None:
        """状態の更新"""
        # 気温差の計算
        temperature_analysis_service = self.service_factory.get_temperature_analysis_service()
        temperature_differences = temperature_analysis_service.calculate_temperature_differences(
            selected_forecast, 
            location_name
        )
        
        # 状態の更新
        state.weather_data = selected_forecast
        state.update_metadata("forecast_collection", forecast_collection)
        state.location = location
        state.update_metadata("location_coordinates", {"latitude": lat, "longitude": lon})
        state.update_metadata("temperature_differences", temperature_differences)
        
        # 4時点の予報データを保存
        state.update_metadata("period_forecasts", period_forecasts)
        logger.info(f"4時点の予報データを保存: {len(period_forecasts)}件")
        
        # 気象変化傾向を保存
        if weather_trend:
            state.update_metadata("weather_trend", weather_trend)
        
        # デバッグ情報
        logger.info(
            f"Weather forecast fetched for {location_name}: {selected_forecast.weather_description}"
        )


def fetch_weather_forecast_node(
    state,
    service_factory: WeatherForecastServiceFactory | None = None
):
    """ワークフロー用の天気予報取得ノード関数（リファクタリング版）"""
    handler = WeatherForecastNodeHandler(service_factory)
    
    try:
        # 1. サービスの初期化
        handler.initialize_services(state)
        
        # 2. 地点情報の処理
        location, lat, lon = handler.process_location(state)
        
        # 3. 天気予報データの取得
        forecast_collection = handler.fetch_weather_data(state, lat, lon, location.name)
        
        # 4. 予報データの処理
        selected_forecast, period_forecasts, weather_trend = handler.process_forecast_data(
            state, forecast_collection, location.name
        )
        
        # 5. 状態の更新
        handler.update_state(
            state, location, selected_forecast, forecast_collection,
            period_forecasts, weather_trend, lat, lon, location.name
        )
        
        return state
        
    except Exception as e:
        logger.error(f"Failed to fetch weather forecast: {e!s}")
        state.add_error(f"天気予報の取得に失敗しました: {e!s}", "weather_forecast")
        raise