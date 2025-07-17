"""天気サマリー生成機能"""

from __future__ import annotations
import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class WeatherSummaryGenerator:
    """天気データのサマリー情報を生成するクラス"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_weather_summary(cache_key: str, period_forecasts_tuple: tuple) -> tuple[bool, float]:
        """天気サマリーを取得（LRUキャッシュ付き）
        
        Args:
            cache_key: キャッシュ用のキー
            period_forecasts_tuple: (降水量, 気温)のタプルのタプル
            
        Returns:
            (has_rain_in_timeline, max_temp_in_timeline): 雨の有無と最高気温
        """
        has_rain_in_timeline = False
        max_temp_in_timeline = 0.0
        
        # タプルの各要素は(precipitation, temperature)のペア
        for precipitation, temperature in period_forecasts_tuple:
            if precipitation > 0:
                has_rain_in_timeline = True
            if temperature > max_temp_in_timeline:
                max_temp_in_timeline = temperature
        
        return has_rain_in_timeline, max_temp_in_timeline
    
    @staticmethod
    def analyze_weather_timeline(
        weather_data: Any,
        state: Any | None = None
    ) -> tuple[bool, float, str]:
        """天気の時系列データを分析
        
        Args:
            weather_data: 天気予報データ
            state: コメント生成の状態
            
        Returns:
            (has_rain_in_timeline, max_temp_in_timeline, cache_key): 
            雨の有無、最高気温、キャッシュキー
        """
        has_rain_in_timeline = False
        max_temp_in_timeline = weather_data.temperature  # デフォルトは現在の温度
        
        # キャッシュキーの生成
        cache_key = f"{weather_data.datetime}_{weather_data.location_id if hasattr(weather_data, 'location_id') else ''}"
        
        if state and hasattr(state, 'generation_metadata'):
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            logger.debug(f"period_forecastsを取得: {len(period_forecasts)}件")
            
            if period_forecasts:
                # タプルを使用して効率的にキャッシュ
                period_forecasts_tuple = tuple(
                    (getattr(f, 'precipitation', 0), getattr(f, 'temperature', 0))
                    for f in period_forecasts
                )
                
                # LRUキャッシュを使用して取得
                has_rain_in_timeline, max_temp_in_timeline = WeatherSummaryGenerator.get_weather_summary(
                    cache_key, period_forecasts_tuple
                )
                
                if has_rain_in_timeline:
                    logger.debug(f"4時点予報で雨を検出（LRUキャッシュ使用）")
            else:
                # period_forecastsが空の場合、weather_timelineをフォールバック
                weather_timeline = state.generation_metadata.get('weather_timeline', {})
                future_forecasts = weather_timeline.get('future_forecasts', [])
                for forecast in future_forecasts:
                    if forecast.get('precipitation', 0) > 0:
                        has_rain_in_timeline = True
                    temp = forecast.get('temperature', 0)
                    if temp > max_temp_in_timeline:
                        max_temp_in_timeline = temp
        
        return has_rain_in_timeline, max_temp_in_timeline, cache_key