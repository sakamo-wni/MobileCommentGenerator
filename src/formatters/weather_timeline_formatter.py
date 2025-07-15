"""
天気タイムラインフォーマッター
"""

from typing import Any
import logging
from datetime import datetime, timedelta
import pytz

from src.data.forecast_cache import ForecastCache, ensure_jst
from src.utils.weather_classifier import classify_weather_type, count_weather_type_changes, is_morning_only_change
from src.config.config import get_weather_constants

logger = logging.getLogger(__name__)


class WeatherTimelineFormatter:
    """天気タイムラインをフォーマットするクラス"""
    
    def __init__(self):
        self.cache = ForecastCache()
        self.jst = pytz.timezone("Asia/Tokyo")
        self.WEATHER_CHANGE_THRESHOLD = get_weather_constants().WEATHER_CHANGE_THRESHOLD
    
    def get_weather_timeline(self, location_name: str, base_datetime: datetime) -> dict[str, Any]:
        """翌日9:00-18:00の天気データを取得
        
        Args:
            location_name: 地点名
            base_datetime: 選択された予報時刻（使用しないが互換性のため維持）
            
        Returns:
            翌日9:00-18:00の時系列天気データ
        """
        now_jst = datetime.now(self.jst)
        
        timeline_data: dict[str, Any] = {
            "future_forecasts": [],
            "past_forecasts": [],
            "base_time": base_datetime.isoformat()
        }
        
        try:
            # 常に翌日を対象にする
            target_date = now_jst.date() + timedelta(days=1)
            target_hours = [9, 12, 15, 18]
            
            logger.info(f"翌日({target_date})の予報データを取得中: {target_hours}")
            
            for hour in target_hours:
                target_time = self.jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
                
                try:
                    # デバッグ: キャッシュ取得前の情報をログ
                    logger.info(f"キャッシュから取得中: {location_name} @ {target_time.strftime('%Y-%m-%d %H:%M')}")
                    forecast = self.cache.get_forecast_at_time(location_name, target_time)
                    if forecast:
                        # デバッグ: キャッシュから取得したデータの詳細
                        logger.info(
                            f"キャッシュデータ詳細 - 実際の時刻: {forecast.forecast_datetime.strftime('%Y-%m-%d %H:%M')}, "
                            f"天気: {forecast.weather_description}, "
                            f"降水量: {forecast.precipitation}mm, "
                            f"キャッシュ保存時刻: {forecast.cached_at.strftime('%Y-%m-%d %H:%M')}"
                        )
                        timeline_data["future_forecasts"].append({
                            "time": target_time.strftime("%m/%d %H:%M"),
                            "label": f"{hour:02d}:00",
                            "weather": forecast.weather_description,
                            "temperature": forecast.temperature,
                            "precipitation": forecast.precipitation
                        })
                        logger.debug(f"翌日予報取得成功: {hour:02d}:00 at {target_time}")
                    else:
                        logger.warning(f"翌日予報データなし: {hour:02d}:00 at {target_time}")
                except Exception as e:
                    logger.warning(f"翌日予報取得エラー ({hour:02d}:00): {e}")
            
            # 過去データ表示は削除（翌日の予報のみ表示）
            timeline_data["past_forecasts"] = []
            
            # データが取得できた場合のみ統計情報を追加
            all_forecasts = timeline_data["future_forecasts"] + timeline_data["past_forecasts"]
            if all_forecasts:
                temps = [f["temperature"] for f in all_forecasts if f["temperature"] is not None]
                precipitations = [f["precipitation"] for f in all_forecasts if f["precipitation"] is not None]
                
                timeline_data["summary"] = {
                    "temperature_range": f"{min(temps):.1f}°C〜{max(temps):.1f}°C" if temps else "データなし",
                    "max_precipitation": f"{max(precipitations):.1f}mm" if precipitations else "0mm",
                    "weather_pattern": self._analyze_weather_pattern(all_forecasts)
                }
        
        except Exception as e:
            logger.error(f"天気タイムライン取得エラー: {e}")
            timeline_data["error"] = str(e)
        
        return timeline_data
    
    def _analyze_weather_pattern(self, forecasts: list[dict[str, Any]]) -> str:
        """天気パターンを分析
        
        Args:
            forecasts: 予報データのリスト
            
        Returns:
            天気パターンの説明
        """
        if not forecasts:
            return "データなし"
        
        weather_conditions = [f["weather"] for f in forecasts if f["weather"]]
        
        # 悪天候の検出
        severe_conditions = ["大雨", "嵐", "雷", "豪雨", "暴風", "台風"]
        rain_conditions = ["雨", "小雨", "中雨"]
        
        has_severe = any(any(severe in weather for severe in severe_conditions) for weather in weather_conditions)
        has_rain = any(any(rain in weather for rain in rain_conditions) for weather in weather_conditions)
        
        if has_severe:
            return "悪天候注意"
        elif has_rain:
            return "雨天続く"
        else:
            # 天気の変化を詳細に分析
            # 全て同じ天気の場合
            if len(set(weather_conditions)) == 1:
                return "安定した天気"
            
            # 天気の変化回数をカウント
            weather_changes = 0
            for i in range(1, len(weather_conditions)):
                if weather_conditions[i] != weather_conditions[i-1]:
                    weather_changes += 1
            
            # 天気タイプを時系列で分類
            weather_type_sequence = []
            for condition in weather_conditions:
                weather_type = classify_weather_type(condition)
                weather_type_sequence.append(weather_type or "other")
            
            # デバッグログ
            logger.debug(f"天気条件: {weather_conditions}")
            logger.debug(f"天気タイプ: {weather_type_sequence}")
            
            # タイプレベルでの変化回数をカウント
            type_changes = count_weather_type_changes(weather_type_sequence)
            logger.debug(f"タイプ変化回数: {type_changes}")
            
            # 判定ロジック
            # WEATHER_CHANGE_THRESHOLD回以上タイプが変わる場合は変わりやすい
            if type_changes >= self.WEATHER_CHANGE_THRESHOLD:
                return "変わりやすい天気"
            # 朝だけ違って、その後同じ天気が続く場合は安定
            elif type_changes == 1 and is_morning_only_change(weather_type_sequence):
                return "安定した天気"
            # その他1回だけ変化する場合も基本的には安定
            elif type_changes <= 1:
                return "安定した天気"
            else:
                return "変わりやすい天気"