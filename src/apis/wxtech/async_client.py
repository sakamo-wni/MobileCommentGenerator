"""
非同期版 WxTech API クライアント

aiohttpを使用した真の非同期実装
"""

import asyncio
import logging
import os
from typing import Optional, Any
from datetime import datetime, timedelta
from functools import wraps

import aiohttp
import pytz

from src.apis.wxtech.parser import parse_forecast_response
from src.apis.wxtech.errors import WxTechAPIError
from src.data.weather_data import WeatherForecastCollection
from src.config.config import get_config
from src.utils.cache import TTLCache, generate_cache_key, async_cached_method
from src.types.api_types import CachedWxTechParams

logger = logging.getLogger(__name__)


class AsyncWxTechAPIClient:
    """非同期版 WxTech API クライアント"""
    
    def __init__(self, api_key: str, enable_cache: bool = True):
        self.api_key = api_key
        self.base_url = "https://wxtech-api.weathernews.com/api/v1"
        self.session: aiohttp.ClientSession | None = None
        self.config = get_config()
        self.max_retries = 3
        self.retry_delay = 1.0  # 初期リトライ遅延（秒）
        
        # キャッシュの設定
        if enable_cache:
            cache_ttl = int(os.environ.get("WXTECH_CACHE_TTL", "300"))
            self._cache = TTLCache(default_ttl=cache_ttl)
            logger.info(f"非同期 WxTech APIキャッシュを有効化 (TTL: {cache_ttl}秒)")
        else:
            self._cache = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        # 接続数制限を設定
        connector = aiohttp.TCPConnector(
            limit=10,  # 全体の最大接続数
            limit_per_host=5  # ホストごとの最大接続数
        )
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
    @async_cached_method(ttl=600)  # 10分間キャッシュ
    async def get_forecast_optimized(self, lat: float, lon: float) -> WeatherForecastCollection:
        """最適化された翌日予報の非同期取得
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            天気予報コレクション
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        target_date = now_jst.date() + timedelta(days=1)
        
        # 翌日8時から19時までの12時間分を確実に取得
        tomorrow_8am = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=8)))
        hours_to_8am = (tomorrow_8am - now_jst).total_seconds() / 3600
        
        if hours_to_8am > 0:
            forecast_hours = int(hours_to_8am) + 12
        else:
            tomorrow_7pm = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=19)))
            hours_to_7pm = (tomorrow_7pm - now_jst).total_seconds() / 3600
            forecast_hours = max(int(hours_to_7pm) + 1, 1)
        
        # 非同期でAPIを呼び出し
        return await self._fetch_forecast_async(lat, lon, forecast_hours)
    
    async def get_forecast_with_cached_params(self, params: CachedWxTechParams) -> WeatherForecastCollection:
        """事前計算されたキャッシュキーを使用して天気予報を取得
        
        Args:
            params: 事前計算されたキャッシュキー付きパラメータ
            
        Returns:
            天気予報コレクション
        """
        # キャッシュから取得を試みる
        if self._cache:
            cached_result = self._cache.get(params.cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit with pre-computed key: {params.cache_key}")
                return cached_result
        
        # キャッシュにない場合はAPIを呼び出し
        result = await self._fetch_forecast_async(params.lat, params.lon, params.hours)
        
        # キャッシュに保存
        if self._cache:
            self._cache.set(params.cache_key, result)
        
        return result
    
    async def _fetch_forecast_async(self, lat: float, lon: float, hours: int) -> WeatherForecastCollection:
        """非同期で天気予報を取得（内部メソッド）
        
        Args:
            lat: 緯度
            lon: 経度
            hours: 予報時間数
            
        Returns:
            天気予報コレクション
        """
        if not self.session:
            raise RuntimeError("セッションが初期化されていません。async with を使用してください。")
        
        # リトライループ
        retry_delay = self.retry_delay
        for attempt in range(self.max_retries):
            try:
                return await self._make_request(lat, lon, hours)
            except (WxTechAPIError, aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"API呼び出し失敗 (試行 {attempt + 1}/{self.max_retries}): {str(e)}. "
                        f"{retry_delay}秒後にリトライします。"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指数バックオフ
                else:
                    logger.error(f"全てのリトライが失敗しました: {str(e)}")
                    raise
        
        raise WxTechAPIError("予期しないエラー: リトライループが正常に終了しませんでした")
    
    async def _make_request(self, lat: float, lon: float, hours: int) -> WeatherForecastCollection:
        """実際のAPIリクエストを実行"""
        endpoint = f"{self.base_url}/ss1wx"
        params = {
            "lat": lat,
            "lon": lon,
            "hours": hours
        }
        headers = {
            "X-API-Key": self.api_key,
            "User-Agent": "AsyncWxTechAPIClient/1.0",
            "Accept": "application/json"
        }
        
        try:
            logger.info(f"🔄 非同期API呼び出し: lat={lat}, lon={lon}, hours={hours}")
            
            async with self.session.get(
                endpoint, 
                params=params, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.api.api_timeout)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise WxTechAPIError(
                        f"APIエラー: ステータス {response.status}",
                        status_code=response.status,
                        response_text=error_text
                    )
                
                data = await response.json()
                logger.info(f"✅ 非同期API応答受信: {len(data.get('hourly', []))}時間分のデータ")
                
                # レスポンスを解析
                location_name = f"{lat:.2f},{lon:.2f}"
                forecast_collection = parse_forecast_response(data, location_name)
                
                if not forecast_collection or not forecast_collection.forecasts:
                    raise ValueError("予報データが空です")
                
                return forecast_collection
                
        except asyncio.TimeoutError:
            raise WxTechAPIError(
                "APIタイムアウト",
                error_type="timeout"
            )
        except aiohttp.ClientError as e:
            raise WxTechAPIError(
                f"ネットワークエラー: {str(e)}",
                error_type="network_error"
            )
        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """キャッシュの統計情報を取得
        
        Returns:
            キャッシュ統計情報、キャッシュが無効な場合はNone
        """
        if self._cache:
            return self._cache.get_stats()
        return None
    
    def clear_cache(self):
        """キャッシュをクリア"""
        if self._cache:
            self._cache.clear()