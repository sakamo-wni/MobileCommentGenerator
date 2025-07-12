"""海岸線検出ユーティリティ - 緯度経度から海岸/内陸を判定（KD-Tree最適化版）"""

import logging
from math import radians, sin, cos, sqrt, atan2
import numpy as np
from scipy.spatial import KDTree
import sys
import threading
import weakref
from typing import ClassVar

# Import type definitions for Python 3.13+
from src.types.workflow_types import TopographicFeatures

logger = logging.getLogger(__name__)

# Python 3.13 type alias
type Coordinate = tuple[float, float]


class CoastalDetector:
    """緯度経度情報を使用して海岸地域を検出
    
    メモリ使用量の制限付きKD-Tree実装：
    - KD-Treeのメモリ使用量を推定
    - メモリ制限を超える場合は従来の線形探索にフォールバック
    - スレッドセーフな初期化
    """
    
    # メモリ使用量の上限（デフォルト: 50MB）
    MAX_MEMORY_MB: ClassVar[int] = 50
    
    # 日本の主要な海岸線の代表点（緯度、経度）
    # これは簡易版で、実際にはより詳細な海岸線データが必要
    COASTAL_REFERENCE_POINTS: list[Coordinate] = [
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
    
    # KD-Treeインスタンス（クラス変数として保持）
    _kdtree: KDTree | None = None
    _reference_coords_3d: np.ndarray | None = None
    _initialization_lock = threading.Lock()
    _memory_usage_mb: float = 0.0
    _use_kdtree: bool = True  # KD-Treeを使用するかどうか
    
    @classmethod
    def _estimate_memory_usage(cls, num_points: int) -> float:
        """KD-Treeのメモリ使用量を推定（MB単位）
        
        Args:
            num_points: データポイント数
            
        Returns:
            推定メモリ使用量（MB）
        """
        # 各座標は3つのfloat64（8バイト×3）
        coords_size = num_points * 3 * 8
        
        # KD-Treeのオーバーヘッド（ノード構造など）
        # 一般的にデータサイズの2-3倍程度
        kdtree_overhead = coords_size * 2.5
        
        # numpy配列とPythonオブジェクトのオーバーヘッド
        object_overhead = num_points * 100  # 各ポイントあたり約100バイト
        
        total_bytes = coords_size + kdtree_overhead + object_overhead
        return total_bytes / (1024 * 1024)  # MBに変換
    
    @classmethod
    def _initialize_kdtree(cls) -> None:
        """KD-Treeを初期化（初回アクセス時のみ実行、スレッドセーフ）"""
        with cls._initialization_lock:
            if cls._kdtree is None and cls.COASTAL_REFERENCE_POINTS:
                # メモリ使用量を推定
                estimated_memory = cls._estimate_memory_usage(len(cls.COASTAL_REFERENCE_POINTS))
                
                if estimated_memory > cls.MAX_MEMORY_MB:
                    logger.warning(
                        f"KD-Treeの推定メモリ使用量（{estimated_memory:.1f}MB）が"
                        f"制限（{cls.MAX_MEMORY_MB}MB）を超えるため、線形探索を使用します"
                    )
                    cls._use_kdtree = False
                    return
                
                try:
                    # 緯度経度を3D直交座標系に変換
                    # これにより、KD-Treeでの距離計算が球面距離により近くなる
                    coords_rad = np.array([
                        [radians(lat), radians(lon)] 
                        for lat, lon in cls.COASTAL_REFERENCE_POINTS
                    ])
                    
                    # 3D直交座標に変換
                    x = np.cos(coords_rad[:, 0]) * np.cos(coords_rad[:, 1])
                    y = np.cos(coords_rad[:, 0]) * np.sin(coords_rad[:, 1])
                    z = np.sin(coords_rad[:, 0])
                    
                    cls._reference_coords_3d = np.column_stack([x, y, z])
                    
                    # メモリ使用量を計測しながらKD-Treeを構築
                    before_memory = cls._get_current_memory_usage()
                    cls._kdtree = KDTree(cls._reference_coords_3d)
                    after_memory = cls._get_current_memory_usage()
                    
                    actual_memory = after_memory - before_memory
                    cls._memory_usage_mb = actual_memory
                    
                    logger.info(
                        f"KD-Tree initialized with {len(cls.COASTAL_REFERENCE_POINTS)} coastal reference points. "
                        f"Memory usage: {actual_memory:.1f}MB (estimated: {estimated_memory:.1f}MB)"
                    )
                    
                    cls._use_kdtree = True
                    
                except MemoryError:
                    logger.error("メモリ不足のためKD-Treeの構築に失敗しました。線形探索を使用します。")
                    cls._kdtree = None
                    cls._reference_coords_3d = None
                    cls._use_kdtree = False
    
    @classmethod
    def _get_current_memory_usage(cls) -> float:
        """現在のプロセスのメモリ使用量を取得（MB単位）"""
        try:
            import resource
            # Unix系システムの場合
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # macOSはバイト、Linuxはキロバイト単位
            if sys.platform == 'darwin':
                return usage / (1024 * 1024)
            else:
                return usage / 1024
        except ImportError:
            # Windowsやresourceモジュールが使えない場合
            # 簡易的な推定値を返す
            return 0.0
    
    @classmethod
    def is_coastal(cls, latitude: float, longitude: float, threshold_km: float | None = None) -> bool:
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
    def get_distance_to_coast(cls, latitude: float, longitude: float) -> float | None:
        """
        最も近い海岸線までの距離を取得（KD-Tree最適化版）
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            海岸線までの最短距離（km）
        """
        if not cls.COASTAL_REFERENCE_POINTS:
            return None
        
        # KD-Treeの初期化（初回のみ）
        cls._initialize_kdtree()
        
        # KD-Treeが使用不可の場合は線形探索にフォールバック
        if not cls._use_kdtree or cls._kdtree is None:
            return cls._get_distance_to_coast_linear(latitude, longitude)
        
        # クエリ点を3D座標に変換
        lat_rad, lon_rad = radians(latitude), radians(longitude)
        x = cos(lat_rad) * cos(lon_rad)
        y = cos(lat_rad) * sin(lon_rad)
        z = sin(lat_rad)
        query_point = np.array([x, y, z])
        
        # 最近傍点を検索（k=5で上位5点を取得し、より正確な距離を計算）
        k = min(5, len(cls.COASTAL_REFERENCE_POINTS))
        distances, indices = cls._kdtree.query(query_point, k=k)
        
        # indicesが単一値の場合は配列に変換
        if k == 1:
            indices = [indices]
        
        # 実際の球面距離を計算（上位k点のみ）
        min_distance = float('inf')
        for idx in indices:
            coastal_lat, coastal_lon = cls.COASTAL_REFERENCE_POINTS[idx]
            distance = cls._calculate_distance(
                latitude, longitude,
                coastal_lat, coastal_lon
            )
            if distance < min_distance:
                min_distance = distance
        
        return min_distance if min_distance != float('inf') else None
    
    @classmethod
    def _get_distance_to_coast_linear(cls, latitude: float, longitude: float) -> float | None:
        """線形探索による海岸線までの距離計算（フォールバック用）
        
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
    
    @classmethod
    def get_distances_to_coast_batch(cls, coordinates: list[Coordinate]) -> list[float | None]:
        """
        複数の座標に対して一括で海岸線までの距離を計算（KD-Tree最適化版）
        
        Args:
            coordinates: 緯度経度のリスト
            
        Returns:
            各座標の海岸線までの最短距離のリスト（km）
        """
        if not cls.COASTAL_REFERENCE_POINTS or not coordinates:
            return [None] * len(coordinates)
        
        # KD-Treeの初期化（初回のみ）
        cls._initialize_kdtree()
        
        # KD-Treeが使用不可の場合は線形探索にフォールバック
        if not cls._use_kdtree or cls._kdtree is None:
            return [cls._get_distance_to_coast_linear(lat, lon) for lat, lon in coordinates]
        
        results: list[float | None] = []
        
        # 座標を3D座標に一括変換
        query_points = []
        for lat, lon in coordinates:
            lat_rad, lon_rad = radians(lat), radians(lon)
            x = cos(lat_rad) * cos(lon_rad)
            y = cos(lat_rad) * sin(lon_rad)
            z = sin(lat_rad)
            query_points.append([x, y, z])
        
        query_array = np.array(query_points)
        
        # 最近傍点を一括検索
        k = min(5, len(cls.COASTAL_REFERENCE_POINTS))
        distances, indices = cls._kdtree.query(query_array, k=k)
        
        # 各クエリ点について実際の球面距離を計算
        for i, (lat, lon) in enumerate(coordinates):
            idx_list = indices[i] if k > 1 else [indices[i]]
            
            min_distance = float('inf')
            for idx in idx_list:
                coastal_lat, coastal_lon = cls.COASTAL_REFERENCE_POINTS[idx]
                distance = cls._calculate_distance(lat, lon, coastal_lat, coastal_lon)
                if distance < min_distance:
                    min_distance = distance
            
            results.append(min_distance if min_distance != float('inf') else None)
        
        return results
    
    @classmethod
    def get_memory_usage(cls) -> dict[str, float]:
        """メモリ使用量の情報を取得
        
        Returns:
            メモリ使用量情報の辞書
        """
        return {
            "kdtree_memory_mb": cls._memory_usage_mb,
            "max_memory_mb": cls.MAX_MEMORY_MB,
            "using_kdtree": cls._use_kdtree,
            "num_reference_points": len(cls.COASTAL_REFERENCE_POINTS)
        }
    
    @classmethod
    def set_memory_limit(cls, max_memory_mb: int) -> None:
        """メモリ使用量の上限を設定
        
        Args:
            max_memory_mb: メモリ使用量の上限（MB）
        """
        cls.MAX_MEMORY_MB = max_memory_mb
        # 既存のKD-Treeをクリアして再初期化を促す
        with cls._initialization_lock:
            cls._kdtree = None
            cls._reference_coords_3d = None
            cls._use_kdtree = True
            cls._memory_usage_mb = 0.0
        logger.info(f"メモリ制限を{max_memory_mb}MBに設定しました")
    
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
    def get_topographic_features(cls, latitude: float, longitude: float) -> TopographicFeatures:
        """
        地形的特徴を推定
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            地形的特徴
        """
        distance_to_coast = cls.get_distance_to_coast(latitude, longitude)
        
        # Initialize with default values
        is_coastal = False
        topographic_type = "unknown"
        
        if distance_to_coast is not None:
            if distance_to_coast <= 5:
                is_coastal = True
                topographic_type = "coastal"
            elif distance_to_coast <= 20:
                is_coastal = True
                topographic_type = "near_coastal"
            elif distance_to_coast <= 50:
                topographic_type = "plain"
            else:
                topographic_type = "inland"
                
                # 簡易的な山間部判定（中部地方の内陸など）
                if 35 <= latitude <= 37 and 137 <= longitude <= 139:
                    topographic_type = "mountainous"
        
        return TopographicFeatures(
            is_coastal=is_coastal,
            distance_to_coast_km=distance_to_coast,
            topographic_type=topographic_type
        )