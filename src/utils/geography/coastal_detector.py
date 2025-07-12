"""海岸線検出ユーティリティ - 緯度経度から海岸/内陸を判定"""

import logging
from typing import List, Tuple, Optional
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)


class CoastalDetector:
    """緯度経度情報を使用して海岸地域を検出"""
    
    # 日本の主要な海岸線の代表点（緯度、経度）
    # これは簡易版で、実際にはより詳細な海岸線データが必要
    COASTAL_REFERENCE_POINTS = [
        # 北海道
        (45.5, 141.9),  # 稚内
        (43.2, 140.9),  # 留萌
        (43.1, 141.3),  # 札幌（石狩湾）
        (42.8, 140.7),  # 小樽
        (41.8, 140.7),  # 函館
        (42.3, 143.2),  # 釧路
        (43.3, 145.6),  # 根室
        (44.0, 144.3),  # 網走
        
        # 東北太平洋側
        (40.9, 141.7),  # 八戸
        (39.7, 141.9),  # 宮古
        (39.0, 141.6),  # 大船渡
        (38.4, 141.3),  # 石巻
        (37.9, 140.9),  # 相馬
        (37.0, 140.9),  # いわき
        
        # 東北日本海側
        (40.8, 140.1),  # 青森
        (40.2, 139.5),  # 男鹿
        (39.0, 139.8),  # 酒田
        (38.9, 139.8),  # 鶴岡
        
        # 関東
        (35.7, 140.9),  # 銚子
        (35.1, 140.3),  # 勝浦
        (35.0, 139.8),  # 館山
        (35.3, 139.6),  # 横須賀
        (35.2, 139.1),  # 平塚
        (35.1, 139.1),  # 小田原
        
        # 中部日本海側
        (37.9, 139.0),  # 新潟
        (36.8, 137.2),  # 富山
        (36.5, 136.6),  # 金沢
        (36.2, 136.1),  # 福井
        
        # 中部太平洋側
        (34.6, 138.9),  # 静岡
        (34.7, 137.4),  # 浜松
        (34.7, 139.0),  # 伊東
        (34.7, 138.9),  # 下田
        
        # 近畿
        (35.5, 135.4),  # 舞鶴
        (34.7, 135.2),  # 神戸
        (34.7, 134.4),  # 姫路
        (34.2, 135.2),  # 和歌山
        (33.6, 135.8),  # 串本
        (33.5, 135.8),  # 潮岬
        
        # 中国
        (35.5, 134.2),  # 鳥取
        (35.4, 133.1),  # 境港
        (35.5, 133.0),  # 松江
        (34.8, 132.1),  # 浜田
        (34.4, 133.9),  # 岡山（瀬戸内）
        (34.4, 132.5),  # 広島（瀬戸内）
        (34.0, 131.0),  # 下関
        
        # 四国
        (34.3, 134.0),  # 高松（瀬戸内）
        (34.1, 134.6),  # 徳島
        (33.6, 133.5),  # 高知
        (33.2, 132.6),  # 宇和島
        (33.8, 132.8),  # 松山
        
        # 九州
        (33.6, 130.4),  # 福岡
        (33.2, 130.3),  # 佐賀
        (32.7, 129.9),  # 長崎
        (32.8, 130.7),  # 熊本
        (33.2, 131.6),  # 大分
        (31.9, 131.4),  # 宮崎
        (31.6, 130.6),  # 鹿児島
        
        # 沖縄
        (26.2, 127.7),  # 那覇
        (24.4, 124.2),  # 石垣
        (24.8, 125.3),  # 宮古島
    ]
    
    # 海岸からの距離閾値（km）
    COASTAL_THRESHOLD_KM = 10.0  # 10km以内を海岸地域とする
    
    @classmethod
    def is_coastal(cls, latitude: float, longitude: float, threshold_km: float = None) -> bool:
        """
        緯度経度から海岸地域かどうかを判定
        
        Args:
            latitude: 緯度
            longitude: 経度
            threshold_km: 海岸判定の閾値（km）、Noneの場合はデフォルト値を使用
            
        Returns:
            海岸地域の場合True
        """
        if threshold_km is None:
            threshold_km = cls.COASTAL_THRESHOLD_KM
            
        min_distance = cls.get_distance_to_coast(latitude, longitude)
        
        if min_distance is None:
            logger.warning(f"海岸距離を計算できません: ({latitude}, {longitude})")
            return False
            
        is_coastal_location = min_distance <= threshold_km
        
        if is_coastal_location:
            logger.debug(f"海岸地域と判定: ({latitude}, {longitude}) - 最短距離: {min_distance:.1f}km")
        else:
            logger.debug(f"内陸地域と判定: ({latitude}, {longitude}) - 最短距離: {min_distance:.1f}km")
            
        return is_coastal_location
    
    @classmethod
    def get_distance_to_coast(cls, latitude: float, longitude: float) -> Optional[float]:
        """
        最も近い海岸線までの距離を取得
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            海岸線までの最短距離（km）
        """
        if not cls.COASTAL_REFERENCE_POINTS:
            return None
            
        min_distance = float('inf')
        
        for coastal_lat, coastal_lon in cls.COASTAL_REFERENCE_POINTS:
            distance = cls._calculate_distance(
                latitude, longitude,
                coastal_lat, coastal_lon
            )
            if distance < min_distance:
                min_distance = distance
                
        return min_distance if min_distance != float('inf') else None
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine公式を使用して2地点間の距離を計算
        
        Args:
            lat1, lon1: 地点1の緯度経度
            lat2, lon2: 地点2の緯度経度
            
        Returns:
            距離（km）
        """
        R = 6371  # 地球の半径（km）
        
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    @classmethod
    def get_topographic_features(cls, latitude: float, longitude: float) -> dict:
        """
        地形的特徴を推定
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            地形的特徴の辞書
        """
        distance_to_coast = cls.get_distance_to_coast(latitude, longitude)
        
        features = {
            "is_coastal": False,
            "distance_to_coast_km": distance_to_coast,
            "topographic_type": "unknown"
        }
        
        if distance_to_coast is not None:
            if distance_to_coast <= 5:
                features["is_coastal"] = True
                features["topographic_type"] = "coastal"
            elif distance_to_coast <= 20:
                features["is_coastal"] = True
                features["topographic_type"] = "near_coastal"
            elif distance_to_coast <= 50:
                features["topographic_type"] = "plain"
            else:
                features["topographic_type"] = "inland"
                
                # 簡易的な山間部判定（中部地方の内陸など）
                if 35 <= latitude <= 37 and 137 <= longitude <= 139:
                    features["topographic_type"] = "mountainous"
        
        return features