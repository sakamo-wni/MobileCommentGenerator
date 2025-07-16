"""コメント生成に関する設定"""

from __future__ import annotations
from dataclasses import dataclass

from src.data.weather_data import WeatherCondition


@dataclass
class CommentConfig:
    """コメント生成の設定"""
    
    # 温度閾値
    heat_warning_threshold: float = 30.0  # 熱中症警告温度
    cold_warning_threshold: float = 15.0  # 防寒警告温度
    
    # トレンド分析期間
    trend_hours_ahead: int = 12  # 気象変化を分析する時間（時間）
    
    # 天気スコア（良い天気ほど高いスコア）
    weather_scores: dict[WeatherCondition, int] = None
    
    def __post_init__(self):
        if self.weather_scores is None:
            self.weather_scores = {
                WeatherCondition.CLEAR: 5,
                WeatherCondition.PARTLY_CLOUDY: 4,
                WeatherCondition.CLOUDY: 3,
                WeatherCondition.RAIN: 2,
                WeatherCondition.HEAVY_RAIN: 0,
                WeatherCondition.SNOW: 1,
                WeatherCondition.HEAVY_SNOW: 0,
                WeatherCondition.STORM: 0,
                WeatherCondition.FOG: 2,
                WeatherCondition.UNKNOWN: 2,
            }


# シングルトンインスタンス
_config = None


def get_comment_config() -> CommentConfig:
    """コメント設定を取得"""
    global _config
    if _config is None:
        _config = CommentConfig()
    return _config
