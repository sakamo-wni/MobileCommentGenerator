"""
Distance calculation utilities

距離計算関連のユーティリティ関数
"""

from __future__ import annotations
from math import radians, sin, cos, sqrt, atan2
from typing import Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の距離を計算（ハーバサイン公式）
    
    Args:
        lat1, lon1: 地点1の緯度・経度
        lat2, lon2: 地点2の緯度・経度
        
    Returns:
        距離（km）
    """
    R = 6371  # 地球の半径（km）
    
    # ラジアンに変換
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # 差分
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # ハーバサイン公式
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def estimate_memory_usage_mb(num_points: int) -> float:
    """KD-Treeのメモリ使用量を推定
    
    Args:
        num_points: ポイント数
        
    Returns:
        推定メモリ使用量（MB）
    """
    # 推定値:
    # - 各座標: 2 * 8 bytes (float64)
    # - KD-Treeのオーバーヘッド: 約3倍
    # - その他のメタデータ
    bytes_per_point = 2 * 8 * 3  # 座標 + KD-Treeオーバーヘッド
    total_bytes = num_points * bytes_per_point
    return total_bytes / (1024 * 1024)  # MB に変換


def find_nearest_distance_linear(lat: float, lon: float, 
                               reference_points: list[tuple[float, float]]) -> Optional[float]:
    """線形探索で最近傍点までの距離を計算
    
    Args:
        lat, lon: 対象地点の緯度・経度
        reference_points: 参照点のリスト
        
    Returns:
        最近傍点までの距離（km）
    """
    if not reference_points:
        return None
        
    min_distance = float('inf')
    
    for ref_lat, ref_lon in reference_points:
        distance = haversine_distance(lat, lon, ref_lat, ref_lon)
        if distance < min_distance:
            min_distance = distance
    
    return min_distance if min_distance != float('inf') else None