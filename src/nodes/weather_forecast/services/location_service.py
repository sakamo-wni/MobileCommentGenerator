"""
Location service for weather forecast node

地点情報の取得と検証を担当するサービス
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple
from src.data.location.models import Location
from src.data.location.manager import LocationManagerRefactored

logger = logging.getLogger(__name__)


class LocationService:
    """地点情報の取得と検証を担当するサービス"""
    
    def __init__(self):
        self.location_manager = LocationManagerRefactored()
    
    def parse_location_string(self, location_name_raw: str) -> Tuple[str, Optional[float], Optional[float]]:
        """地点名文字列から地点名と座標を抽出
        
        Args:
            location_name_raw: 生の地点名文字列（"地点名,緯度,経度" 形式の場合あり）
            
        Returns:
            (地点名, 緯度, 経度) のタプル
        """
        provided_lat = None
        provided_lon = None
        
        if "," in location_name_raw:
            parts = location_name_raw.split(",")
            location_name = parts[0].strip()
            if len(parts) >= 3:
                try:
                    provided_lat = float(parts[1].strip())
                    provided_lon = float(parts[2].strip())
                    logger.info(
                        f"Extracted location name '{location_name}' with coordinates ({provided_lat}, {provided_lon})"
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid coordinates in '{location_name_raw}', will look up in LocationManager"
                    )
            else:
                logger.info(f"Extracted location name '{location_name}' from '{location_name_raw}'")
        else:
            location_name = location_name_raw.strip()
            
        return location_name, provided_lat, provided_lon
    
    def get_location_with_coordinates(
        self, 
        location_name: str, 
        provided_lat: Optional[float] = None,
        provided_lon: Optional[float] = None
    ) -> Location:
        """地点情報を取得（座標情報付き）
        
        Args:
            location_name: 地点名
            provided_lat: 提供された緯度（オプション）
            provided_lon: 提供された経度（オプション）
            
        Returns:
            Location オブジェクト
            
        Raises:
            ValueError: 地点が見つからない場合（LocationManagerに登録されておらず、かつ座標が提供されていない場合）
        """
        location = self.location_manager.get_location(location_name)
        
        # LocationManagerで見つからない場合、提供された座標を使用
        if location is None:
            if provided_lat is not None and provided_lon is not None:
                logger.info(
                    f"Location '{location_name}' not found in LocationManager, using provided coordinates"
                )
                # 座標のみを持つLocationオブジェクトを作成
                location = Location(
                    name=location_name,
                    prefecture="不明",
                    region="不明",
                    latitude=provided_lat,
                    longitude=provided_lon
                )
            else:
                raise ValueError(f"地点 '{location_name}' が見つかりません")
        else:
            # LocationManagerから取得した地点でも、提供された座標があれば上書き
            if provided_lat is not None and provided_lon is not None:
                location = Location(
                    name=location.name,
                    prefecture=location.prefecture,
                    region=location.region,
                    latitude=provided_lat,
                    longitude=provided_lon
                )
                logger.info(
                    f"Using provided coordinates for location '{location_name}': ({provided_lat}, {provided_lon})"
                )
                
        return location