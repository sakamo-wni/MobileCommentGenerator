"""
キャッシュ付きWxTech APIクライアント

キャッシュ機能を持つWxTech APIクライアントの実装
"""

from typing import Dict, Any, Optional
import logging
import os

from src.data.weather_data import WeatherForecastCollection
from src.data.location.models import Location
from src.apis.wxtech.client import WxTechAPIClient
from src.utils.cache import TTLCache, cached_method

logger = logging.getLogger(__name__)


class CachedWxTechAPIClient(WxTechAPIClient):
    """キャッシュ機能付きWxTech APIクライアント
    
    WxTechAPIClientにTTLキャッシュ機能を追加
    """
    
    def __init__(self, api_key: str, timeout: int = 30, cache_ttl: Optional[int] = None, cache_size: Optional[int] = None):
        """キャッシュ付きクライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
            cache_ttl: キャッシュの有効期限（秒）（デフォルト: 環境変数または300秒）
            cache_size: キャッシュサイズ（デフォルト: 環境変数または100）
        
        Note:
            LRU（Least Recently Used）アルゴリズムにより、キャッシュが満杯になった場合は
            最も使用されていないエントリが自動的に削除されます。
        """
        super().__init__(api_key, timeout)
        
        # 環境変数から設定を取得
        if cache_ttl is None:
            cache_ttl = int(os.environ.get('WXTECH_CACHE_TTL', '300'))
        if cache_size is None:
            cache_size = int(os.environ.get('WXTECH_CACHE_SIZE', '100'))
        
        # キャッシュを初期化
        self._cache = TTLCache(default_ttl=cache_ttl, max_size=cache_size)
        logger.info(f"キャッシュを初期化しました（TTL: {cache_ttl}秒, サイズ: {cache_size}）")
    
    @cached_method(cache_attr="_cache")
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
    
    @cached_method(cache_attr="_cache")
    def get_forecast_for_location(self, location: Location, forecast_hours: int = 72) -> WeatherForecastCollection:
        """地点データから天気予報を取得（キャッシュ付き）
        
        Args:
            location: 地点データ
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
        """
        return super().get_forecast_for_location(location, forecast_hours)
    
    @cached_method(cache_attr="_cache")
    def get_forecast_for_next_day_hours_optimized(self, lat: float, lon: float) -> WeatherForecastCollection:
        """翌日の9, 12, 15, 18時のデータを効率的に取得（キャッシュ付き）
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            翌日の天気予報コレクション（基準時刻および9,12,15,18時を含む）
        """
        return super().get_forecast_for_next_day_hours_optimized(lat, lon)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得
        
        Returns:
            キャッシュ統計情報
        """
        return self._cache.get_stats()
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()
        logger.info("キャッシュをクリアしました")