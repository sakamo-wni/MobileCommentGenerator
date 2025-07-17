"""
weather_data.py の後方互換性を完全に保証するラッパー

古いコードが'location'パラメータを使用している場合に対応
"""

from __future__ import annotations
from typing import Any
import warnings

from src.data.weather_collection import WeatherForecastCollection as _WeatherForecastCollection
from src.data.weather_models import WeatherForecast
from src.data.weather_enums import WeatherCondition, WindDirection


class WeatherForecastCollection(_WeatherForecastCollection):
    """後方互換性のためのWeatherForecastCollectionラッパー"""
    
    def __init__(self, **kwargs):
        """初期化時に'location'パラメータを'location_id'に変換"""
        # 'location'パラメータが渡された場合の処理
        if 'location' in kwargs and 'location_id' not in kwargs:
            warnings.warn(
                "WeatherForecastCollection: 'location' parameter is deprecated, use 'location_id' instead",
                DeprecationWarning,
                stacklevel=2
            )
            kwargs['location_id'] = kwargs.pop('location')
        
        # 'generated_at'パラメータが渡された場合の処理
        if 'generated_at' in kwargs and 'created_at' not in kwargs:
            warnings.warn(
                "WeatherForecastCollection: 'generated_at' parameter is deprecated, use 'created_at' instead",
                DeprecationWarning,
                stacklevel=2
            )
            kwargs['created_at'] = kwargs.pop('generated_at')
        
        # 親クラスの初期化
        super().__init__(**kwargs)
    
    @property
    def location(self) -> str:
        """後方互換性のためのプロパティ"""
        warnings.warn(
            "WeatherForecastCollection.location is deprecated, use location_id instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.location_id
    
    @property
    def generated_at(self):
        """後方互換性のためのプロパティ"""
        warnings.warn(
            "WeatherForecastCollection.generated_at is deprecated, use created_at instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.created_at


# 再エクスポート（変更なし）
__all__ = [
    'WeatherCondition',
    'WindDirection', 
    'WeatherForecast',
    'WeatherForecastCollection',
]