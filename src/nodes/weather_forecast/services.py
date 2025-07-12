"""
Weather forecast node services

天気予報ノードで使用する各種サービスクラス
責務ごとに分離されたサービスを提供
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
import pytz

from src.data.location_manager import Location, get_location_manager
from src.data.weather_data import WeatherForecast, WeatherForecastCollection, WeatherCondition, WindDirection
from src.data.forecast_cache import save_forecast_to_cache, get_temperature_differences, get_forecast_cache
from src.apis.wxtech import WxTechAPIError
from src.apis.wxtech.client import WxTechAPIClient
from src.config.config_loader import load_config
from src.config.config import get_weather_config
from src.data.weather_trend import WeatherTrend
from src.nodes.weather_forecast.data_validator import WeatherDataValidator
from src.nodes.weather_forecast.constants import (
    API_MAX_RETRIES,
    API_INITIAL_RETRY_DELAY,
    API_RETRY_BACKOFF_MULTIPLIER,
    DEFAULT_TARGET_HOURS,
    DATE_BOUNDARY_HOUR,
    TREND_ANALYSIS_MIN_FORECASTS
)
from src.nodes.weather_forecast.messages import Messages


logger = logging.getLogger(__name__)


class LocationService:
    """地点情報の取得と検証を担当するサービス"""
    
    def __init__(self):
        self.location_manager = get_location_manager()
    
    def parse_location_string(self, location_name_raw: str) -> Tuple[str, Optional[float], Optional[float]]:
        """地点名文字列から地点名と座標を抽出
        
        Args:
            location_name_raw: 生の地点名文字列（"地点名,緯度,経度" 形式の場合あり）
            
        Returns:
            (地点名, 緯度, 経度) のタプル
        """
        provided_lat = None
        provided_lon = None
        
        if "," in location_name_raw:
            parts = location_name_raw.split(",")
            location_name = parts[0].strip()
            if len(parts) >= 3:
                try:
                    provided_lat = float(parts[1].strip())
                    provided_lon = float(parts[2].strip())
                    logger.info(
                        f"Extracted location name '{location_name}' with coordinates ({provided_lat}, {provided_lon})"
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid coordinates in '{location_name_raw}', will look up in LocationManager"
                    )
            else:
                logger.info(f"Extracted location name '{location_name}' from '{location_name_raw}'")
        else:
            location_name = location_name_raw.strip()
            
        return location_name, provided_lat, provided_lon
    
    def get_location_with_coordinates(
        self, 
        location_name: str, 
        provided_lat: Optional[float] = None,
        provided_lon: Optional[float] = None
    ) -> Location:
        """地点情報を取得（座標情報付き）
        
        Args:
            location_name: 地点名
            provided_lat: 提供された緯度（オプション）
            provided_lon: 提供された経度（オプション）
            
        Returns:
            Location オブジェクト
            
        Raises:
            ValueError: 地点が見つからない場合
        """
        location = self.location_manager.get_location(location_name)
        
        # LocationManagerで見つからない場合、提供された座標を使用
        if not location and provided_lat is not None and provided_lon is not None:
            logger.info(
                f"Location '{location_name}' not found in LocationManager, using provided coordinates"
            )
            # 疑似Locationオブジェクトを作成
            location = Location(
                name=location_name,
                normalized_name=location_name.lower(),
                latitude=provided_lat,
                longitude=provided_lon,
            )
        elif not location:
            raise ValueError(f"地点が見つかりません: {location_name}")
        
        if not location.latitude or not location.longitude:
            raise ValueError(f"地点 '{location_name}' の緯度経度情報がありません")
        
        return location


class WeatherAPIService:
    """天気予報API通信を担当するサービス"""
    
    def __init__(self, api_key: str):
        self.client = WxTechAPIClient(api_key)
        self.max_retries = API_MAX_RETRIES
        self.initial_retry_delay = API_INITIAL_RETRY_DELAY
        self.weather_config = get_weather_config()
    
    def fetch_forecast_with_retry(
        self, 
        lat: float, 
        lon: float,
        location_name: str
    ) -> WeatherForecastCollection:
        """リトライ機能付きで天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            location_name: 地点名（ログ用）
            
        Returns:
            WeatherForecastCollection
            
        Raises:
            WxTechAPIError: API通信エラー
            ValueError: データ取得失敗
        """
        
        retry_delay = self.initial_retry_delay
        forecast_collection = None
        
        for attempt in range(self.max_retries):
            try:
                # 最適化版の使用を判定
                if self.weather_config.use_optimized_forecast:
                    logger.info("最適化された予報取得を使用")
                    forecast_collection = self.client.get_forecast_for_next_day_hours_optimized(lat, lon)
                else:
                    forecast_collection = self.client.get_forecast_for_next_day_hours(lat, lon)
                
                # forecast_collectionが空でないことを確認
                if forecast_collection and forecast_collection.forecasts:
                    logger.info(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"天気予報データを正常に取得しました。"
                    )
                    return forecast_collection
                else:
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_retries}: "
                            f"天気予報データが空です。{retry_delay}秒後にリトライします。"
                        )
                        time.sleep(retry_delay)
                        retry_delay *= API_RETRY_BACKOFF_MULTIPLIER  # 指数バックオフ
                    else:
                        raise ValueError(
                            f"地点 '{location_name}' の天気予報データが取得できませんでした"
                        )
                        
            except WxTechAPIError as e:
                # リトライ可能なエラーかチェック
                if (e.error_type in ['network_error', 'timeout', 'server_error'] 
                    and attempt < self.max_retries - 1):
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"APIエラー ({e.error_type}). {retry_delay}秒後にリトライします。"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    # リトライ不可能なエラーまたは最後の試行の場合
                    self._handle_api_error(e)
                    raise
        
        raise ValueError("予期しないエラー: リトライループが正常に終了しませんでした")
    
    async def fetch_forecast_with_retry_async(
        self, 
        lat: float, 
        lon: float,
        location_name: str
    ) -> WeatherForecastCollection:
        """非同期版: リトライ機能付きで天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            location_name: 地点名（ログ用）
            
        Returns:
            WeatherForecastCollection
            
        Raises:
            WxTechAPIError: API通信エラー
            ValueError: データ取得失敗
        """
        
        retry_delay = self.initial_retry_delay
        forecast_collection = None
        
        for attempt in range(self.max_retries):
            try:
                # 最適化版の使用を判定
                if self.weather_config.use_optimized_forecast:
                    logger.info("最適化された予報取得を使用")
                    # 非同期版メソッドを呼び出し
                    forecast_collection = await self.client.get_forecast_for_next_day_hours_optimized_async(lat, lon)
                else:
                    # 通常の非同期版メソッド
                    forecast_collection = await self.client.get_forecast_async(lat, lon)
                
                # 予報データがある場合
                if forecast_collection and forecast_collection.forecasts:
                    logger.info(
                        f"🌤️ {location_name} の天気予報を取得しました。"
                        f"データ数: {len(forecast_collection.forecasts)}"
                    )
                    break
                else:
                    # データが取得できなかった場合、リトライするかチェック
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.max_retries}: "
                            f"天気データが空です。{retry_delay}秒後にリトライします。"
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                        continue
                    else:
                        raise ValueError(
                            f"地点 '{location_name}' の天気予報データが取得できませんでした"
                        )
                        
            except WxTechAPIError as e:
                # リトライ可能なエラーかチェック
                if (e.error_type in ['network_error', 'timeout', 'server_error'] 
                    and attempt < self.max_retries - 1):
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries}: "
                        f"APIエラー ({e.error_type}). {retry_delay}秒後にリトライします。"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= API_RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    # リトライ不可能なエラーまたは最後の試行の場合
                    self._handle_api_error(e)
                    raise
        
        raise ValueError("予期しないエラー: リトライループが正常に終了しませんでした")
    
    def _handle_api_error(self, error: WxTechAPIError) -> str:
        """APIエラーを処理してユーザー向けメッセージを生成
        
        Args:
            error: WxTechAPIError
            
        Returns:
            エラーメッセージ
        """
        error_msg = Messages.get_api_error(
            error.error_type or 'unknown',
            error=error
        )
        logger.error(
            f"気象APIエラー (type: {error.error_type}, status: {error.status_code}): {error_msg}"
        )
        return error_msg


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
        target_hours: Optional[List[int]] = None
    ) -> List[WeatherForecast]:
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
        forecasts: List[WeatherForecast], 
        target_time: datetime
    ) -> Optional[WeatherForecast]:
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
        period_forecasts: List[WeatherForecast]
    ) -> Optional[WeatherTrend]:
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
        forecasts: List[WeatherForecast], 
        target_datetime: datetime
    ) -> Optional[WeatherForecast]:
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
        forecasts: List[WeatherForecast]
    ) -> Optional[WeatherForecast]:
        """優先度に基づいて予報を選択（雨・猛暑日を優先）
        
        Args:
            forecasts: 予報リスト（9, 12, 15, 18時）
            
        Returns:
            優先度に基づいて選択された予報
        """
        return self.validator.select_priority_forecast(forecasts)


class CacheService:
    """キャッシュ処理を担当するサービス"""
    
    def __init__(self):
        self.cache = get_forecast_cache()
    
    def save_forecasts(
        self, 
        selected_forecast: WeatherForecast,
        all_forecasts: List[WeatherForecast],
        location_name: str
    ) -> None:
        """予報データをキャッシュに保存
        
        Args:
            selected_forecast: 選択された予報
            all_forecasts: 全予報データ
            location_name: 地点名
        """
        try:
            # 選択された予報データを保存
            save_forecast_to_cache(selected_forecast, location_name)
            
            # タイムライン表示用に必要な時間帯のデータのみを保存
            # 翌日の9, 12, 15, 18時の前後1時間（8-10時、11-13時、14-16時、17-19時）
            jst = pytz.timezone("Asia/Tokyo")
            target_hours = [(8, 10), (11, 13), (14, 16), (17, 19)]
            
            filtered_forecasts = []
            for forecast in all_forecasts:
                forecast_hour = forecast.datetime.astimezone(jst).hour
                for start_hour, end_hour in target_hours:
                    if start_hour <= forecast_hour <= end_hour:
                        filtered_forecasts.append(forecast)
                        break
            
            # フィルタリングされた予報データをキャッシュに保存
            for forecast in filtered_forecasts:
                try:
                    self.cache.save_forecast(forecast, location_name)
                except Exception as forecast_save_error:
                    logger.debug(f"個別予報保存に失敗: {forecast_save_error}")
                    continue
                    
            logger.info(
                f"予報データをキャッシュに保存: {location_name} "
                f"(全{len(all_forecasts)}件中{len(filtered_forecasts)}件を保存)"
            )
        except Exception as e:
            logger.warning(f"キャッシュ保存に失敗: {e}")
            # キャッシュ保存の失敗は致命的エラーではないので続行


class TemperatureAnalysisService:
    """気温分析を担当するサービス"""
    
    def calculate_temperature_differences(
        self, 
        forecast: WeatherForecast, 
        location_name: str
    ) -> Dict[str, Optional[float]]:
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