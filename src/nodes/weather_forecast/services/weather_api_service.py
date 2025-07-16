"""
Weather API service for weather forecast node

天気予報API通信を担当するサービス
"""

from __future__ import annotations

import asyncio
import logging
import time
from src.apis.wxtech import WxTechAPIError
from src.apis.wxtech.cached_client import CachedWxTechAPIClient
from src.config.config import get_weather_config
from src.data.weather_data import WeatherForecastCollection
from src.nodes.weather_forecast.constants import (
    API_MAX_RETRIES,
    API_INITIAL_RETRY_DELAY,
    API_RETRY_BACKOFF_MULTIPLIER
)
from src.nodes.weather_forecast.messages import Messages

logger = logging.getLogger(__name__)


class WeatherAPIService:
    """天気予報API通信を担当するサービス"""
    
    def __init__(self, api_key: str):
        self.client = CachedWxTechAPIClient(api_key)
        self.max_retries = API_MAX_RETRIES
        self.initial_retry_delay = API_INITIAL_RETRY_DELAY
        self.weather_config = get_weather_config()
    
    def fetch_forecast_with_retry(
        self, 
        lat: float, 
        lon: float,
        location_name: str
    ) -> WeatherForecastCollection:
        """リトライ機能付きで天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            location_name: 地点名（ログ用）
            
        Returns:
            WeatherForecastCollection
            
        Raises:
            WxTechAPIError: API通信エラー（ネットワークエラー、タイムアウト、サーバーエラー等）
            ValueError: データ取得失敗（空のデータ、無効な地点名等）
        """
        
        retry_delay = self.initial_retry_delay
        forecast_collection = None
        
        for attempt in range(self.max_retries):
            try:
                # 常に最適化版を使用
                logger.info("最適化された予報取得を使用")
                forecast_collection = self.client.get_forecast_for_next_day_hours_optimized(lat, lon)
                
                # forecast_collectionが空でないことを確認
                if forecast_collection and forecast_collection.forecasts:
                    logger.info(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"天気予報データを正常に取得しました。"
                    )
                    return forecast_collection
                else:
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_retries}: "
                            f"天気予報データが空です。{retry_delay}秒後にリトライします。"
                        )
                        time.sleep(retry_delay)
                        retry_delay *= API_RETRY_BACKOFF_MULTIPLIER  # 指数バックオフ
                    else:
                        raise ValueError(
                            f"地点 '{location_name}' の天気予報データが取得できませんでした"
                        )
                        
            except WxTechAPIError as e:
                # リトライ可能なエラーかチェック
                if (e.error_type in ['network_error', 'timeout', 'server_error'] 
                    and attempt < self.max_retries - 1):
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"APIエラー ({e.error_type}). {retry_delay}秒後にリトライします。"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    # リトライ不可能なエラーまたは最後の試行の場合
                    self._handle_api_error(e)
                    raise
        
        raise ValueError("予期しないエラー: リトライループが正常に終了しませんでした")
    
    async def fetch_forecast_with_retry_async(
        self, 
        lat: float, 
        lon: float,
        location_name: str
    ) -> WeatherForecastCollection:
        """非同期版: リトライ機能付きで天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            location_name: 地点名（ログ用）
            
        Returns:
            WeatherForecastCollection
            
        Raises:
            WxTechAPIError: API通信エラー（ネットワークエラー、タイムアウト、サーバーエラー等）
            ValueError: データ取得失敗（空のデータ、無効な地点名等）
        """
        
        retry_delay = self.initial_retry_delay
        forecast_collection = None
        
        for attempt in range(self.max_retries):
            try:
                # 最適化版の使用を判定
                if self.weather_config.use_optimized_forecast:
                    logger.info("最適化された予報取得を使用")
                    # 非同期版メソッドを呼び出し
                    forecast_collection = await self.client.get_forecast_for_next_day_hours_optimized_async(lat, lon)
                else:
                    # 通常の非同期版メソッド
                    forecast_collection = await self.client.get_forecast_async(lat, lon)
                
                # 予報データがある場合
                if forecast_collection and forecast_collection.forecasts:
                    logger.info(
                        f"🌤️ {location_name} の天気予報を取得しました。"
                        f"データ数: {len(forecast_collection.forecasts)}"
                    )
                    break
                else:
                    # データが取得できなかった場合、リトライするかチェック
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_retries}: "
                            f"天気データが空です。{retry_delay}秒後にリトライします。"
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                        continue
                    else:
                        raise ValueError(
                            f"地点 '{location_name}' の天気予報データが取得できませんでした"
                        )
                        
            except WxTechAPIError as e:
                # リトライ可能なエラーかチェック
                if (e.error_type in ['network_error', 'timeout', 'server_error'] 
                    and attempt < self.max_retries - 1):
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"APIエラー ({e.error_type}). {retry_delay}秒後にリトライします。"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    # リトライ不可能なエラーまたは最後の試行の場合
                    self._handle_api_error(e)
                    raise
        
        raise ValueError("予期しないエラー: リトライループが正常に終了しませんでした")
    
    def _handle_api_error(self, error: WxTechAPIError) -> str:
        """APIエラーを処理してユーザー向けメッセージを生成
        
        Args:
            error: WxTechAPIError
            
        Returns:
            エラーメッセージ
        """
        error_msg = Messages.get_api_error(
            error.error_type or 'unknown',
            error=error
        )
        logger.error(
            f"気象APIエラー (type: {error.error_type}, status: {error.status_code}): {error_msg}"
        )
        return error_msg