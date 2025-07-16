"""
海岸線検出ユーティリティ（後方互換性のためのラッパー）

このファイルは後方互換性のために保持されています。
新しいコードでは src.utils.geography.coastal_detector パッケージを直接インポートしてください。
"""

# 後方互換性のため、すべてのエクスポートを再エクスポート
from src.utils.geography.coastal_detector import (
    CoastalDetector,
    COASTAL_REFERENCE_POINTS,
    Coordinate,
    haversine_distance
)

__all__ = [
    'CoastalDetector',
    'COASTAL_REFERENCE_POINTS',
    'Coordinate',
    'haversine_distance'
]