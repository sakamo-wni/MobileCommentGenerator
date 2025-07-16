"""
Temperature analysis service for weather forecast node

気温分析を担当するサービス
"""

from __future__ import annotations

import logging
from typing import Optional
from src.data.weather_data import WeatherForecast
from src.data.forecast_cache import get_temperature_differences

logger = logging.getLogger(__name__)


class TemperatureAnalysisService:
    """気温分析を担当するサービス"""
    
    def calculate_temperature_differences(
        self, 
        forecast: WeatherForecast, 
        location_name: str
    ) -> dict[str, Optional[float]]:
        """気温差を計算
        
        Args:
            forecast: 予報データ
            location_name: 地点名
            
        Returns:
            気温差の辞書
        """
        try:
            temperature_differences = get_temperature_differences(forecast, location_name)
            
            if temperature_differences.get("previous_day_diff") is not None:
                logger.info(
                    f"前日との気温差: {temperature_differences['previous_day_diff']:.1f}℃"
                )
            if temperature_differences.get("twelve_hours_ago_diff") is not None:
                logger.info(
                    f"12時間前との気温差: {temperature_differences['twelve_hours_ago_diff']:.1f}℃"
                )
            if temperature_differences.get("daily_range") is not None:
                logger.info(
                    f"日較差: {temperature_differences['daily_range']:.1f}℃"
                )
                
            return temperature_differences
            
        except Exception as e:
            logger.warning(f"気温差の計算に失敗: {e}")
            # 気温差計算の失敗も致命的エラーではないので空の辞書を返す
            return {}