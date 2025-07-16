"""
Forecast cache manager

予報キャッシュの管理を担当
"""

from __future__ import annotations
import csv
import re
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Any
from zoneinfo import ZoneInfo

from src.data.weather_data import WeatherForecast
from src.config.weather_config import get_config
from .models import ForecastCacheEntry
from .utils import ensure_jst

logger = logging.getLogger(__name__)

# タイムゾーン定義
JST = ZoneInfo("Asia/Tokyo")


class ForecastCache:
    """天気予報キャッシュの管理クラス
    
    地点ごとにCSVファイルで予報データを保存し、
    前日や前回の予報との比較を可能にする
    """
    
    def __init__(self, cache_dir: Path | None = None):
        """初期化
        
        Args:
            cache_dir: キャッシュディレクトリ（Noneの場合はデフォルト）
        """
        if cache_dir is None:
            # デフォルトはプロジェクトルートの.cacheディレクトリ
            cache_dir = Path(__file__).parent.parent.parent.parent / ".cache" / "forecasts"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # CSVのヘッダー定義
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
        """予報データをキャッシュに保存
        
        Args:
            weather_forecast: 天気予報データ
            location_name: 地点名
        """
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
            # 同じ時刻の複数エントリがある場合は最新のキャッシュを優先
            best_entry = None
            min_time_diff = timedelta(hours=tolerance_hours + 1)  # 許容範囲外の初期値
            latest_cached_at = None
            
            for entry in entries:
                time_diff = abs(entry.forecast_datetime - target_datetime)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_entry = entry
                    latest_cached_at = entry.cached_at
                elif time_diff == min_time_diff and latest_cached_at and entry.cached_at > latest_cached_at:
                    # 同じ時刻の場合は、より新しいキャッシュを優先
                    best_entry = entry
                    latest_cached_at = entry.cached_at
            
            # 許容範囲内かチェック
            if best_entry and min_time_diff <= timedelta(hours=tolerance_hours):
                # 同じ時刻のエントリ数をカウント
                same_time_entries = [e for e in entries if e.forecast_datetime == best_entry.forecast_datetime]
                logger.info(
                    f"キャッシュから予報データを取得: {location_name} - "
                    f"要求時刻: {target_datetime.strftime('%Y-%m-%d %H:%M')}, "
                    f"実際の時刻: {best_entry.forecast_datetime.strftime('%Y-%m-%d %H:%M')}, "
                    f"時間差: {min_time_diff}, "
                    f"降水量: {best_entry.precipitation}mm, "
                    f"キャッシュ保存時刻: {best_entry.cached_at.strftime('%Y-%m-%d %H:%M')}, "
                    f"同時刻エントリ数: {len(same_time_entries)}"
                )
                return best_entry
            
            return None
            
        except Exception as e:
            logger.error(f"予報データの取得に失敗: {e}")
            return None
    
    def get_daily_min_max(self, location_name: str, target_date: date) -> dict[str, Optional[float]]:
        """指定日の最高・最低気温を取得
        
        Args:
            location_name: 地点名
            target_date: 対象日
            
        Returns:
            {"min": 最低気温, "max": 最高気温} の辞書
        """
        try:
            # 指定日の全データを読み込み
            target_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=JST)
            entries = self._load_cache_entries(location_name, date_filter=target_datetime, days_range=1)
            
            # 指定日のエントリのみフィルタ
            daily_entries = [
                e for e in entries 
                if e.forecast_datetime.date() == target_date
            ]
            
            if not daily_entries:
                return {"min": None, "max": None}
            
            temperatures = [e.temperature for e in daily_entries]
            
            return {
                "min": min(temperatures),
                "max": max(temperatures)
            }
            
        except Exception as e:
            logger.error(f"日次最高・最低気温の取得に失敗: {e}")
            return {"min": None, "max": None}
    
    def _load_cache_entries(self, location_name: str, date_filter: Optional[datetime] = None, 
                          days_range: int = 30) -> list[ForecastCacheEntry]:
        """キャッシュファイルからエントリを読み込み
        
        Args:
            location_name: 地点名
            date_filter: フィルタ日時（この前後のデータのみ読み込む）
            days_range: 読み込み範囲（日数）
            
        Returns:
            ForecastCacheEntryのリスト
        """
        cache_file = self.get_cache_file_path(location_name)
        
        if not cache_file.exists():
            return []
        
        entries = []
        
        # フィルタ範囲の計算
        if date_filter:
            date_filter_jst = ensure_jst(date_filter)
            start_date = date_filter_jst - timedelta(days=days_range)
            end_date = date_filter_jst + timedelta(days=days_range)
        
        with open(cache_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            
            # ヘッダーをスキップ
            next(reader, None)
            
            for row in reader:
                if len(row) < 6:  # 最低限必要な列数
                    continue
                
                try:
                    entry = ForecastCacheEntry.from_csv_row(row)
                    
                    # 日付フィルタリング
                    if date_filter:
                        entry_dt_jst = ensure_jst(entry.forecast_datetime)
                        if not (start_date <= entry_dt_jst <= end_date):
                            continue
                    
                    entries.append(entry)
                    
                except Exception as e:
                    logger.warning(f"キャッシュエントリの読み込みエラー: {e}")
                    continue
        
        return entries
    
    def _cleanup_old_data(self, location_name: str, days: int = 30) -> None:
        """古いキャッシュデータを削除
        
        Args:
            location_name: 地点名
            days: 保持日数
        """
        try:
            cache_file = self.get_cache_file_path(location_name)
            
            if not cache_file.exists():
                return
            
            cutoff_date = datetime.now(JST) - timedelta(days=days)
            
            # 新しいデータのみを保持
            entries = self._load_cache_entries(location_name)
            recent_entries = [
                e for e in entries 
                if ensure_jst(e.cached_at) > cutoff_date
            ]
            
            # 削除されるエントリ数をログ
            deleted_count = len(entries) - len(recent_entries)
            if deleted_count > 0:
                logger.info(f"{location_name}の古いキャッシュデータを{deleted_count}件削除")
            
            # ファイルを書き直し
            with open(cache_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.csv_headers)
                
                for entry in recent_entries:
                    writer.writerow(entry.to_csv_row())
                    
        except Exception as e:
            logger.error(f"キャッシュクリーンアップ中にエラー: {e}")


# シングルトンインスタンス
_forecast_cache_instance = None


def get_forecast_cache() -> ForecastCache:
    """ForecastCacheのシングルトンインスタンスを取得
    
    Returns:
        ForecastCache インスタンス
    """
    global _forecast_cache_instance
    if _forecast_cache_instance is None:
        _forecast_cache_instance = ForecastCache()
    return _forecast_cache_instance