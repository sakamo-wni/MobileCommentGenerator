"""
WxTech API クライアント

高レベルのAPI操作インターフェースを提供
"""

from __future__ import annotations
from typing import Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import pytz
from datetime import timedelta, datetime

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from src.data.weather_data import WeatherForecastCollection
from src.data.location.models import Location
from src.apis.wxtech.api import WxTechAPI
from src.apis.wxtech.parser import parse_forecast_response
from src.apis.wxtech.errors import WxTechAPIError

logger = logging.getLogger(__name__)


class WxTechAPIClient:
    """WxTech API クライアント
    
    天気予報データの取得・処理を行う高レベルインターフェース
    """
    
    def __init__(self, api_key: str, timeout: int = 30):
        """クライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.api_key = api_key
        self.api = WxTechAPI(api_key, timeout)
        self.timeout = timeout
        
        # 非同期セッション（必要時に初期化）
        self._async_session: aiohttp.ClientSession | None = None
        self.base_url = "https://wxtech.weathernews.com/api/v1"
    
    def get_forecast(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """指定座標の天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        # パラメータ検証
        if not (-90 <= lat <= 90):
            raise ValueError(f"緯度が範囲外です: {lat} （-90～90の範囲で指定してください）")
        if not (-180 <= lon <= 180):
            raise ValueError(f"経度が範囲外です: {lon} （-180～180の範囲で指定してください）")
        if forecast_hours <= 0 or forecast_hours > 168:  # 最大7日間
            raise ValueError(f"予報時間数が範囲外です: {forecast_hours} （1-168時間の範囲で指定してください）")
        
        # API リクエスト実行
        params = {
            "lat": lat, 
            "lon": lon,
            "hours": forecast_hours
        }
        
        logger.info(f"🔄 WxTech API リクエスト: endpoint=ss1wx, params={params}")
        
        raw_data = self.api.make_request("ss1wx", params)
        
        # レスポンスの基本情報をログ出力
        if "wxdata" in raw_data and raw_data["wxdata"]:
            wxdata = raw_data["wxdata"][0]
            srf_count = len(wxdata.get("srf", []))
            mrf_count = len(wxdata.get("mrf", []))
            logger.info(f"📊 WxTech API レスポンス: srf={srf_count}件, mrf={mrf_count}件")
        
        # レスポンスデータの変換
        return parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")
    
    def get_forecast_by_location(self, location: Location) -> WeatherForecastCollection:
        """Location オブジェクトから天気予報を取得
        
        Args:
            location: 地点情報
            
        Returns:
            天気予報コレクション
            
        Raises:
            ValueError: 地点に緯度経度情報がない場合
            WxTechAPIError: API エラーが発生した場合
        """
        if location.latitude is None or location.longitude is None:
            raise ValueError(f"地点 '{location.name}' に緯度経度情報がありません")
        
        forecast_collection = self.get_forecast_for_next_day_hours_optimized(location.latitude, location.longitude)
        
        # 地点名を正しく設定
        forecast_collection.location = location.name
        for forecast in forecast_collection.forecasts:
            forecast.location = location.name
        
        return forecast_collection
    
    def get_forecast_for_next_day_hours_optimized(self, lat: float, lon: float) -> WeatherForecastCollection:
        """翌日の9, 12, 15, 18時のデータを効率的に取得する最適化版
        
        翌日6時から20時までの15時間分を取得し、必要な時刻のデータを含む
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            翌日の天気予報コレクション（基準時刻および9,12,15,18時を含む）
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        target_date = now_jst.date() + timedelta(days=1)
        
        # 最適化: 翌日8時から19時までの12時間分を確実に取得
        # これにより、9,12,15,18時すべてが含まれる
        tomorrow_8am = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=8)))
        tomorrow_7pm = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=19)))
        
        hours_to_8am = (tomorrow_8am - now_jst).total_seconds() / 3600
        
        # 最適な取得時間を決定
        if hours_to_8am > 0:
            # まだ翌日8時前なので、8時から19時までの12時間分
            forecast_hours = int(hours_to_8am) + 12
            logger.info(f"最適化: 翌日8時まで{hours_to_8am:.1f}h → {forecast_hours}時間分を取得")
        else:
            # すでに翌日8時を過ぎているので、現在から19時まで
            hours_to_7pm = (tomorrow_7pm - now_jst).total_seconds() / 3600
            forecast_hours = max(int(hours_to_7pm) + 1, 1)
            logger.info(f"最適化: 翌日19時まで{hours_to_7pm:.1f}h → {forecast_hours}時間分を取得")
        
        # データを取得
        forecast_collection = self.get_forecast(lat, lon, forecast_hours=forecast_hours)
        
        # 翌日の9, 12, 15, 18時に最も近い予報を選択
        target_hours = [9, 12, 15, 18]
        selected_forecasts = []
        
        for hour in target_hours:
            target_time = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            closest_forecast = None
            min_diff = float('inf')
            
            for forecast in forecast_collection.forecasts:
                # forecastのdatetimeがnaiveな場合はJSTとして扱う
                forecast_dt = forecast.datetime
                if forecast_dt.tzinfo is None:
                    forecast_dt = jst.localize(forecast_dt)
                
                # 翌日のデータのみを対象
                if forecast_dt.date() == target_date:
                    # 目標時刻との差を計算
                    diff = abs((forecast_dt - target_time).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest_forecast = forecast
            
            if closest_forecast:
                selected_forecasts.append(closest_forecast)
                logger.debug(
                    f"目標時刻 {hour:02d}:00 → 選択: {closest_forecast.datetime.strftime('%Y-%m-%d %H:%M')} "
                    f"(差: {min_diff/3600:.1f}時間)"
                )
            else:
                logger.warning(f"目標時刻 {hour:02d}:00 の予報が見つかりません")
        
        # フィルタリング結果のログ
        logger.info(
            f"最適化結果: {len(forecast_collection.forecasts)}件から{len(selected_forecasts)}件に絞り込み "
            f"- 選択された時刻: {[f.datetime.strftime('%H:%M') for f in selected_forecasts]}"
        )
        
        # フィルタリングしたデータを新しいコレクションとして返す
        filtered_collection = WeatherForecastCollection(
            location=forecast_collection.location,
            forecasts=selected_forecasts
        )
        
        return filtered_collection
    
    
    async def get_forecast_async(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """非同期で天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_forecast, lat, lon, forecast_hours)
    
    async def get_forecast_for_next_day_hours_optimized_async(self, lat: float, lon: float) -> WeatherForecastCollection:
        """非同期版: 翌日の9, 12, 15, 18時のデータを効率的に取得する最適化版
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            翌日の天気予報コレクション（基準時刻および9,12,15,18時を含む）
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_forecast_for_next_day_hours_optimized, lat, lon)
    
    def close(self):
        """セッションを閉じる"""
        self.api.close()
    
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type: type[BaseException | None], exc_val: BaseException | None, exc_tb: Any | None) -> None:
        self.close()
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        if AIOHTTP_AVAILABLE and self._async_session is None:
            # 接続数制限を設定
            connector = aiohttp.TCPConnector(
                limit=10,  # 全体の最大接続数
                limit_per_host=5  # ホストごとの最大接続数
            )
            self._async_session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self._async_session:
            await self._async_session.close()
            self._async_session = None
    
    async def ensure_async_session(self):
        """非同期セッションが存在することを確認"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttpがインストールされていません。pip install aiohttpを実行してください。")
        
        if self._async_session is None:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5
            )
            self._async_session = aiohttp.ClientSession(connector=connector)
    
    async def async_get_forecast_optimized(self, lat: float, lon: float) -> WeatherForecastCollection:
        """最適化された翌日予報の非同期取得（真の非同期実装）
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            天気予報コレクション
        """
        await self.ensure_async_session()
        
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
        return await self._async_fetch_forecast(lat, lon, forecast_hours)
    
    async def _async_fetch_forecast(self, lat: float, lon: float, hours: int) -> WeatherForecastCollection:
        """非同期で天気予報を取得（内部メソッド）"""
        endpoint = f"{self.base_url}/ss1wx"
        params = {
            "lat": lat,
            "lon": lon,
            "hours": hours
        }
        headers = {
            "X-API-Key": self.api_key,
            "User-Agent": "WxTechAPIClient/2.0",
            "Accept": "application/json"
        }
        
        try:
            logger.info(f"🔄 非同期API呼び出し: lat={lat}, lon={lon}, hours={hours}")
            
            async with self._async_session.get(
                endpoint, 
                params=params, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
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
        except Exception as e:
            if isinstance(e, WxTechAPIError):
                raise
            logger.error(f"予期しないエラー: {str(e)}")
            raise WxTechAPIError(f"予期しないエラー: {str(e)}")


# 既存の関数との互換性を保つためのラッパー関数
async def get_japan_1km_mesh_weather_forecast(
    lat: float, lon: float, api_key: str
) -> dict[str, Any]:
    """既存の get_japan_1km_mesh_weather_forecast 関数の互換ラッパー
    
    Args:
        lat: 緯度
        lon: 経度
        api_key: WxTech API キー
        
    Returns:
        天気予報データの辞書
    """
    client = WxTechAPIClient(api_key)
    try:
        forecast_collection = await client.get_forecast_async(lat, lon, forecast_hours=72)
        return forecast_collection.to_dict()
    finally:
        client.close()