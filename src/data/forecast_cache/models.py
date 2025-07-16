"""
Forecast cache data models

予報キャッシュのデータモデル定義
"""

from __future__ import annotations
import ast
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any
from zoneinfo import ZoneInfo

from src.data.weather_data import WeatherForecast

# タイムゾーン定義
JST = ZoneInfo("Asia/Tokyo")


@dataclass
class ForecastCacheEntry:
    """予報キャッシュエントリ
    
    Attributes:
        location_name: 地点名
        forecast_datetime: 予報日時
        cached_at: キャッシュ保存日時
        temperature: 気温（℃）
        max_temperature: 最高気温（℃）
        min_temperature: 最低気温（℃）
        weather_condition: 天気状況
        weather_description: 天気の説明
        precipitation: 降水量（mm）
        humidity: 湿度（%）
        wind_speed: 風速（m/s）
        metadata: その他のメタデータ
    """
    
    location_name: str
    forecast_datetime: datetime
    cached_at: datetime
    temperature: float
    max_temperature: float | None = None
    min_temperature: float | None = None
    weather_condition: str = ""
    weather_description: str = ""
    precipitation: float = 0.0
    humidity: float = 0.0
    wind_speed: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_csv_row(self) -> list[str]:
        """CSV行として出力"""
        return [
            self.location_name,
            self.forecast_datetime.isoformat(),
            self.cached_at.isoformat(),
            str(self.temperature),
            str(self.max_temperature) if self.max_temperature is not None else "",
            str(self.min_temperature) if self.min_temperature is not None else "",
            self.weather_condition,
            self.weather_description,
            str(self.precipitation),
            str(self.humidity),
            str(self.wind_speed),
            str(self.metadata) if self.metadata else ""
        ]
    
    @classmethod
    def from_csv_row(cls, row: list[str]) -> "ForecastCacheEntry":
        """CSV行から復元"""
        # metadataを安全に評価
        metadata = {}
        if len(row) > 11 and row[11]:
            try:
                metadata = ast.literal_eval(row[11])
            except (ValueError, SyntaxError):
                # 評価できない場合は空の辞書
                metadata = {}
        
        return cls(
            location_name=row[0],
            forecast_datetime=datetime.fromisoformat(row[1]),
            cached_at=datetime.fromisoformat(row[2]),
            temperature=float(row[3]),
            max_temperature=float(row[4]) if row[4] else None,
            min_temperature=float(row[5]) if row[5] else None,
            weather_condition=row[6] if len(row) > 6 else "",
            weather_description=row[7] if len(row) > 7 else "",
            precipitation=float(row[8]) if len(row) > 8 and row[8] else 0.0,
            humidity=float(row[9]) if len(row) > 9 and row[9] else 0.0,
            wind_speed=float(row[10]) if len(row) > 10 and row[10] else 0.0,
            metadata=metadata
        )
    
    @classmethod
    def from_weather_forecast(cls, forecast: WeatherForecast, location_name: str) -> "ForecastCacheEntry":
        """WeatherForecastオブジェクトから生成
        
        Args:
            forecast: 天気予報データ
            location_name: 地点名
            
        Returns:
            ForecastCacheEntry インスタンス
        """
        # datetimeをJSTとして扱う
        forecast_dt = forecast.datetime
        if forecast_dt.tzinfo is None:
            forecast_dt = forecast_dt.replace(tzinfo=JST)
        elif forecast_dt.tzinfo != JST:
            forecast_dt = forecast_dt.astimezone(JST)
        
        cached_at = datetime.now(JST)
        
        return cls(
            location_name=location_name,
            forecast_datetime=forecast_dt,
            cached_at=cached_at,
            temperature=forecast.temperature,
            max_temperature=getattr(forecast, 'max_temperature', None),
            min_temperature=getattr(forecast, 'min_temperature', None),
            weather_condition=getattr(forecast, 'weather', ''),
            weather_description=getattr(forecast, 'weather_description', ''),
            precipitation=getattr(forecast, 'precipitation', 0.0),
            humidity=getattr(forecast, 'humidity', 0.0),
            wind_speed=getattr(forecast, 'wind_speed', 0.0),
            metadata={}
        )