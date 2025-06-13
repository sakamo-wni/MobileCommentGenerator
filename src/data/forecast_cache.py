"""
天気予報キャッシュシステム

地点ごとの予報結果をCSVファイルで管理し、
前日との気温差や日較差の比較を可能にする
"""

import ast
import csv
import os
import re
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Iterator
from pathlib import Path
from zoneinfo import ZoneInfo

from src.data.weather_data import WeatherForecast
from src.config.weather_config import get_config

logger = logging.getLogger(__name__)

# タイムゾーン定義
JST = ZoneInfo("Asia/Tokyo")


def ensure_jst(dt: datetime) -> datetime:
    """datetimeオブジェクトをJSTとして確実に扱う
    
    Args:
        dt: datetime オブジェクト
        
    Returns:
        JSTタイムゾーン付きのdatetime
    """
    if dt.tzinfo is None:
        # naiveな場合はJSTとして扱う
        return dt.replace(tzinfo=JST)
    elif dt.tzinfo != JST:
        # 他のタイムゾーンの場合はJSTに変換
        return dt.astimezone(JST)
    else:
        # 既にJSTの場合はそのまま返す
        return dt


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
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    weather_condition: str = ""
    weather_description: str = ""
    precipitation: float = 0.0
    humidity: float = 0.0
    wind_speed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_csv_row(self) -> List[str]:
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
    def from_csv_row(cls, row: List[str]) -> "ForecastCacheEntry":
        """CSV行から作成"""
        try:
            # 必須フィールドの解析
            location_name = row[0]
            
            # datetimeのタイムゾーン処理
            forecast_datetime = ensure_jst(datetime.fromisoformat(row[1]))
            cached_at = ensure_jst(datetime.fromisoformat(row[2]))
                
            temperature = float(row[3])
            
            # オプショナルフィールドの解析
            max_temperature = float(row[4]) if row[4] and row[4] != "" else None
            min_temperature = float(row[5]) if row[5] and row[5] != "" else None
            weather_condition = row[6] if len(row) > 6 else ""
            weather_description = row[7] if len(row) > 7 else ""
            precipitation = float(row[8]) if len(row) > 8 and row[8] else 0.0
            humidity = float(row[9]) if len(row) > 9 and row[9] else 0.0
            wind_speed = float(row[10]) if len(row) > 10 and row[10] else 0.0
            
            # メタデータの解析
            metadata = {}
            if len(row) > 11 and row[11]:
                try:
                    metadata = ast.literal_eval(row[11])  # 安全な評価関数を使用
                    if not isinstance(metadata, dict):
                        metadata = {}
                except (ValueError, SyntaxError) as e:
                    logger.warning(f"メタデータの解析に失敗: {e}")
                    metadata = {}
            
            return cls(
                location_name=location_name,
                forecast_datetime=forecast_datetime,
                cached_at=cached_at,
                temperature=temperature,
                max_temperature=max_temperature,
                min_temperature=min_temperature,
                weather_condition=weather_condition,
                weather_description=weather_description,
                precipitation=precipitation,
                humidity=humidity,
                wind_speed=wind_speed,
                metadata=metadata
            )
        except (ValueError, IndexError) as e:
            raise ValueError(f"CSV行の解析に失敗しました: {e}")
    
    @classmethod
    def from_weather_forecast(cls, weather_forecast: WeatherForecast, location_name: str) -> "ForecastCacheEntry":
        """WeatherForecastオブジェクトから作成"""
        # 現在時刻をJSTで取得
        cached_at = datetime.now(JST)
        
        # forecast_datetimeがnaiveの場合はJSTとして扱う
        forecast_dt = weather_forecast.datetime
        forecast_dt = ensure_jst(forecast_dt)
        
        return cls(
            location_name=location_name,
            forecast_datetime=forecast_dt,
            cached_at=cached_at,
            temperature=weather_forecast.temperature,
            weather_condition=weather_forecast.weather_condition.value,
            weather_description=weather_forecast.weather_description,
            precipitation=weather_forecast.precipitation,
            humidity=weather_forecast.humidity,
            wind_speed=weather_forecast.wind_speed,
            metadata={
                "weather_code": weather_forecast.weather_code,
                "wind_direction": weather_forecast.wind_direction.value,
                "wind_direction_degrees": weather_forecast.wind_direction_degrees,
                "pressure": weather_forecast.pressure,
                "visibility": weather_forecast.visibility,
                "uv_index": weather_forecast.uv_index,
                "confidence": weather_forecast.confidence
            }
        )


