#!/usr/bin/env python3
"""緯度経度ベースの海岸判定テスト"""

from src.utils.geography import CoastalDetector
from src.data.location_manager import LocationManager


def test_coordinate_based_coastal_detection():
    """緯度経度ベースの海岸判定テスト"""
    print("=== 緯度経度ベースの海岸判定テスト ===\n")
    
    # LocationManagerから地点情報を取得
    location_manager = LocationManager()
    
    # テスト地点
    test_locations = [
        "東京",    # 内陸（東京都心）
        "横浜",    # 海岸
        "京都",    # 内陸
        "大阪",    # 大阪湾に近い
        "長野",    # 山間部
        "銚子",    # 海岸
        "名古屋",  # 伊勢湾に近い
        "金沢",    # 海岸
        "札幌",    # やや内陸
        "那覇",    # 海岸（島）
    ]
    
    for location_name in test_locations:
        location = location_manager.get_location(location_name)
        
        if location and location.latitude and location.longitude:
            # 海岸からの距離を計算
            distance = CoastalDetector.get_distance_to_coast(
                location.latitude, 
                location.longitude
            )
            
            # 海岸地域かどうか判定
            is_coastal = CoastalDetector.is_coastal(
                location.latitude,
                location.longitude,
                threshold_km=15.0
            )
            
            # 地形的特徴を取得
            features = CoastalDetector.get_topographic_features(
                location.latitude,
                location.longitude
            )
            
            print(f"{location_name}:")
            print(f"  座標: ({location.latitude:.4f}, {location.longitude:.4f})")
            print(f"  海岸からの距離: {distance:.1f}km")
            print(f"  海岸地域判定: {'海岸' if is_coastal else '内陸'}")
            print(f"  地形タイプ: {features['topographic_type']}")
            print()
        else:
            print(f"{location_name}: 座標情報なし")
            print()


def test_specific_coordinates():
    """特定の座標での判定テスト"""
    print("\n=== 特定座標の判定テスト ===\n")
    
    test_cases = [
        ("富士山頂", 35.3606, 138.7274),  # 明らかに内陸
        ("房総半島先端", 34.9, 139.9),    # 明らかに海岸
        ("琵琶湖周辺", 35.3, 136.0),      # 内陸の湖
        ("瀬戸内海の島", 34.4, 133.2),    # 島嶼部
    ]
    
    for name, lat, lon in test_cases:
        distance = CoastalDetector.get_distance_to_coast(lat, lon)
        is_coastal = CoastalDetector.is_coastal(lat, lon)
        
        print(f"{name} ({lat}, {lon}):")
        print(f"  海岸からの距離: {distance:.1f}km")
        print(f"  判定: {'海岸地域' if is_coastal else '内陸地域'}")
        print()


if __name__ == "__main__":
    test_coordinate_based_coastal_detection()
    test_specific_coordinates()