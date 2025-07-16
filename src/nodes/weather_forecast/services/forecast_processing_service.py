"""
Forecast processing service for weather forecast node

天気予報データの処理を担当するサービス
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
import pytz
from src.data.weather_data import WeatherForecast, WeatherForecastCollection
from src.data.weather_trend import WeatherTrend
from src.nodes.weather_forecast.data_validator import WeatherDataValidator
from src.nodes.weather_forecast.constants import (
    DEFAULT_TARGET_HOURS,
    DATE_BOUNDARY_HOUR,
    TREND_ANALYSIS_MIN_FORECASTS
)

logger = logging.getLogger(__name__)


class ForecastProcessingService:
    """天気予報データの処理を担当するサービス"""
    
    def __init__(self):
        self.validator = WeatherDataValidator()
        self.jst = pytz.timezone("Asia/Tokyo")
    
    def get_target_date(self, now_jst: datetime, date_boundary_hour: int = DATE_BOUNDARY_HOUR) -> datetime.date:
        """対象日を計算
        
        Args:
            now_jst: 現在時刻（JST）
            date_boundary_hour: 境界時刻（デフォルト: 6時）
            
        Returns:
            対象日
        """
        if now_jst.hour < date_boundary_hour:
            # 深夜〜早朝は当日を対象
            return now_jst.date()
        else:
            # 境界時刻以降は翌日を対象
            return now_jst.date() + timedelta(days=1)
    
    def extract_period_forecasts(
        self, 
        forecast_collection: WeatherForecastCollection,
        target_date: datetime.date,
        target_hours: list[int | None] = None
    ) -> list[WeatherForecast]:
        """指定時刻の予報を抽出
        
        Args:
            forecast_collection: 予報コレクション
            target_date: 対象日
            target_hours: 対象時刻のリスト（デフォルト: [9, 12, 15, 18]）
            
        Returns:
            抽出された予報のリスト
        """
        if target_hours is None:
            target_hours = DEFAULT_TARGET_HOURS
        
        target_times = [
            self.jst.localize(
                datetime.combine(target_date, datetime.min.time().replace(hour=hour))
            )
            for hour in target_hours
        ]
        
        period_forecasts = []
        logger.info(f"Total forecasts in collection: {len(forecast_collection.forecasts)}")
        
        for target_time in target_times:
            closest_forecast = self._find_closest_forecast(
                forecast_collection.forecasts, 
                target_time
            )
            
            if closest_forecast:
                period_forecasts.append(closest_forecast)
                # デバッグ: 実際に選択された時刻と降水量を詳細に記録
                logger.info(
                    f"目標時刻 {target_time.strftime('%H:%M')} → "
                    f"実際の予報時刻: {closest_forecast.datetime.strftime('%Y-%m-%d %H:%M')}, "
                    f"天気: {closest_forecast.weather_description}, "
                    f"降水量: {closest_forecast.precipitation}mm"
                )
            else:
                logger.warning(f"No forecast found for target time {target_time.strftime('%H:%M')}")
        
        return period_forecasts
    
    def _find_closest_forecast(
        self, 
        forecasts: list[WeatherForecast], 
        target_time: datetime
    ) -> WeatherForecast | None:
        """目標時刻に最も近い予報を見つける
        
        Args:
            forecasts: 予報リスト
            target_time: 目標時刻
            
        Returns:
            最も近い予報（見つからない場合はNone）
        """
        closest_forecast = None
        min_diff = float('inf')
        
        # デバッグ: 利用可能な予報時刻を記録
        available_times = []
        for forecast in forecasts:
            forecast_dt = forecast.datetime
            if forecast_dt.tzinfo is None:
                forecast_dt = self.jst.localize(forecast_dt)
            if forecast_dt.date() == target_time.date():
                available_times.append(forecast_dt.strftime('%H:%M'))
        
        if available_times:
            logger.debug(f"目標時刻 {target_time.strftime('%H:%M')} に対して利用可能な予報時刻: {sorted(available_times)}")
        
        for forecast in forecasts:
            # forecastのdatetimeがnaiveな場合はJSTとして扱う
            forecast_dt = forecast.datetime
            if forecast_dt.tzinfo is None:
                forecast_dt = self.jst.localize(forecast_dt)
            
            # 目標時刻との差を計算
            diff = abs((forecast_dt - target_time).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_forecast = forecast
        
        return closest_forecast
    
    def analyze_weather_trend(
        self, 
        period_forecasts: list[WeatherForecast]
    ) -> WeatherTrend | None:
        """気象変化傾向を分析
        
        Args:
            period_forecasts: 期間の予報リスト
            
        Returns:
            WeatherTrend オブジェクト（データ不足の場合はNone）
        """
        if len(period_forecasts) >= TREND_ANALYSIS_MIN_FORECASTS:
            weather_trend = WeatherTrend.from_forecasts(period_forecasts)
            logger.info(f"気象変化傾向: {weather_trend.get_summary()}")
            return weather_trend
        else:
            logger.warning(
                f"気象変化分析に十分な予報データがありません: {len(period_forecasts)}件"
            )
            return None
    
    def select_forecast_by_time(
        self, 
        forecasts: list[WeatherForecast], 
        target_datetime: datetime
    ) -> WeatherForecast | None:
        """ターゲット時刻に最も近い予報を選択
        
        Args:
            forecasts: 予報リスト
            target_datetime: ターゲット時刻
            
        Returns:
            選択された予報
        """
        return self.validator.select_forecast_by_time(forecasts, target_datetime)
    
    def select_priority_forecast(
        self, 
        forecasts: list[WeatherForecast]
    ) -> WeatherForecast | None:
        """優先度に基づいて予報を選択（雨・猛暑日を優先）
        
        Args:
            forecasts: 予報リスト（9, 12, 15, 18時）
            
        Returns:
            優先度に基づいて選択された予報
        """
        return self.validator.select_priority_forecast(forecasts)