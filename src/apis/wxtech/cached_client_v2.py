"""
改善されたキャッシュ付きWxTech APIクライアント

統一キャッシュマネージャーを使用し、
より効率的なキャッシュ管理を実現
"""

from __future__ import annotations

from typing import Any
import logging
import os

from src.data.weather_data import WeatherForecastCollection
from src.data.location.models import Location
from src.apis.wxtech.client import WxTechAPIClient
from src.utils.cache_decorators import smart_cache
from src.utils.cache_manager import get_cache_manager, CacheConfig

logger = logging.getLogger(__name__)


class CachedWxTechAPIClientV2(WxTechAPIClient):
    """改善されたキャッシュ機能付きWxTech APIクライアント
    
    統一キャッシュマネージャーを使用し、メモリ効率と
    パフォーマンスを向上させたバージョン
    """
    
    def __init__(self, api_key: str, timeout: int = 30, cache_ttl: int | None = None):
        """キャッシュ付きクライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
            cache_ttl: キャッシュの有効期限（秒）（デフォルト: 環境変数または600秒）
        """
        super().__init__(api_key, timeout)
        
        # 環境変数から設定を取得
        if cache_ttl is None:
            cache_ttl = int(os.environ.get('WXTECH_CACHE_TTL', '600'))  # 10分
        
        self._cache_ttl = cache_ttl
        
        # 専用キャッシュが存在しない場合は作成
        cache_manager = get_cache_manager()
        if "wxtech_api" not in cache_manager._caches:
            cache_manager.create_cache(
                "wxtech_api",
                CacheConfig(
                    default_ttl_seconds=cache_ttl,
                    max_size=200,
                    max_memory_mb=20,
                    enable_stats_tracking=True
                )
            )
        
        logger.info(f"WxTech APIクライアントを初期化しました（キャッシュTTL: {cache_ttl}秒）")
    
    @smart_cache(
        cache_name="wxtech_api",
        key_prefix="forecast",
        condition=lambda result: result is not None and len(result.forecasts) > 0
    )
    def get_forecast(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """天気予報を取得（キャッシュ付き）
        
        Args:
            lat: 緯度
            lon: 経度  
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
        """
        return super().get_forecast(lat, lon, forecast_hours)
    
    @smart_cache(
        cache_name="wxtech_api",
        key_prefix="forecast_location",
        condition=lambda result: result is not None and len(result.forecasts) > 0
    )
    def get_forecast_for_location(self, location: Location, forecast_hours: int = 72) -> WeatherForecastCollection:
        """地点データから天気予報を取得（キャッシュ付き）
        
        Args:
            location: 地点データ
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
        """
        return super().get_forecast_for_location(location, forecast_hours)
    
    def get_forecast_with_metadata(
        self, 
        lat: float, 
        lon: float, 
        forecast_hours: int = 72,
        include_cache_info: bool = False
    ) -> dict[str, Any]:
        """天気予報をメタデータ付きで取得
        
        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数
            include_cache_info: キャッシュ情報を含めるかどうか
            
        Returns:
            予報データとメタデータを含む辞書
        """
        # キャッシュを明示的にバイパスしてフレッシュなデータを取得したい場合
        # _bypass_cache=True を指定できる
        forecast = self.get_forecast(lat, lon, forecast_hours)
        
        result = {
            "forecast": forecast,
            "metadata": {
                "lat": lat,
                "lon": lon,
                "forecast_hours": forecast_hours,
                "api_client": "CachedWxTechAPIClientV2"
            }
        }
        
        if include_cache_info:
            cache_manager = get_cache_manager()
            cache_stats = cache_manager.get_cache("wxtech_api").get_stats()
            result["cache_info"] = {
                "hit_rate": cache_stats.hit_rate,
                "total_requests": cache_stats.total_requests,
                "cache_size": cache_stats.size
            }
        
        return result
    
    def warm_cache_for_locations(self, locations: list[Location], forecast_hours: int = 72):
        """複数地点の予報データでキャッシュをウォーミング
        
        Args:
            locations: 地点データのリスト
            forecast_hours: 予報時間数
        """
        logger.info(f"{len(locations)}地点のキャッシュウォーミングを開始します")
        
        success_count = 0
        for location in locations:
            try:
                # キャッシュに投入
                self.get_forecast_for_location(location, forecast_hours)
                success_count += 1
            except Exception as e:
                logger.error(f"地点 {location.name} のキャッシュウォーミングに失敗: {e}")
        
        logger.info(f"キャッシュウォーミング完了: {success_count}/{len(locations)} 地点")
    
    def clear_cache(self):
        """WxTech APIのキャッシュをクリア"""
        cache_manager = get_cache_manager()
        cache = cache_manager.get_cache("wxtech_api")
        cache.clear()
        logger.info("WxTech APIキャッシュをクリアしました")


# 既存のクライアントとの互換性のためのファクトリ関数
def create_cached_wxtech_client(
    api_key: str | None = None,
    timeout: int = 30,
    cache_ttl: int | None = None,
    use_v2: bool = True
) -> WxTechAPIClient:
    """キャッシュ付きWxTech APIクライアントを作成
    
    Args:
        api_key: APIキー（Noneの場合は環境変数から取得）
        timeout: タイムアウト秒数
        cache_ttl: キャッシュTTL
        use_v2: V2クライアントを使用するかどうか
        
    Returns:
        WxTech APIクライアント
    """
    if api_key is None:
        api_key = os.environ.get('WXTECH_API_KEY', '')
    
    if use_v2:
        return CachedWxTechAPIClientV2(api_key, timeout, cache_ttl)
    else:
        from src.apis.wxtech.cached_client import CachedWxTechAPIClient
        return CachedWxTechAPIClient(api_key, timeout, cache_ttl)