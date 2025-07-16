"""類似度計算の設定"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SimilarityConfig:
    """類似度計算の設定値"""
    
    # 温度差の閾値（この値で類似度が0になる）
    temperature_diff_threshold: float = 10.0
    
    # 湿度差の閾値（この値で類似度が0になる）
    humidity_diff_threshold: float = 50.0
    
    # 重み付け設定
    weather_condition_weight: float = 0.5
    temperature_weight: float = 0.3
    humidity_weight: float = 0.2
    
    # デフォルトの類似度閾値
    default_similarity_threshold: float = 0.7


# シングルトンインスタンス
_similarity_config = None


def get_similarity_config() -> SimilarityConfig:
    """類似度設定を取得"""
    global _similarity_config
    if _similarity_config is None:
        _similarity_config = SimilarityConfig()
    return _similarity_config