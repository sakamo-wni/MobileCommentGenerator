"""
非同期版 WxTech API クライアント

aiohttpを使用した真の非同期実装
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import aiohttp
import pytz

from src.apis.wxtech.parser import WxTechResponseParser
from src.apis.wxtech.errors import WxTechAPIError
from src.data.weather_data import WeatherForecastCollection

logger = logging.getLogger(__name__)


class AsyncWxTechAPIClient:
    """非同期版 WxTech API クライアント"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://wxtech-api.weathernews.com/api/v1"
        self.parser = WxTechResponseParser()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
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
                timeout=aiohttp.ClientTimeout(total=30)
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
                
                # パーサーで解析
                forecasts = self.parser.parse_response(data)
                
                if not forecasts:
                    raise ValueError("予報データが空です")
                
                # location_nameを適切に設定
                location_name = f"{lat:.2f},{lon:.2f}"
                
                return WeatherForecastCollection(
                    location=location_name,
                    forecasts=forecasts
                )
                
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