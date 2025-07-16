"""
Spatial cache clustering for nearby locations

近隣位置のキャッシュクラスタリング
"""

from __future__ import annotations
import logging
import math
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from threading import RLock

from .models import ForecastCacheEntry

logger = logging.getLogger(__name__)


@dataclass
class LocationCoordinate:
    """位置座標"""
    name: str
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'LocationCoordinate') -> float:
        """他の位置までの距離を計算（km）
        
        Haversine formulaを使用した大圏距離計算
        """
        R = 6371.0  # 地球の半径（km）
        
        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)
        
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


class SpatialForecastCache:
    """空間的な予報キャッシュ
    
    近隣の位置のキャッシュを活用して、
    APIコール数を削減
    """
    
    def __init__(self, 
                 max_distance_km: float = 10.0,
                 max_neighbors: int = 5):
        """初期化
        
        Args:
            max_distance_km: 近隣とみなす最大距離（km）
            max_neighbors: 検索する最大近隣数
        """
        self.max_distance_km = max_distance_km
        self.max_neighbors = max_neighbors
        self._location_coords: Dict[str, LocationCoordinate] = {}
        self._cache: Dict[str, List[Tuple[datetime, ForecastCacheEntry]]] = {}
        self._lock = RLock()
        
        # 統計情報
        self._stats = {
            "direct_hits": 0,
            "neighbor_hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    def register_location(self, name: str, latitude: float, longitude: float) -> None:
        """位置を登録
        
        Args:
            name: 地点名
            latitude: 緯度
            longitude: 経度
        """
        with self._lock:
            self._location_coords[name] = LocationCoordinate(name, latitude, longitude)
            logger.debug(f"Registered location: {name} ({latitude}, {longitude})")
    
    def put(self, location_name: str, forecast_datetime: datetime, entry: ForecastCacheEntry) -> None:
        """キャッシュに追加
        
        Args:
            location_name: 地点名
            forecast_datetime: 予報日時
            entry: キャッシュエントリ
        """
        with self._lock:
            if location_name not in self._cache:
                self._cache[location_name] = []
            
            # 古いエントリを削除（同じ時刻のもの）
            self._cache[location_name] = [
                (dt, e) for dt, e in self._cache[location_name]
                if dt != forecast_datetime
            ]
            
            # 新規追加
            self._cache[location_name].append((forecast_datetime, entry))
            
            # サイズ制限（各地点最大100エントリ）
            if len(self._cache[location_name]) > 100:
                self._cache[location_name] = self._cache[location_name][-100:]
    
    def get(self, location_name: str, target_datetime: datetime,
            tolerance_hours: int = 3) -> Optional[ForecastCacheEntry]:
        """キャッシュから取得（近隣位置も検索）
        
        Args:
            location_name: 地点名
            target_datetime: 対象日時
            tolerance_hours: 許容時間差（時間）
            
        Returns:
            キャッシュエントリ（見つからない場合はNone）
        """
        with self._lock:
            self._stats["total_requests"] += 1
            
            # 直接キャッシュをチェック
            if direct_result := self._get_direct(location_name, target_datetime, tolerance_hours):
                self._stats["direct_hits"] += 1
                logger.debug(f"Direct cache hit for {location_name}")
                return direct_result
            
            # 近隣位置のキャッシュをチェック
            if neighbor_result := self._get_from_neighbors(location_name, target_datetime, tolerance_hours):
                self._stats["neighbor_hits"] += 1
                logger.info(f"Neighbor cache hit for {location_name}")
                return neighbor_result
            
            self._stats["misses"] += 1
            return None
    
    def _get_direct(self, location_name: str, target_datetime: datetime,
                   tolerance_hours: int) -> Optional[ForecastCacheEntry]:
        """直接キャッシュから取得"""
        if location_name not in self._cache:
            return None
        
        best_entry = None
        min_time_diff = float('inf')
        
        for dt, entry in self._cache[location_name]:
            time_diff = abs((dt - target_datetime).total_seconds() / 3600)
            if time_diff <= tolerance_hours and time_diff < min_time_diff:
                min_time_diff = time_diff
                best_entry = entry
        
        return best_entry
    
    def _get_from_neighbors(self, location_name: str, target_datetime: datetime,
                           tolerance_hours: int) -> Optional[ForecastCacheEntry]:
        """近隣位置のキャッシュから取得"""
        if location_name not in self._location_coords:
            return None
        
        target_coord = self._location_coords[location_name]
        neighbors = self._find_nearest_neighbors(target_coord)
        
        for neighbor_coord, distance in neighbors:
            if neighbor_entry := self._get_direct(neighbor_coord.name, target_datetime, tolerance_hours):
                logger.info(
                    f"Using cache from neighbor {neighbor_coord.name} "
                    f"({distance:.1f}km away) for {location_name}"
                )
                # 近隣のデータを使用（地点名は変更）
                return ForecastCacheEntry(
                    location_name=location_name,  # 要求された地点名を使用
                    forecast_datetime=neighbor_entry.forecast_datetime,
                    cached_at=neighbor_entry.cached_at,
                    temperature=neighbor_entry.temperature,
                    max_temperature=neighbor_entry.max_temperature,
                    min_temperature=neighbor_entry.min_temperature,
                    weather_condition=neighbor_entry.weather_condition,
                    weather_description=neighbor_entry.weather_description,
                    precipitation=neighbor_entry.precipitation,
                    humidity=neighbor_entry.humidity,
                    wind_speed=neighbor_entry.wind_speed,
                    metadata=neighbor_entry.metadata
                )
        
        return None
    
    def _find_nearest_neighbors(self, target: LocationCoordinate) -> List[Tuple[LocationCoordinate, float]]:
        """最も近い近隣位置を検索"""
        neighbors = []
        
        for name, coord in self._location_coords.items():
            if coord.name == target.name:
                continue
            
            distance = target.distance_to(coord)
            if distance <= self.max_distance_km:
                neighbors.append((coord, distance))
        
        # 距離でソート
        neighbors.sort(key=lambda x: x[1])
        
        # 最大数で制限
        return neighbors[:self.max_neighbors]
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            total_hits = self._stats["direct_hits"] + self._stats["neighbor_hits"]
            hit_rate = total_hits / self._stats["total_requests"] if self._stats["total_requests"] > 0 else 0.0
            
            return {
                "total_requests": self._stats["total_requests"],
                "direct_hits": self._stats["direct_hits"],
                "neighbor_hits": self._stats["neighbor_hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "total_locations": len(self._location_coords),
                "cached_locations": len(self._cache),
                "max_distance_km": self.max_distance_km,
                "max_neighbors": self.max_neighbors
            }
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                "direct_hits": 0,
                "neighbor_hits": 0,
                "misses": 0,
                "total_requests": 0
            }
            logger.info("Spatial cache cleared")