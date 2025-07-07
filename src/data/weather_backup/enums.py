"""
天気関連の列挙型定義

天気状況と風向きの列挙型
"""

from enum import Enum


class WeatherCondition(Enum):
    """天気状況の列挙型"""

    CLEAR = "clear"  # 晴れ
    PARTLY_CLOUDY = "partly_cloudy"  # 曇り時々晴れ
    CLOUDY = "cloudy"  # 曇り
    RAIN = "rain"  # 雨
    HEAVY_RAIN = "heavy_rain"  # 大雨
    SNOW = "snow"  # 雪
    HEAVY_SNOW = "heavy_snow"  # 大雪
    STORM = "storm"  # 嵐
    FOG = "fog"  # 霧
    THUNDER = "thunder"  # 雷
    EXTREME_HEAT = "extreme_heat"  # 猫暮
    SEVERE_STORM = "severe_storm"  # 大雨・嵐
    UNKNOWN = "unknown"  # 不明
    
    @property
    def priority(self) -> int:
        """天気状況の優先度を返す（数値が大きいほど優先度が高い）
        
        特殊な気象状況（雷、濃霧、嵐など）を優先的に扱うための優先度設定
        """
        priority_map = {
            "severe_storm": 12,  # 大雨・嵐 - 最高優先
            "thunder": 11,       # 雷
            "extreme_heat": 10,  # 猫暮
            "storm": 9,          # 嵐
            "fog": 8,            # 霧
            "heavy_snow": 7,     # 大雪
            "heavy_rain": 6,     # 大雨
            "snow": 5,           # 雪
            "rain": 4,           # 雨
            "cloudy": 3,         # 曇り
            "partly_cloudy": 2,  # 曇り時々晴れ
            "clear": 1,          # 晴れ
            "unknown": 0         # 不明
        }
        return priority_map.get(self.value, 0)
    
    @property
    def is_special_condition(self) -> bool:
        """特殊な気象状況かどうかを判定"""
        special_conditions = [
            WeatherCondition.THUNDER,
            WeatherCondition.FOG,
            WeatherCondition.STORM,
            WeatherCondition.EXTREME_HEAT,
            WeatherCondition.SEVERE_STORM
        ]
        return self in special_conditions


class WindDirection(Enum):
    """風向きの列挙型"""

    NORTH = "north"  # 北
    NORTHEAST = "northeast"  # 北東
    EAST = "east"  # 東
    SOUTHEAST = "southeast"  # 南東
    SOUTH = "south"  # 南
    SOUTHWEST = "southwest"  # 南西
    WEST = "west"  # 西
    NORTHWEST = "northwest"  # 北西
    CALM = "calm"  # 無風
    VARIABLE = "variable"  # 変動