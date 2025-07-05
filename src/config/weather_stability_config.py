"""天気安定性判定のための設定"""

from dataclasses import dataclass
from typing import List


@dataclass
class WeatherStabilityConfig:
    """天気安定性判定の設定"""
    
    # 時間帯設定
    target_hours: List[int] = None
    minimum_data_points: int = 4
    
    # 変化判定の閾値
    weather_change_threshold: int = 2  # 「変わりやすい」と判定する変化回数
    
    # 天候パラメータの閾値
    cloudy_precipitation_threshold: float = 1.0  # mm/h
    cloudy_wind_speed_threshold: float = 10.0  # m/s
    
    # 不安定パターン
    unstable_patterns: List[str] = None
    
    def __post_init__(self):
        if self.target_hours is None:
            self.target_hours = [9, 12, 15, 18]
        
        if self.unstable_patterns is None:
            self.unstable_patterns = [
                "変わりやすい",
                "ところにより",
                "所により",
                "一時",
                "時々",
                "のち",
                "変化",
                "不安定",
                "にわか雨",
                "急な雨"
            ]


# デフォルト設定
default_stability_config = WeatherStabilityConfig()