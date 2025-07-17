"""
天気関連の列挙型定義

天気状況と風向きの列挙型を定義
"""

from __future__ import annotations
from enum import Enum

from src.constants import (
    SPECIAL_WEATHER_PRIORITY_THRESHOLD,
    WIND_DIRECTION_MIN_DEGREES,
    WIND_DIRECTION_MAX_DEGREES,
)


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
        """天気の優先度を返す（数値が小さいほど優先度が高い）"""
        priorities = {
            self.SEVERE_STORM: 1,  # 最優先：大雨・嵐
            self.THUNDER: 2,       # 雷
            self.STORM: 3,         # 嵐
            self.HEAVY_RAIN: 4,    # 大雨
            self.HEAVY_SNOW: 5,    # 大雪
            self.FOG: 6,           # 霧
            self.EXTREME_HEAT: 7,  # 猛暑
            self.RAIN: 8,          # 雨
            self.SNOW: 9,          # 雪
            self.CLOUDY: 10,       # 曇り
            self.PARTLY_CLOUDY: 11,  # 曇り時々晴れ
            self.CLEAR: 12,        # 晴れ
            self.UNKNOWN: 99,      # 不明
        }
        return priorities.get(self, 99)

    def is_special_condition(self) -> bool:
        """特別な天気状況かどうかを判定"""
        return self.priority <= SPECIAL_WEATHER_PRIORITY_THRESHOLD

    def is_precipitation(self) -> bool:
        """降水を伴う天気かどうかを判定"""
        return self in {
            self.RAIN,
            self.HEAVY_RAIN,
            self.SNOW,
            self.HEAVY_SNOW,
            self.STORM,
            self.SEVERE_STORM,
            self.THUNDER,
        }

    def get_japanese_name(self) -> str:
        """天気状況の日本語名を返す"""
        names = {
            self.CLEAR: "晴れ",
            self.PARTLY_CLOUDY: "曇り時々晴れ",
            self.CLOUDY: "曇り",
            self.RAIN: "雨",
            self.HEAVY_RAIN: "大雨",
            self.SNOW: "雪",
            self.HEAVY_SNOW: "大雪",
            self.STORM: "嵐",
            self.FOG: "霧",
            self.THUNDER: "雷",
            self.EXTREME_HEAT: "猛暑",
            self.SEVERE_STORM: "大雨・嵐",
            self.UNKNOWN: "不明",
        }
        return names.get(self, "不明")


class WindDirection(Enum):
    """風向きの列挙型"""

    NORTH = "north"            # 北
    NORTH_NORTHEAST = "north_northeast"  # 北北東
    NORTHEAST = "northeast"    # 北東
    EAST_NORTHEAST = "east_northeast"    # 東北東
    EAST = "east"              # 東
    EAST_SOUTHEAST = "east_southeast"    # 東南東
    SOUTHEAST = "southeast"    # 南東
    SOUTH_SOUTHEAST = "south_southeast"  # 南南東
    SOUTH = "south"            # 南
    SOUTH_SOUTHWEST = "south_southwest"  # 南南西
    SOUTHWEST = "southwest"    # 南西
    WEST_SOUTHWEST = "west_southwest"    # 西南西
    WEST = "west"              # 西
    WEST_NORTHWEST = "west_northwest"    # 西北西
    NORTHWEST = "northwest"    # 北西
    NORTH_NORTHWEST = "north_northwest"  # 北北西
    CALM = "calm"              # 無風
    VARIABLE = "variable"      # 不定

    @classmethod
    def from_degrees(cls, degrees: float) -> WindDirection:
        """角度から風向きを取得
        
        Args:
            degrees: 風向きの角度（0-360度、北が0度）
            
        Returns:
            対応する風向き
        """
        if not isinstance(degrees, (int, float)):
            return cls.VARIABLE
            
        # 角度を0-360の範囲に正規化
        normalized_degrees = degrees % 360
        
        if normalized_degrees < WIND_DIRECTION_MIN_DEGREES or normalized_degrees > WIND_DIRECTION_MAX_DEGREES:
            return cls.CALM
        
        # 16方位に分割（22.5度ごと）
        directions = [
            (11.25, cls.NORTH),
            (33.75, cls.NORTH_NORTHEAST),
            (56.25, cls.NORTHEAST),
            (78.75, cls.EAST_NORTHEAST),
            (101.25, cls.EAST),
            (123.75, cls.EAST_SOUTHEAST),
            (146.25, cls.SOUTHEAST),
            (168.75, cls.SOUTH_SOUTHEAST),
            (191.25, cls.SOUTH),
            (213.75, cls.SOUTH_SOUTHWEST),
            (236.25, cls.SOUTHWEST),
            (258.75, cls.WEST_SOUTHWEST),
            (281.25, cls.WEST),
            (303.75, cls.WEST_NORTHWEST),
            (326.25, cls.NORTHWEST),
            (348.75, cls.NORTH_NORTHWEST),
            (360.0, cls.NORTH),
        ]
        
        for threshold, direction in directions:
            if normalized_degrees <= threshold:
                return direction
                
        return cls.NORTH

    def get_japanese_name(self) -> str:
        """風向きの日本語名を返す"""
        names = {
            self.NORTH: "北",
            self.NORTH_NORTHEAST: "北北東",
            self.NORTHEAST: "北東",
            self.EAST_NORTHEAST: "東北東",
            self.EAST: "東",
            self.EAST_SOUTHEAST: "東南東",
            self.SOUTHEAST: "南東",
            self.SOUTH_SOUTHEAST: "南南東",
            self.SOUTH: "南",
            self.SOUTH_SOUTHWEST: "南南西",
            self.SOUTHWEST: "南西",
            self.WEST_SOUTHWEST: "西南西",
            self.WEST: "西",
            self.WEST_NORTHWEST: "西北西",
            self.NORTHWEST: "北西",
            self.NORTH_NORTHWEST: "北北西",
            self.CALM: "無風",
            self.VARIABLE: "不定",
        }
        return names.get(self, "不定")