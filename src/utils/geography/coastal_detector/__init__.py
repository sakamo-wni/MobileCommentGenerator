"""
Coastal detector package

海岸線検出システム
"""

from .detector import CoastalDetector
from .coordinates import COASTAL_REFERENCE_POINTS, Coordinate
from .distance import haversine_distance

__all__ = [
    'CoastalDetector',
    'COASTAL_REFERENCE_POINTS',
    'Coordinate',
    'haversine_distance'
]