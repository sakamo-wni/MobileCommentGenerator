"""
Cache warmer for popular locations

人気地点のキャッシュ事前温め
"""

from __future__ import annotations
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import json
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from src.data.weather_data import WeatherForecast
    from .manager import ForecastCache

logger = logging.getLogger(__name__)

# タイムゾーン定義
JST = ZoneInfo("Asia/Tokyo")


@dataclass
class PopularLocation:
    """人気地点情報"""
    name: str
    latitude: float
    longitude: float
    priority: int = 1  # 優先度（高いほど優先）
    access_count: int = 0  # アクセス数


class CacheWarmer:
    """キャッシュウォーマー
    
    人気の高い地点の予報を事前に取得してキャッシュを温める
    """
    
    def __init__(self, 
                 popular_locations_file: Optional[Path] = None,
                 max_concurrent: int = 5,
                 warm_hours_ahead: int = 48):
        """初期化
        
        Args:
            popular_locations_file: 人気地点リストファイル
            max_concurrent: 最大同時実行数
            warm_hours_ahead: 何時間先までキャッシュするか
        """
        self.popular_locations_file = popular_locations_file
        self.max_concurrent = max_concurrent
        self.warm_hours_ahead = warm_hours_ahead
        self._popular_locations: List[PopularLocation] = []
        self._stats = {
            "warmed_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "total_time_seconds": 0.0
        }
        
        # 人気地点リストを読み込み
        if popular_locations_file and popular_locations_file.exists():
            self._load_popular_locations()
    
    def _load_popular_locations(self) -> None:
        """人気地点リストを読み込み"""
        try:
            with open(self.popular_locations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for loc_data in data.get("locations", []):
                location = PopularLocation(
                    name=loc_data["name"],
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                    priority=loc_data.get("priority", 1),
                    access_count=loc_data.get("access_count", 0)
                )
                self._popular_locations.append(location)
            
            # 優先度とアクセス数でソート
            self._popular_locations.sort(
                key=lambda x: (x.priority, x.access_count), 
                reverse=True
            )
            
            logger.info(f"人気地点リストを読み込み: {len(self._popular_locations)}件")
            
        except Exception as e:
            logger.error(f"人気地点リストの読み込みエラー: {e}")
    
    def add_popular_location(self, location: PopularLocation) -> None:
        """人気地点を追加
        
        Args:
            location: 地点情報
        """
        # 既存の地点かチェック
        for idx, loc in enumerate(self._popular_locations):
            if loc.name == location.name:
                # アクセス数を更新
                self._popular_locations[idx].access_count += 1
                return
        
        # 新規追加
        self._popular_locations.append(location)
        
        # 再ソート
        self._popular_locations.sort(
            key=lambda x: (x.priority, x.access_count), 
            reverse=True
        )
    
    def save_popular_locations(self) -> None:
        """人気地点リストを保存"""
        if not self.popular_locations_file:
            return
        
        try:
            data = {
                "updated_at": datetime.now(JST).isoformat(),
                "locations": [
                    {
                        "name": loc.name,
                        "latitude": loc.latitude,
                        "longitude": loc.longitude,
                        "priority": loc.priority,
                        "access_count": loc.access_count
                    }
                    for loc in self._popular_locations
                ]
            }
            
            self.popular_locations_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.popular_locations_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"人気地点リストを保存: {len(self._popular_locations)}件")
            
        except Exception as e:
            logger.error(f"人気地点リストの保存エラー: {e}")
    
    async def warm_cache_async(self, 
                             forecast_fetcher: Callable[[str, float, float, datetime], Awaitable['WeatherForecast']], 
                             forecast_cache: 'ForecastCache') -> Dict[str, Any]:
        """キャッシュを非同期で温める
        
        Args:
            forecast_fetcher: 予報取得関数（async def(location_name, lat, lon, datetime) -> WeatherForecast）
            forecast_cache: ForecastCacheインスタンス
            
        Returns:
            実行統計
        """
        start_time = datetime.now()
        
        # 処理対象の時刻リスト
        target_hours = []
        current_time = datetime.now(JST)
        for hours_ahead in range(0, self.warm_hours_ahead, 3):  # 3時間ごと
            target_hours.append(current_time + timedelta(hours=hours_ahead))
        
        # タスクリスト
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 上位の人気地点のみ処理
        top_locations = self._popular_locations[:20]  # 上位20地点
        
        for location in top_locations:
            # 位置座標を登録
            forecast_cache.register_location_coordinate(
                location.name, 
                location.latitude, 
                location.longitude
            )
            
            for target_time in target_hours:
                task = self._warm_single_location(
                    location, 
                    target_time, 
                    forecast_fetcher, 
                    forecast_cache,
                    semaphore
                )
                tasks.append(task)
        
        # 全タスクを実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を集計
        for result in results:
            if isinstance(result, Exception):
                self._stats["failed_count"] += 1
                logger.error(f"キャッシュ温めエラー: {result}")
            elif result == "skipped":
                self._stats["skipped_count"] += 1
            else:
                self._stats["warmed_count"] += 1
        
        # 実行時間を記録
        self._stats["total_time_seconds"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"キャッシュ温め完了: "
            f"成功={self._stats['warmed_count']}, "
            f"スキップ={self._stats['skipped_count']}, "
            f"失敗={self._stats['failed_count']}, "
            f"時間={self._stats['total_time_seconds']:.1f}秒"
        )
        
        return self._stats
    
    async def _warm_single_location(self, 
                                  location: PopularLocation,
                                  target_time: datetime,
                                  forecast_fetcher,
                                  forecast_cache,
                                  semaphore: asyncio.Semaphore) -> str:
        """単一地点・時刻のキャッシュを温める"""
        async with semaphore:
            try:
                # 既にキャッシュがあるかチェック
                if forecast_cache.get_forecast_at_time(location.name, target_time):
                    logger.debug(f"既にキャッシュ済み: {location.name} at {target_time}")
                    return "skipped"
                
                # 予報を取得
                forecast = await forecast_fetcher(
                    location.name,
                    location.latitude,
                    location.longitude,
                    target_time
                )
                
                # キャッシュに保存
                forecast_cache.save_forecast(forecast, location.name)
                
                logger.debug(f"キャッシュ温め成功: {location.name} at {target_time}")
                return "warmed"
                
            except Exception as e:
                logger.error(f"キャッシュ温めエラー {location.name} at {target_time}: {e}")
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self._stats,
            "popular_locations_count": len(self._popular_locations),
            "top_locations": [
                {
                    "name": loc.name,
                    "access_count": loc.access_count,
                    "priority": loc.priority
                }
                for loc in self._popular_locations[:10]
            ]
        }