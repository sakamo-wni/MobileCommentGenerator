"""
天気予報データ取得モジュール

WxTech APIを使用して天気予報データを取得する機能を提供
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

import pytz

from src.apis.wxtech import WxTechAPIClient, WxTechAPIError
from src.config.weather_settings import WeatherConfig
from src.data.location_manager import Location, LocationManager
from src.data.weather_data import WeatherForecast, WeatherForecastCollection

logger = logging.getLogger(__name__)


class WeatherDataFetcher:
    """天気予報データ取得クラス"""
    
    def __init__(self, api_key: str):
        """初期化
        
        Args:
            api_key: WxTech API キー
        """
        self.api_key = api_key
        self.location_manager = LocationManager()
        self.weather_config = WeatherConfig()
    
    async def fetch_weather_data(
        self,
        location: Union[str, Tuple[float, float]],
    ) -> Optional[WeatherForecastCollection]:
        """天気予報データを取得
        
        Args:
            location: 地点名または(緯度, 経度)のタプル
            
        Returns:
            天気予報コレクション
        """
        try:
            with WxTechAPIClient(self.api_key) as client:
                if isinstance(location, str):
                    # 地点名から座標を取得
                    location_obj = self.location_manager.find_exact_match(location)
                    if not location_obj or location_obj.latitude is None or location_obj.longitude is None:
                        # 地点検索を試行
                        search_results = self.location_manager.search_location(location)
                        if search_results:
                            location_obj = search_results[0]
                        else:
                            raise ValueError(f"地点「{location}」が見つかりません")
                    
                    # 翌日9, 12, 15, 18時JSTのみ取得
                    if self.weather_config.use_optimized_forecast:
                        logger.info("最適化された予報取得を使用")
                        return client.get_forecast_for_next_day_hours_optimized(
                            location_obj.latitude,
                            location_obj.longitude
                        )
                    else:
                        return client.get_forecast_for_next_day_hours(
                            location_obj.latitude,
                            location_obj.longitude
                        )
                
                if isinstance(location, tuple) and len(location) == 2:
                    # 緯度経度から直接取得
                    lat, lon = location
                    # 翌日9, 12, 15, 18時JSTのみ取得
                    if self.weather_config.use_optimized_forecast:
                        logger.info("最適化された予報取得を使用")
                        return client.get_forecast_for_next_day_hours_optimized(lat, lon)
                    else:
                        return client.get_forecast_for_next_day_hours(lat, lon)
                
                raise ValueError("無効な地点情報です")
                
        except WxTechAPIError as e:
            logger.error(f"WxTech API エラー: {e!s}")
            raise
        except Exception as e:
            logger.error(f"天気予報データ取得エラー: {e!s}")
            raise
    
    def fetch_for_workflow(
        self,
        location_name: str,
        provided_lat: Optional[float] = None,
        provided_lon: Optional[float] = None,
    ) -> Tuple[WeatherForecastCollection, Location]:
        """ワークフロー用の天気予報データ取得（同期版）
        
        Args:
            location_name: 地点名
            provided_lat: 提供された緯度（オプション）
            provided_lon: 提供された経度（オプション）
            
        Returns:
            天気予報コレクションと地点情報のタプル
            
        Raises:
            ValueError: 地点が見つからない場合
            WxTechAPIError: API接続エラー
        """
        # LocationManagerから地点データを取得
        from src.data.location_manager import get_location_manager
        
        location_manager = get_location_manager()
        location = location_manager.get_location(location_name)
        
        # LocationManagerで見つからない場合、提供された座標を使用
        if not location and provided_lat is not None and provided_lon is not None:
            logger.info(
                f"Location '{location_name}' not found in LocationManager, using provided coordinates",
            )
            # 疑似Locationオブジェクトを作成
            location = Location(
                name=location_name,
                normalized_name=location_name.lower(),
                latitude=provided_lat,
                longitude=provided_lon,
            )
        elif not location:
            error_msg = f"地点が見つかりません: {location_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not location.latitude or not location.longitude:
            error_msg = f"地点 '{location_name}' の緯度経度情報がありません"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        lat, lon = location.latitude, location.longitude
        
        # WxTech APIクライアントの初期化
        with WxTechAPIClient(self.api_key) as client:
            # 天気予報の取得（翌日9, 12, 15, 18時JSTのみ）
            try:
                if self.weather_config.use_optimized_forecast:
                    logger.info("最適化された予報取得を使用")
                    forecast_collection = client.get_forecast_for_next_day_hours_optimized(lat, lon)
                else:
                    forecast_collection = client.get_forecast_for_next_day_hours(lat, lon)
                return forecast_collection, location
            except WxTechAPIError as e:
                # エラータイプに基づいて適切なエラーメッセージを設定
                if e.error_type == 'api_key_invalid':
                    error_msg = "気象APIキーが無効です。\nWXTECH_API_KEYが正しく設定されているか確認してください。"
                elif e.error_type == 'rate_limit':
                    error_msg = "気象APIのレート制限に達しました。しばらく待ってから再試行してください。"
                elif e.error_type == 'network_error':
                    error_msg = "気象APIサーバーに接続できません。ネットワーク接続を確認してください。"
                elif e.error_type == 'timeout':
                    error_msg = f"気象APIへのリクエストがタイムアウトしました: {e}"
                elif e.error_type == 'server_error':
                    error_msg = "気象APIサーバーでエラーが発生しました。しばらく待ってから再試行してください。"
                else:
                    error_msg = f"気象API接続エラー: {e}"
                
                logger.error(f"気象APIエラー (type: {e.error_type}, status: {e.status_code}): {error_msg}")
                raise WxTechAPIError(error_msg, e.error_type, e.status_code)
    
    def extract_period_forecasts(
        self,
        forecast_collection: WeatherForecastCollection,
        target_date: datetime.date,
        target_hours: list[int] = [9, 12, 15, 18],
    ) -> list[WeatherForecast]:
        """指定日の指定時刻の予報を抽出
        
        Args:
            forecast_collection: 天気予報コレクション
            target_date: 対象日
            target_hours: 対象時刻のリスト（デフォルト: [9, 12, 15, 18]）
            
        Returns:
            抽出された予報のリスト
        """
        # JST タイムゾーンの設定
        jst = pytz.timezone("Asia/Tokyo")
        
        # 対象時刻のリスト
        target_times = [
            jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour))) 
            for hour in target_hours
        ]
        
        # 各対象時刻に最も近い予報を抽出
        period_forecasts = []
        for target_time in target_times:
            closest_forecast = None
            min_diff = float('inf')
            
            for forecast in forecast_collection.forecasts:
                # forecastのdatetimeがnaiveな場合はJSTとして扱う
                forecast_dt = forecast.datetime
                if forecast_dt.tzinfo is None:
                    forecast_dt = jst.localize(forecast_dt)
                
                # 目標時刻との差を計算
                diff = abs((forecast_dt - target_time).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_forecast = forecast
            
            if closest_forecast:
                period_forecasts.append(closest_forecast)
        
        return period_forecasts