class ForecastCache:
    """予報キャッシュ管理クラス"""
    
    def __init__(self, cache_dir: str = "data/forecast_cache"):
        """
        Args:
            cache_dir: キャッシュファイルの保存ディレクトリ
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # CSVヘッダー
        self.csv_headers = [
            "location_name",
            "forecast_datetime", 
            "cached_at",
            "temperature",
            "max_temperature",
            "min_temperature",
            "weather_condition",
            "weather_description",
            "precipitation",
            "humidity", 
            "wind_speed",
            "metadata"
        ]
    
    def get_cache_file_path(self, location_name: str) -> Path:
        """地点名からキャッシュファイルのパスを取得"""
        # ファイルシステムで安全な文字のみを使用
        safe_name = re.sub(r'[^\w\s-]', '', location_name)
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        return self.cache_dir / f"forecast_cache_{safe_name}.csv"
    
    def save_forecast(self, weather_forecast: WeatherForecast, location_name: str) -> None:
        """予報データをキャッシュに保存"""
        try:
            cache_entry = ForecastCacheEntry.from_weather_forecast(weather_forecast, location_name)
            cache_file = self.get_cache_file_path(location_name)
            
            # ファイルが存在しない場合はヘッダーを書き込み
            write_header = not cache_file.exists()
            
            with open(cache_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                if write_header:
                    writer.writerow(self.csv_headers)
                
                writer.writerow(cache_entry.to_csv_row())
            
            logger.info(f"予報データをキャッシュに保存: {location_name} at {weather_forecast.datetime}")
            
            # 古いデータのクリーンアップ（設定から保持日数を取得）
            config = get_config()
            retention_days = config.weather.forecast_cache_retention_days
            self._cleanup_old_data(location_name, days=retention_days)
            
        except Exception as e:
            logger.error(f"予報データの保存に失敗: {e}")
    
    def get_forecast_at_time(self, location_name: str, target_datetime: datetime, 
                           tolerance_hours: int = 3) -> Optional[ForecastCacheEntry]:
        """指定時刻の予報データを取得
        
        Args:
            location_name: 地点名
            target_datetime: 対象日時
            tolerance_hours: 許容時間差（時間）
            
        Returns:
            予報キャッシュエントリ（見つからない場合はNone）
        """
        try:
            cache_file = self.get_cache_file_path(location_name)
            
            if not cache_file.exists():
                return None
            
            # パフォーマンス最適化: 対象日時の前後数日分のみ読み込み
            entries = self._load_cache_entries(location_name, date_filter=target_datetime, days_range=7)
            
            # 指定時刻に最も近いエントリを検索
            best_entry = None
            min_time_diff = timedelta(hours=tolerance_hours + 1)  # 許容範囲外の初期値
            
            for entry in entries:
                time_diff = abs(entry.forecast_datetime - target_datetime)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_entry = entry
            
            # 許容範囲内かチェック
            if best_entry and min_time_diff <= timedelta(hours=tolerance_hours):
                logger.info(f"キャッシュから予報データを取得: {location_name} at {best_entry.forecast_datetime}")
                return best_entry
            
            return None
            
        except Exception as e:
            logger.error(f"予報データの取得に失敗: {e}")
            return None
    
    def get_previous_day_forecast(self, location_name: str, reference_datetime: datetime) -> Optional[ForecastCacheEntry]:
        """前日の同時刻の予報データを取得
        
        Args:
            location_name: 地点名
            reference_datetime: 基準日時
            
        Returns:
            前日の予報データ（見つからない場合はNone）
        """
        previous_day = reference_datetime - timedelta(days=1)
        return self.get_forecast_at_time(location_name, previous_day, tolerance_hours=6)
    
    def get_forecast_12hours_ago(self, location_name: str, reference_datetime: datetime) -> Optional[ForecastCacheEntry]:
        """12時間前の予報データを取得
        
        Args:
            location_name: 地点名
            reference_datetime: 基準日時
            
        Returns:
            12時間前の予報データ（見つからない場合はNone）
        """
        twelve_hours_ago = reference_datetime - timedelta(hours=12)
        return self.get_forecast_at_time(location_name, twelve_hours_ago, tolerance_hours=3)
    
    def calculate_temperature_difference(self, current_forecast: WeatherForecast, 
                                       location_name: str) -> Dict[str, Optional[float]]:
        """気温差を計算
        
        Args:
            current_forecast: 現在の予報データ
            location_name: 地点名
            
        Returns:
            気温差の辞書
        """
        result = {
            "previous_day_diff": None,  # 前日同時刻との差
            "twelve_hours_ago_diff": None,  # 12時間前との差
            "daily_range": None  # 日較差
        }
        
        try:
            # 前日との比較
            previous_day_forecast = self.get_previous_day_forecast(location_name, current_forecast.datetime)
            if previous_day_forecast:
                result["previous_day_diff"] = current_forecast.temperature - previous_day_forecast.temperature
                logger.info(f"前日との気温差: {result['previous_day_diff']:.1f}℃")
            
            # 12時間前との比較
            twelve_hours_ago_forecast = self.get_forecast_12hours_ago(location_name, current_forecast.datetime)
            if twelve_hours_ago_forecast:
                result["twelve_hours_ago_diff"] = current_forecast.temperature - twelve_hours_ago_forecast.temperature
                logger.info(f"12時間前との気温差: {result['twelve_hours_ago_diff']:.1f}℃")
            
            # 日較差の計算（今回のキャッシュから当日の最高・最低気温を取得）
            daily_forecasts = self._get_daily_forecasts(location_name, current_forecast.datetime.date())
            if len(daily_forecasts) >= 2:
                temperatures = [f.temperature for f in daily_forecasts]
                max_temp = max(temperatures)
                min_temp = min(temperatures)
                result["daily_range"] = max_temp - min_temp
                logger.info(f"日較差: {result['daily_range']:.1f}℃")
            
        except Exception as e:
            logger.error(f"気温差の計算に失敗: {e}")
        
        return result
    
    def _load_cache_entries(self, location_name: str, 
                           date_filter: Optional[datetime] = None,
                           days_range: int = 7) -> List[ForecastCacheEntry]:
        """キャッシュエントリを読み込み
        
        Args:
            location_name: 地点名
            date_filter: フィルタリング基準日時（指定した場合、この日時から過去days_range日分のみ読み込み）
            days_range: 読み込む日数範囲
            
        Returns:
            キャッシュエントリのリスト
        """
        cache_file = self.get_cache_file_path(location_name)
        entries = []
        
        # フィルタリング用の日時を計算
        cutoff_date = None
        if date_filter:
            date_filter = ensure_jst(date_filter)
            cutoff_date = date_filter - timedelta(days=days_range)
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーをスキップ
                
                for row in reader:
                    if len(row) >= 4:  # 最低限のフィールドがある行のみ
                        try:
                            # 日時フィールドを先に確認（パフォーマンス最適化）
                            if cutoff_date and len(row) > 1:
                                forecast_dt = datetime.fromisoformat(row[1])
                                forecast_dt = ensure_jst(forecast_dt)
                                if forecast_dt < cutoff_date:
                                    continue
                            
                            entry = ForecastCacheEntry.from_csv_row(row)
                            entries.append(entry)
                        except ValueError as e:
                            logger.warning(f"無効なキャッシュエントリをスキップ: {e}")
                            continue
                            
        except FileNotFoundError:
            pass  # ファイルが存在しない場合は空のリストを返す
        except Exception as e:
            logger.error(f"キャッシュファイルの読み込みに失敗: {e}")
        
        return entries
    
    def _get_daily_forecasts(self, location_name: str, target_date) -> List[ForecastCacheEntry]:
        """指定日の全ての予報データを取得"""
        entries = self._load_cache_entries(location_name)
        return [entry for entry in entries if entry.forecast_datetime.date() == target_date]
    
    def _cleanup_old_data(self, location_name: str, days: int = 7) -> None:
        """古いキャッシュデータを削除"""
        try:
            entries = self._load_cache_entries(location_name)
            cutoff_date = datetime.now(JST) - timedelta(days=days)
            
            # 期限内のエントリのみを残す（タイムゾーンを考慮）
            valid_entries = []
            for entry in entries:
                # エントリのcached_atをJSTとして確実に扱う
                cached_at = ensure_jst(entry.cached_at)
                if cached_at >= cutoff_date:
                    valid_entries.append(entry)
            
            if len(valid_entries) < len(entries):
                # ファイルを再作成
                cache_file = self.get_cache_file_path(location_name)
                with open(cache_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(self.csv_headers)
                    
                    for entry in valid_entries:
                        writer.writerow(entry.to_csv_row())
                
                removed_count = len(entries) - len(valid_entries)
                logger.info(f"古いキャッシュデータを削除: {location_name} ({removed_count}件)")
                
        except Exception as e:
            logger.error(f"キャッシュクリーンアップに失敗: {e}")


# グローバルキャッシュインスタンス
_global_cache: Optional[ForecastCache] = None


def get_forecast_cache() -> ForecastCache:
    """グローバル予報キャッシュインスタンスを取得"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ForecastCache()
    return _global_cache


def save_forecast_to_cache(weather_forecast: WeatherForecast, location_name: str) -> None:
    """予報データをキャッシュに保存（便利関数）"""
    cache = get_forecast_cache()
    cache.save_forecast(weather_forecast, location_name)


def get_temperature_differences(current_forecast: WeatherForecast, location_name: str) -> Dict[str, Optional[float]]:
    """気温差を取得（便利関数）"""
    cache = get_forecast_cache()
    return cache.calculate_temperature_difference(current_forecast, location_name)