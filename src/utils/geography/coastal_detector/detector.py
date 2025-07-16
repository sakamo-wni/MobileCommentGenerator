"""
Coastal detector main class

海岸線検出のメインクラス
"""

from __future__ import annotations
import logging
import numpy as np
from scipy.spatial import KDTree
import sys
import threading
import weakref
from typing import ClassVar, Optional

from src.types.workflow_types import TopographicFeatures
from .coordinates import COASTAL_REFERENCE_POINTS, Coordinate
from .distance import haversine_distance, estimate_memory_usage_mb, find_nearest_distance_linear

logger = logging.getLogger(__name__)


class CoastalDetector:
    """緯度経度情報を使用して海岸地域を検出
    
    メモリ使用量の制限付きKD-Tree実装：
    - KD-Treeのメモリ使用量を推定
    - メモリ制限を超える場合は従来の線形探索にフォールバック
    - スレッドセーフな初期化
    """
    
    # メモリ使用量の上限（デフォルト: 50MB）
    MAX_MEMORY_MB: ClassVar[int] = 50
    
    # KD-Treeインスタンス（遅延初期化）
    _kdtree = None
    _kdtree_lock = threading.Lock()
    _kdtree_built = False
    _use_kdtree = None  # None: 未決定, True: 使用, False: 不使用
    
    # 弱参照によるインスタンス管理
    _instances = weakref.WeakSet()
    
    def __init__(self):
        """初期化"""
        self._instances.add(self)
    
    @classmethod
    def _check_memory_usage(cls) -> bool:
        """メモリ使用量をチェックしてKD-Treeを使用するか決定
        
        Returns:
            KD-Treeを使用する場合True
        """
        if cls._use_kdtree is not None:
            return cls._use_kdtree
            
        # 推定メモリ使用量を計算
        estimated_mb = estimate_memory_usage_mb(len(COASTAL_REFERENCE_POINTS))
        
        # メモリ制限チェック
        if estimated_mb > cls.MAX_MEMORY_MB:
            logger.warning(
                f"KD-Treeのメモリ使用量 ({estimated_mb:.1f}MB) が制限 ({cls.MAX_MEMORY_MB}MB) を超えるため、"
                f"線形探索を使用します"
            )
            cls._use_kdtree = False
        else:
            logger.info(f"KD-Treeを使用します (推定メモリ: {estimated_mb:.1f}MB)")
            cls._use_kdtree = True
            
        return cls._use_kdtree
    
    @classmethod
    def _build_kdtree(cls) -> bool:
        """KD-Treeを構築（スレッドセーフ）
        
        Returns:
            構築に成功した場合True
        """
        if not cls._check_memory_usage():
            return False
            
        with cls._kdtree_lock:
            if cls._kdtree_built:
                return True
                
            try:
                # 座標をラジアンに変換してnumpy配列に
                coords_rad = np.array([
                    [np.radians(lat), np.radians(lon)]
                    for lat, lon in COASTAL_REFERENCE_POINTS
                ])
                
                cls._kdtree = KDTree(coords_rad)
                cls._kdtree_built = True
                logger.info("KD-Treeの構築が完了しました")
                return True
                
            except Exception as e:
                logger.error(f"KD-Tree構築エラー: {e}")
                cls._use_kdtree = False
                return False
    
    def is_coastal(self, latitude: float, longitude: float, 
                   threshold_km: float = 10.0) -> bool:
        """指定地点が海岸地域かどうか判定
        
        Args:
            latitude: 緯度
            longitude: 経度
            threshold_km: 海岸線からの距離閾値（km）
            
        Returns:
            海岸地域の場合True
        """
        distance = self.distance_to_coast(latitude, longitude)
        return distance is not None and distance <= threshold_km
    
    def distance_to_coast(self, latitude: float, longitude: float) -> Optional[float]:
        """海岸線までの最短距離を計算
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            海岸線までの距離（km）、計算できない場合はNone
        """
        # 入力検証
        if not (-90 <= latitude <= 90):
            logger.error(f"無効な緯度: {latitude}")
            return None
        if not (-180 <= longitude <= 180):
            logger.error(f"無効な経度: {longitude}")
            return None
        
        # KD-Treeの使用を試みる
        if self._check_memory_usage() and self._build_kdtree():
            try:
                # KD-Treeで最近傍探索
                coords_rad = np.array([np.radians(latitude), np.radians(longitude)])
                distance_rad, _ = self._kdtree.query(coords_rad)
                
                # ラジアン距離をkmに変換（簡易式）
                R = 6371  # 地球の半径（km）
                distance_km = distance_rad * R
                
                return distance_km
                
            except Exception as e:
                logger.error(f"KD-Tree探索エラー: {e}")
                # フォールバック
        
        # 線形探索にフォールバック
        return find_nearest_distance_linear(latitude, longitude, COASTAL_REFERENCE_POINTS)
    
    def get_topographic_features(self, latitude: float, longitude: float) -> TopographicFeatures:
        """地形特徴を取得
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            地形特徴オブジェクト
        """
        distance = self.distance_to_coast(latitude, longitude)
        
        # 海岸地域の判定（段階的）
        if distance is None:
            is_coastal = False
            is_near_coast = False
        else:
            is_coastal = distance <= 10.0      # 10km以内
            is_near_coast = distance <= 20.0   # 20km以内
        
        # 山間部・内陸部の簡易判定
        # 実際には標高データが必要だが、ここでは海岸からの距離で代用
        is_mountainous = distance is not None and distance > 50.0
        is_inland = distance is not None and distance > 30.0
        
        return TopographicFeatures(
            is_coastal=is_coastal,
            is_mountainous=is_mountainous,
            is_inland=is_inland,
            distance_to_coast_km=distance,
            is_near_coast=is_near_coast
        )
    
    @classmethod
    def cleanup(cls):
        """リソースのクリーンアップ"""
        with cls._kdtree_lock:
            cls._kdtree = None
            cls._kdtree_built = False
            cls._use_kdtree = None
        logger.info("CoastalDetectorのリソースをクリーンアップしました")
    
    def __del__(self):
        """デストラクタ"""
        # 最後のインスタンスが削除される時にクリーンアップ
        if not self._instances:
            self.cleanup()