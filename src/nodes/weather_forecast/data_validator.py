"""
天気予報データ検証・選択モジュール

天気予報データの検証と優先度に基づく選択機能を提供
"""

from __future__ import annotations
import logging
from typing import Any
from src.data.weather_data import WeatherForecast, WeatherCondition

logger = logging.getLogger(__name__)


class WeatherDataValidator:
    """天気予報データ検証・選択クラス"""
    
    def select_forecast_by_time(self, forecasts: list[WeatherForecast], target_datetime) -> WeatherForecast:
        """指定された時刻に最も近い予報データを選択
        
        Args:
            forecasts: 予報データリスト
            target_datetime: ターゲット時刻
            
        Returns:
            ターゲット時刻に最も近い予報データ
        """
        if not forecasts:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # タイムゾーンの処理
        import pytz
        jst = pytz.timezone('Asia/Tokyo')
        
        # target_datetimeがnaiveな場合はJSTとして扱う
        if target_datetime.tzinfo is None:
            target_datetime = jst.localize(target_datetime)
        
        # ターゲット時刻に最も近い予報を選択
        def time_diff(forecast):
            # forecastのdatetimeがnaiveな場合はJSTとして扱う
            forecast_dt = forecast.datetime
            if forecast_dt.tzinfo is None:
                forecast_dt = jst.localize(forecast_dt)
            return abs((forecast_dt - target_datetime).total_seconds())
        
        closest_forecast = min(forecasts, key=time_diff)
        
        logger.info(
            f"指定時刻 {target_datetime.strftime('%H:%M')} に最も近い予報を選択: "
            f"{closest_forecast.datetime.strftime('%H:%M')}, {closest_forecast.weather_description}, "
            f"{closest_forecast.temperature}°C"
        )
        
        return closest_forecast
    
    def select_priority_forecast(self, forecasts: list[WeatherForecast]) -> WeatherForecast:
        """翌日9:00-18:00の予報から最も重要な気象条件を選択
        
        優先順位ルール:
        1. 雷、嵐、霧などの特殊気象条件を最優先
        2. 本降りの雨（>10mm/h）は猛暑日でも優先
        3. 猛暑日（35℃以上）では小雨でも熱中症対策を優先
        4. 雨 > 曇り > 晴れの順で優先
        
        Args:
            forecasts: 9時間の予報リスト（9:00, 12:00, 15:00, 18:00）
            
        Returns:
            選択された予報（優先度ルールに基づく）
            
        Raises:
            ValueError: 予報データが空の場合
        """
        if not forecasts:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"翌日9:00-18:00の予報分析開始: {len(forecasts)}件")
        
        # 各予報の詳細をログ出力
        for f in forecasts:
            logger.info(f"  {f.datetime.strftime('%H:%M')}: {f.weather_description}, 気温{f.temperature}°C, 降水量{f.precipitation}mm/h, 天気条件: {f.weather_condition.value}")
        
        # 1. 真の特殊気象条件（雷、霧、嵐）を最優先（雨・猛暑は除く）
        extreme_conditions = [f for f in forecasts if f.weather_condition in [
            WeatherCondition.THUNDER, WeatherCondition.FOG, WeatherCondition.STORM, 
            WeatherCondition.SEVERE_STORM
        ]]
        if extreme_conditions:
            selected = max(extreme_conditions, key=lambda f: f.weather_condition.priority)
            logger.info(f"特殊気象条件を優先選択: {selected.weather_condition.value} ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 2. 本降りの雨（>10mm/h）は猛暑日でも優先
        heavy_rain = [f for f in forecasts if f.precipitation > 10.0]
        logger.debug(f"本降りの雨チェック: {len(heavy_rain)}件 (>10mm/h)")
        if heavy_rain:
            selected = max(heavy_rain, key=lambda f: f.precipitation)
            logger.info(f"本降りの雨を優先選択: {selected.precipitation}mm/h ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 3. 雨天チェック（猛暑日より雨を優先）
        rainy_forecasts = [f for f in forecasts if f.precipitation > 0]
        logger.debug(f"一般的な雨天チェック: {len(rainy_forecasts)}件 (>0mm/h)")
        if rainy_forecasts:
            logger.info(f"雨天予報を検出: {len(rainy_forecasts)}件")
            for rf in rainy_forecasts:
                logger.info(f"  - {rf.datetime.strftime('%H:%M')}: {rf.weather_description}, 降水量{rf.precipitation}mm, 天気条件: {rf.weather_condition.value}")
            selected = max(rainy_forecasts, key=lambda f: f.precipitation)
            logger.info(f"雨天を優先選択: {selected.precipitation}mm/h ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 4. 猛暑日（35℃以上）の場合の処理（雨がない場合のみ）
        extreme_hot = [f for f in forecasts if f.temperature >= 35.0]
        logger.debug(f"猛暑日チェック: {len(extreme_hot)}件 (>=35°C)")
        if extreme_hot:
            selected = max(extreme_hot, key=lambda f: f.temperature)
            logger.info(f"猛暑日を優先選択（雨なし）: {selected.temperature}°C ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 5. 悪天候を優先（降水量の多い順）
        severe_weather = [f for f in forecasts if f.is_severe_weather()]
        if severe_weather:
            selected = max(severe_weather, key=lambda f: f.precipitation)
            logger.info(f"悪天候を優先選択: {selected.weather_description} ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 6. 曇りを優先（晴れ以外の条件）
        non_clear_forecasts = [f for f in forecasts if f.weather_condition.value != "clear"]
        if non_clear_forecasts:
            selected = max(non_clear_forecasts, key=lambda f: f.weather_condition.priority)
            logger.info(f"曇りを優先選択: {selected.weather_description} ({selected.datetime.strftime('%H:%M')})")
            return selected
        
        # 7. 全て晴れの場合は最も気温の高い時間帯を選択
        selected = max(forecasts, key=lambda f: f.temperature)
        logger.info(f"晴れ日で最高気温を選択: {selected.temperature}°C ({selected.datetime.strftime('%H:%M')})")
        return selected
    
    def validate_forecast_data(
        self,
        forecasts: list[WeatherForecast],
        min_forecasts: int = 1,
    ) -> bool:
        """予報データの妥当性を検証
        
        Args:
            forecasts: 天気予報リスト
            min_forecasts: 最小必要予報数（デフォルト: 1）
            
        Returns:
            データが妥当な場合はTrue
        """
        if not forecasts:
            logger.error("予報データが空です")
            return False
        
        if len(forecasts) < min_forecasts:
            logger.error(f"予報データが不足しています: {len(forecasts)}件 < {min_forecasts}件")
            return False
        
        # 各予報データの妥当性チェック
        for i, forecast in enumerate(forecasts):
            # 気温の妥当性チェック（-50℃ ～ 50℃）
            if not -50 <= forecast.temperature <= 50:
                logger.error(f"予報{i+1}: 異常な気温値: {forecast.temperature}°C")
                return False
            
            # 降水量の妥当性チェック（0mm/h ～ 300mm/h）
            if not 0 <= forecast.precipitation <= 300:
                logger.error(f"予報{i+1}: 異常な降水量: {forecast.precipitation}mm/h")
                return False
            
            # 風速の妥当性チェック（0m/s ～ 100m/s）
            if not 0 <= forecast.wind_speed <= 100:
                logger.error(f"予報{i+1}: 異常な風速: {forecast.wind_speed}m/s")
                return False
        
        return True
    
    def parse_location_string(self, location_name_raw: str) -> tuple[str, float | None, float | None]:
        """地点文字列をパース
        
        Args:
            location_name_raw: 生の地点文字列（"地点名,緯度,経度" 形式も可）
            
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
                        f"Extracted location name '{location_name}' with coordinates ({provided_lat}, {provided_lon})",
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid coordinates in '{location_name_raw}', will look up in LocationManager",
                    )
            else:
                logger.info(f"Extracted location name '{location_name}' from '{location_name_raw}'")
        else:
            location_name = location_name_raw.strip()
        
        return location_name, provided_lat, provided_lon