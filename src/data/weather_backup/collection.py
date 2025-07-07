"""
天気予報コレクション

複数の天気予報データを管理し、検索・分析機能を提供
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from src.data.weather.models import WeatherForecast
from src.data.weather.enums import WeatherCondition


class WeatherForecastCollection:
    """天気予報のコレクションを管理するクラス

    Attributes:
        forecasts: WeatherForecastインスタンスのリスト
        location: 共通の地点名
    """

    def __init__(self, forecasts: Optional[List[WeatherForecast]] = None, location: Optional[str] = None):
        """コンストラクタ

        Args:
            forecasts: 初期予報リスト
            location: 地点名
        """
        self.forecasts = sorted(forecasts or [], key=lambda f: f.date)
        self.location = location

    def get_current_forecast(self) -> Optional[WeatherForecast]:
        """現在時刻に最も近い予報を取得

        Returns:
            Optional[WeatherForecast]: 現在の予報（存在しない場合はNone）
        """
        if not self.forecasts:
            return None

        now = datetime.now()
        return self.get_nearest_forecast(now)

    def get_nearest_forecast(self, target_datetime: datetime) -> Optional[WeatherForecast]:
        """指定日時に最も近い予報を取得

        Args:
            target_datetime: 対象日時

        Returns:
            Optional[WeatherForecast]: 最も近い予報
        """
        if not self.forecasts:
            return None

        def get_comparable_datetime(dt: datetime) -> datetime:
            """比較用の日時を取得（日付と時間のみ）"""
            return dt.replace(second=0, microsecond=0)

        target_comparable = get_comparable_datetime(target_datetime)

        # 最も近い予報を探す
        nearest_forecast = None
        min_diff = None

        for forecast in self.forecasts:
            forecast_comparable = get_comparable_datetime(forecast.date)
            diff = abs((forecast_comparable - target_comparable).total_seconds())

            if min_diff is None or diff < min_diff:
                min_diff = diff
                nearest_forecast = forecast

        return nearest_forecast

    def get_forecast_by_hour(self, target_hour: int) -> Optional[WeatherForecast]:
        """指定時刻の予報を取得

        Args:
            target_hour: 対象時刻（0-23）

        Returns:
            Optional[WeatherForecast]: 該当時刻の予報
        """
        for forecast in self.forecasts:
            if forecast.date.hour == target_hour:
                return forecast
        return None

    def get_daily_summary(self) -> Dict[str, Any]:
        """1日の天気サマリーを取得

        Returns:
            Dict[str, Any]: 天気のサマリー情報
        """
        if not self.forecasts:
            return {}

        temperatures = [f.temperature for f in self.forecasts]
        humidities = [f.humidity for f in self.forecasts]
        precipitations = [f.precipitation_mm for f in self.forecasts]
        wind_speeds = [f.wind_speed for f in self.forecasts]

        # 天気の頻度を集計
        weather_counts = {}
        for forecast in self.forecasts:
            weather = forecast.weather.value
            weather_counts[weather] = weather_counts.get(weather, 0) + 1

        # 最も多い天気を代表天気とする
        dominant_weather = max(weather_counts.items(), key=lambda x: x[1])[0] if weather_counts else None

        # 特殊な気象状況をチェック
        special_conditions = []
        for forecast in self.forecasts:
            if forecast.weather.is_special_condition and forecast.weather.value not in special_conditions:
                special_conditions.append(forecast.weather.value)

        return {
            "location": self.location,
            "date": self.forecasts[0].date.date() if self.forecasts else None,
            "temperature": {
                "min": min(temperatures),
                "max": max(temperatures),
                "avg": sum(temperatures) / len(temperatures),
            },
            "humidity": {
                "min": min(humidities),
                "max": max(humidities),
                "avg": sum(humidities) / len(humidities),
            },
            "precipitation": {
                "total": sum(precipitations),
                "max_hourly": max(precipitations),
            },
            "wind_speed": {
                "max": max(wind_speeds),
                "avg": sum(wind_speeds) / len(wind_speeds),
            },
            "dominant_weather": dominant_weather,
            "weather_distribution": weather_counts,
            "special_conditions": special_conditions,
            "forecast_hours": len(self.forecasts),
        }

    def filter_by_weather(self, weather_conditions: List[WeatherCondition]) -> "WeatherForecastCollection":
        """天気条件でフィルタリング

        Args:
            weather_conditions: フィルタリングする天気条件のリスト

        Returns:
            WeatherForecastCollection: フィルタリング後の新しいコレクション
        """
        filtered_forecasts = [
            f for f in self.forecasts if f.weather in weather_conditions
        ]
        return WeatherForecastCollection(filtered_forecasts, self.location)

    def filter_by_date_range(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> "WeatherForecastCollection":
        """日付範囲でフィルタリング

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            WeatherForecastCollection: フィルタリング後の新しいコレクション
        """
        filtered_forecasts = []
        for forecast in self.forecasts:
            if start_date and forecast.date < start_date:
                continue
            if end_date and forecast.date > end_date:
                continue
            filtered_forecasts.append(forecast)
        
        return WeatherForecastCollection(filtered_forecasts, self.location)

    def get_severe_weather_periods(self) -> List[Tuple[datetime, datetime, str]]:
        """悪天候の期間を取得

        Returns:
            List[Tuple[datetime, datetime, str]]: (開始時刻, 終了時刻, 天気) のリスト
        """
        periods = []
        current_period_start = None
        current_weather = None

        for i, forecast in enumerate(self.forecasts):
            if forecast.is_severe_weather():
                if current_period_start is None:
                    current_period_start = forecast.date
                    current_weather = forecast.weather.value
            else:
                if current_period_start is not None:
                    # 悪天候期間の終了
                    end_time = self.forecasts[i - 1].date if i > 0 else current_period_start
                    periods.append((current_period_start, end_time, current_weather))
                    current_period_start = None
                    current_weather = None

        # 最後まで悪天候が続いている場合
        if current_period_start is not None:
            periods.append((current_period_start, self.forecasts[-1].date, current_weather))

        return periods

    def to_dict(self) -> Dict[str, Any]:
        """コレクション全体を辞書形式に変換

        Returns:
            Dict[str, Any]: コレクションの辞書表現
        """
        return {
            "location": self.location,
            "forecasts": [forecast.to_dict() for forecast in self.forecasts],
            "count": len(self.forecasts),
            "summary": self.get_daily_summary(),
        }