"""
天気予報コレクションの定義

複数の天気予報データを管理するコレクションクラス
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

from src.data.weather_models import WeatherForecast
from src.data.weather_enums import WeatherCondition


@dataclass
class WeatherForecastCollection:
    """複数時点の天気予報を管理するコレクション"""

    location_id: str
    forecasts: list[WeatherForecast] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """予報データを時系列でソート"""
        self.forecasts.sort(key=lambda f: f.datetime)

    def __len__(self) -> int:
        """予報データ数を返す"""
        return len(self.forecasts)

    def __iter__(self) -> Iterator[WeatherForecast]:
        """予報データのイテレータを返す"""
        return iter(self.forecasts)

    def __getitem__(self, index: int) -> WeatherForecast:
        """インデックスで予報データを取得"""
        return self.forecasts[index]

    def add_forecast(self, forecast: WeatherForecast) -> None:
        """予報データを追加"""
        if forecast.location_id != self.location_id:
            raise ValueError(f"Location ID mismatch: expected {self.location_id}, got {forecast.location_id}")
        self.forecasts.append(forecast)
        self.forecasts.sort(key=lambda f: f.datetime)

    def get_forecast_at(self, target_datetime: datetime) -> WeatherForecast | None:
        """指定時刻の予報を取得（最も近い時刻の予報を返す）"""
        if not self.forecasts:
            return None
        
        # 最も近い時刻の予報を探す
        closest = min(self.forecasts, key=lambda f: abs((f.datetime - target_datetime).total_seconds()))
        return closest

    def get_forecasts_between(self, start: datetime, end: datetime) -> list[WeatherForecast]:
        """指定期間内の予報を取得"""
        return [f for f in self.forecasts if start <= f.datetime <= end]

    def get_latest_forecast(self) -> WeatherForecast | None:
        """最新の予報を取得"""
        return self.forecasts[-1] if self.forecasts else None

    def get_earliest_forecast(self) -> WeatherForecast | None:
        """最も古い予報を取得"""
        return self.forecasts[0] if self.forecasts else None

    def filter_by_condition(self, condition: WeatherCondition) -> list[WeatherForecast]:
        """特定の天気状況の予報のみを取得"""
        return [f for f in self.forecasts if f.weather_condition == condition]

    def has_extreme_weather(self) -> bool:
        """異常気象が含まれているかチェック"""
        return any(f.is_extreme_weather for f in self.forecasts)

    def get_temperature_range(self) -> tuple[float, float] | None:
        """温度範囲を取得"""
        if not self.forecasts:
            return None
        temperatures = [f.temperature for f in self.forecasts]
        return min(temperatures), max(temperatures)

    def get_precipitation_total(self) -> float:
        """総降水量を取得"""
        return sum(f.precipitation for f in self.forecasts)

    def to_dict(self) -> dict[str, any]:
        """辞書形式に変換"""
        return {
            "location_id": self.location_id,
            "created_at": self.created_at.isoformat(),
            "forecasts": [f.to_dict() for f in self.forecasts],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> WeatherForecastCollection:
        """辞書形式から作成"""
        collection = cls(
            location_id=data["location_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )
        for forecast_data in data.get("forecasts", []):
            forecast = WeatherForecast.from_dict(forecast_data)
            collection.add_forecast(forecast)
        return collection