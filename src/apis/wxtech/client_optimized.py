"""最適化されたWxTech APIクライアント実装案"""

from datetime import datetime, timedelta
import pytz
import logging
from typing import List

from src.apis.wxtech.client import WxTechAPIClient
from src.data.weather_data import WeatherForecastCollection

logger = logging.getLogger(__name__)


class OptimizedWxTechAPIClient(WxTechAPIClient):
    """最適化されたWxTech APIクライアント"""
    
    def get_forecast_for_next_day_hours_optimized(self, lat: float, lon: float) -> WeatherForecastCollection:
        """翌日の9, 12, 15, 18時のデータを最適に取得
        
        方式1: 個別取得（APIが特定時刻取得をサポートしている場合）
        方式2: 最小範囲取得（サポートしていない場合）
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        target_date = now_jst.date() + timedelta(days=1)
        target_hours = [9, 12, 15, 18]
        
        # 方式1: 個別取得を試みる
        if self._supports_specific_time_api():
            return self._fetch_individual_hours(lat, lon, target_date, target_hours)
        
        # 方式2: 最小範囲での取得
        return self._fetch_minimal_range(lat, lon, target_date, target_hours)
    
    def _supports_specific_time_api(self) -> bool:
        """APIが特定時刻取得をサポートしているかチェック"""
        # TODO: test_specific_time_parametersの結果を元に判定
        return False
    
    def _fetch_individual_hours(self, lat: float, lon: float, target_date, target_hours: List[int]) -> WeatherForecastCollection:
        """各時刻を個別に取得"""
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        forecasts = []
        
        for hour in target_hours:
            target_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            hours_ahead = int((target_dt - now_jst).total_seconds() / 3600)
            
            if hours_ahead <= 0:
                continue
            
            try:
                # 1時間分のみ取得
                response = self.get_forecast(lat, lon, forecast_hours=1, start_offset=hours_ahead)
                if response.forecasts:
                    forecasts.append(response.forecasts[0])
            except Exception as e:
                logger.error(f"個別取得エラー {hour}時: {e}")
        
        collection = WeatherForecastCollection()
        collection.forecasts = sorted(forecasts, key=lambda f: f.datetime)
        return collection
    
    def _fetch_minimal_range(self, lat: float, lon: float, target_date, target_hours: List[int]) -> WeatherForecastCollection:
        """最小範囲でのデータ取得（9時〜18時の10時間分のみ）"""
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        
        # 9時と18時の時刻を計算
        start_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=9)))
        end_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=18)))
        
        # 現在から9時までの時間
        hours_to_start = max(1, int((start_dt - now_jst).total_seconds() / 3600))
        # 9時から18時までは9時間
        duration = 9
        
        # 9時〜18時の範囲のみ取得
        logger.info(f"最適化: {hours_to_start}時間後から{duration}時間分のみ取得")
        
        # APIが開始オフセットをサポートしていない場合は、現在から18時までを取得
        hours_to_end = int((end_dt - now_jst).total_seconds() / 3600) + 1
        response = self.get_forecast(lat, lon, forecast_hours=hours_to_end)
        
        # 必要な4時点のデータを抽出
        selected_forecasts = []
        for hour in target_hours:
            target_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            
            # 最も近い予報を見つける
            closest = min(
                response.forecasts,
                key=lambda f: abs((f.datetime - target_dt).total_seconds()),
                default=None
            )
            if closest:
                selected_forecasts.append(closest)
        
        collection = WeatherForecastCollection()
        collection.forecasts = selected_forecasts
        return collection