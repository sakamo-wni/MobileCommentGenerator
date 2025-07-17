"""
天気データのコアモデル定義

WeatherForecastデータクラスとその基本的なプロパティを定義
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.data.weather_enums import WeatherCondition, WindDirection
from src.constants import (
    TEMPERATURE_MIN, TEMPERATURE_MAX,
    HUMIDITY_MIN, HUMIDITY_MAX,
    WIND_SPEED_MIN, WIND_SPEED_MAX,
    PRECIPITATION_THRESHOLD_LIGHT,
    PRECIPITATION_THRESHOLD_NONE,
    PRECIPITATION_THRESHOLD_LIGHT_RAIN,
    PRECIPITATION_THRESHOLD_MODERATE,
    PRECIPITATION_THRESHOLD_HEAVY,
    PRECIPITATION_THRESHOLD_VERY_HEAVY,
    WIND_SPEED_THRESHOLD_STRONG,
    TEMPERATURE_COMFORTABLE_MIN,
    TEMPERATURE_COMFORTABLE_MAX,
)


@dataclass
class WeatherForecast:
    """単一時点の天気予報データ"""

    location_id: str
    datetime: datetime
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: WindDirection
    weather_condition: WeatherCondition
    weather_description: str
    precipitation: float = 0.0
    cloud_coverage: float = 0.0
    visibility: float = 10.0
    uv_index: float = 0.0
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """データ検証"""
        # 温度の範囲チェック
        if not TEMPERATURE_MIN <= self.temperature <= TEMPERATURE_MAX:
            raise ValueError(
                f"Temperature {self.temperature}°C is out of valid range "
                f"({TEMPERATURE_MIN}°C - {TEMPERATURE_MAX}°C)"
            )
        
        # 湿度の範囲チェック
        if not HUMIDITY_MIN <= self.humidity <= HUMIDITY_MAX:
            raise ValueError(
                f"Humidity {self.humidity}% is out of valid range "
                f"({HUMIDITY_MIN}% - {HUMIDITY_MAX}%)"
            )
        
        # 風速の範囲チェック
        if not WIND_SPEED_MIN <= self.wind_speed <= WIND_SPEED_MAX:
            raise ValueError(
                f"Wind speed {self.wind_speed}m/s is out of valid range "
                f"({WIND_SPEED_MIN}m/s - {WIND_SPEED_MAX}m/s)"
            )

    @property
    def location(self) -> str:
        """後方互換性のためのプロパティ（非推奨）"""
        import warnings
        warnings.warn(
            "The 'location' property is deprecated. Use 'location_id' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.location_id
    
    @location.setter
    def location(self, value: str) -> None:
        """後方互換性のためのセッター（非推奨）"""
        import warnings
        warnings.warn(
            "The 'location' property is deprecated. Use 'location_id' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.location_id = value
    
    @property
    def is_rainy(self) -> bool:
        """雨天かどうか"""
        return self.weather_condition in {
            WeatherCondition.RAIN,
            WeatherCondition.HEAVY_RAIN,
            WeatherCondition.STORM,
            WeatherCondition.SEVERE_STORM,
            WeatherCondition.THUNDER,
        }

    @property
    def is_snowy(self) -> bool:
        """雪天かどうか"""
        return self.weather_condition in {
            WeatherCondition.SNOW,
            WeatherCondition.HEAVY_SNOW,
        }

    @property
    def is_extreme_weather(self) -> bool:
        """異常気象かどうか"""
        return self.weather_condition.is_special_condition()

    def is_severe_weather(self) -> bool:
        """悪天候かどうか（後方互換性のため）"""
        return self.is_extreme_weather
    
    @property
    def weather_code(self) -> int:
        """天気コード（後方互換性のため、非推奨）"""
        import warnings
        warnings.warn(
            "The 'weather_code' property is deprecated. Use 'weather_condition' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # weather_conditionからおおよその天気コードを返す
        code_mapping = {
            WeatherCondition.CLEAR: 100,
            WeatherCondition.PARTLY_CLOUDY: 101,
            WeatherCondition.CLOUDY: 200,
            WeatherCondition.RAIN: 300,
            WeatherCondition.HEAVY_RAIN: 301,
            WeatherCondition.SNOW: 400,
            WeatherCondition.HEAVY_SNOW: 401,
            WeatherCondition.STORM: 500,
            WeatherCondition.FOG: 600,
            WeatherCondition.THUNDER: 700,
            WeatherCondition.EXTREME_HEAT: 800,
            WeatherCondition.SEVERE_STORM: 900,
            WeatherCondition.UNKNOWN: 0,
        }
        return code_mapping.get(self.weather_condition, 0)
    
    @property
    def wind_direction_degrees(self) -> float:
        """風向きの角度（後方互換性のため、非推奨）"""
        import warnings
        warnings.warn(
            "The 'wind_direction_degrees' property is deprecated. Use 'wind_direction' enum instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # wind_directionから角度を計算
        direction_degrees = {
            WindDirection.NORTH: 0,
            WindDirection.NORTH_NORTHEAST: 22.5,
            WindDirection.NORTHEAST: 45,
            WindDirection.EAST_NORTHEAST: 67.5,
            WindDirection.EAST: 90,
            WindDirection.EAST_SOUTHEAST: 112.5,
            WindDirection.SOUTHEAST: 135,
            WindDirection.SOUTH_SOUTHEAST: 157.5,
            WindDirection.SOUTH: 180,
            WindDirection.SOUTH_SOUTHWEST: 202.5,
            WindDirection.SOUTHWEST: 225,
            WindDirection.WEST_SOUTHWEST: 247.5,
            WindDirection.WEST: 270,
            WindDirection.WEST_NORTHWEST: 292.5,
            WindDirection.NORTHWEST: 315,
            WindDirection.NORTH_NORTHWEST: 337.5,
            WindDirection.CALM: 0,
            WindDirection.VARIABLE: 0,
        }
        return direction_degrees.get(self.wind_direction, 0)

    @property
    def precipitation_level(self) -> str:
        """降水レベルを返す"""
        if self.precipitation < PRECIPITATION_THRESHOLD_NONE:
            return "none"
        elif self.precipitation < PRECIPITATION_THRESHOLD_LIGHT:
            return "very_light"
        elif self.precipitation < PRECIPITATION_THRESHOLD_LIGHT_RAIN:
            return "light"
        elif self.precipitation < PRECIPITATION_THRESHOLD_MODERATE:
            return "moderate"
        elif self.precipitation < PRECIPITATION_THRESHOLD_HEAVY:
            return "heavy"
        elif self.precipitation < PRECIPITATION_THRESHOLD_VERY_HEAVY:
            return "very_heavy"
        else:
            return "extreme"

    @property
    def is_comfortable_temperature(self) -> bool:
        """快適な温度範囲かどうか"""
        return TEMPERATURE_COMFORTABLE_MIN <= self.temperature <= TEMPERATURE_COMFORTABLE_MAX

    @property
    def is_strong_wind(self) -> bool:
        """強風かどうか"""
        return self.wind_speed >= WIND_SPEED_THRESHOLD_STRONG

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "location_id": self.location_id,
            "datetime": self.datetime.isoformat(),
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction.value,
            "weather_condition": self.weather_condition.value,
            "weather_description": self.weather_description,
            "precipitation": self.precipitation,
            "cloud_coverage": self.cloud_coverage,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeatherForecast:
        """辞書形式から作成"""
        return cls(
            location_id=data["location_id"],
            datetime=datetime.fromisoformat(data["datetime"]),
            temperature=float(data["temperature"]),
            feels_like=float(data["feels_like"]),
            humidity=float(data["humidity"]),
            pressure=float(data["pressure"]),
            wind_speed=float(data["wind_speed"]),
            wind_direction=WindDirection(data["wind_direction"]),
            weather_condition=WeatherCondition(data["weather_condition"]),
            weather_description=data["weather_description"],
            precipitation=float(data.get("precipitation", 0.0)),
            cloud_coverage=float(data.get("cloud_coverage", 0.0)),
            visibility=float(data.get("visibility", 10.0)),
            uv_index=float(data.get("uv_index", 0.0)),
            raw_data=data.get("raw_data", {}),
        )