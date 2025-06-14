"""
天気データ関連のデータクラスと型定義

WxTech APIからの天気予報データを標準化して扱うためのクラス群
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class WeatherCondition(Enum):
    """天気状況の列挙型"""

    CLEAR = "clear"  # 晴れ
    PARTLY_CLOUDY = "partly_cloudy"  # 曇り時々晴れ
    CLOUDY = "cloudy"  # 曇り
    RAIN = "rain"  # 雨
    HEAVY_RAIN = "heavy_rain"  # 大雨
    SNOW = "snow"  # 雪
    HEAVY_SNOW = "heavy_snow"  # 大雪
    STORM = "storm"  # 嵐
    FOG = "fog"  # 霧
    THUNDER = "thunder"  # 雷
    EXTREME_HEAT = "extreme_heat"  # 猫暮
    SEVERE_STORM = "severe_storm"  # 大雨・嵐
    UNKNOWN = "unknown"  # 不明
    
    @property
    def priority(self) -> int:
        """天気状況の優先度を返す（数値が大きいほど優先度が高い）
        
        特殊な気象状況（雷、濃霧、嵐など）を優先的に扱うための優先度設定
        """
        priority_map = {
            "severe_storm": 12,  # 大雨・嵐 - 最高優先
            "thunder": 11,       # 雷
            "extreme_heat": 10,  # 猫暮
            "storm": 9,          # 嵐
            "fog": 8,            # 霧
            "heavy_snow": 7,     # 大雪
            "heavy_rain": 6,     # 大雨
            "snow": 5,           # 雪
            "rain": 4,           # 雨
            "cloudy": 3,         # 曇り
            "partly_cloudy": 2,  # 曇り時々晴れ
            "clear": 1,          # 晴れ
            "unknown": 0         # 不明
        }
        return priority_map.get(self.value, 0)
    
    @property
    def is_special_condition(self) -> bool:
        """特殊な気象状況かどうかを判定"""
        return self.priority >= 4  # 雨、大雨、霧、嵐、雷、猫暮、大雨・嵐を特殊気象とする


class WindDirection(Enum):
    """風向きの列挙型"""

    N = "north"  # 北
    NE = "northeast"  # 北東
    E = "east"  # 東
    SE = "southeast"  # 南東
    S = "south"  # 南
    SW = "southwest"  # 南西
    W = "west"  # 西
    NW = "northwest"  # 北西
    CALM = "calm"  # 無風
    UNKNOWN = "unknown"  # 不明


@dataclass
class WeatherForecast:
    """天気予報データを表すデータクラス

    Attributes:
        location: 地点名
        datetime: 予報日時
        temperature: 気温（℃）
        weather_code: 天気コード（WxTech API固有）
        weather_condition: 標準化された天気状況
        weather_description: 天気の日本語説明
        precipitation: 降水量（mm）
        humidity: 湿度（%）
        wind_speed: 風速（m/s）
        wind_direction: 風向き
        wind_direction_degrees: 風向き（度）
        pressure: 気圧（hPa, オプション）
        visibility: 視界（km, オプション）
        uv_index: UV指数（オプション）
        confidence: 予報信頼度（0.0-1.0, オプション）
        raw_data: 元のAPIレスポンスデータ
    """

    location: str
    datetime: datetime
    temperature: float
    weather_code: str
    weather_condition: WeatherCondition
    weather_description: str
    precipitation: float
    humidity: float
    wind_speed: float
    wind_direction: WindDirection
    wind_direction_degrees: int
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    uv_index: Optional[int] = None
    confidence: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """データクラス初期化後の検証処理"""
        # 気温の妥当性チェック（-50℃〜60℃）
        if not -50 <= self.temperature <= 60:
            raise ValueError(f"異常な気温値: {self.temperature}℃")

        # 湿度の妥当性チェック（0-100%）
        if not 0 <= self.humidity <= 100:
            raise ValueError(f"異常な湿度値: {self.humidity}%")

        # 風速の妥当性チェック（0-200 m/s）
        if not 0 <= self.wind_speed <= 200:
            raise ValueError(f"異常な風速値: {self.wind_speed} m/s")

        # 降水量の妥当性チェック（0以上）
        if self.precipitation < 0:
            raise ValueError(f"異常な降水量値: {self.precipitation} mm")

        # 風向き度数の妥当性チェック（0-360度）
        if not 0 <= self.wind_direction_degrees <= 360:
            raise ValueError(f"異常な風向き度数: {self.wind_direction_degrees}度")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            天気予報データの辞書
        """
        return {
            "location": self.location,
            "datetime": self.datetime.isoformat(),
            "temperature": self.temperature,
            "weather_code": self.weather_code,
            "weather_condition": self.weather_condition.value,
            "weather_description": self.weather_description,
            "precipitation": self.precipitation,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction.value,
            "wind_direction_degrees": self.wind_direction_degrees,
            "pressure": self.pressure,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherForecast":
        """辞書から WeatherForecast オブジェクトを作成

        Args:
            data: 天気予報データの辞書

        Returns:
            WeatherForecast オブジェクト
        """
        # datetime文字列を datetime オブジェクトに変換
        if isinstance(data["datetime"], str):
            data["datetime"] = datetime.fromisoformat(data["datetime"])

        # enum値を適切に変換
        if isinstance(data["weather_condition"], str):
            data["weather_condition"] = WeatherCondition(data["weather_condition"])

        if isinstance(data["wind_direction"], str):
            data["wind_direction"] = WindDirection(data["wind_direction"])

        return cls(**data)

    def is_good_weather(self) -> bool:
        """良い天気かどうかを判定

        Returns:
            良い天気の場合True
        """
        good_conditions = {WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY}
        return (
            self.weather_condition in good_conditions
            and self.precipitation <= 0.1  # ほぼ降水なし
            and 10 <= self.temperature <= 30  # 適度な気温
        )

    def is_severe_weather(self) -> bool:
        """悪天候かどうかを判定

        Returns:
            悪天候の場合True
        """
        severe_conditions = {
            WeatherCondition.HEAVY_RAIN,
            WeatherCondition.HEAVY_SNOW,
            WeatherCondition.STORM,
            WeatherCondition.SEVERE_STORM, # 大雨・嵐を追加
        }
        
        # 雷は降水量が5mm以上の場合のみ悪天候とする
        thunder_with_rain = (
            self.weather_condition == WeatherCondition.THUNDER and 
            self.precipitation >= 5.0
        )
        
        return (
            self.weather_condition in severe_conditions
            or thunder_with_rain  # 雷+降水量5mm以上
            or self.precipitation >= 10.0  # 強い降水
            or self.wind_speed >= 15.0  # 強風
        )
    
    def get_precipitation_severity(self) -> str:
        """降水量の重要度を取得
        
        Returns:
            降水量レベル（'none', 'light', 'moderate', 'heavy', 'very_heavy'）
        """
        if self.precipitation <= 0.5:
            return "none"
        elif self.precipitation <= 2.0:
            return "light"  # 軽い雨
        elif self.precipitation <= 10.0:
            return "moderate"  # 中程度の雨
        elif self.precipitation <= 30.0:
            return "heavy"  # 大雨
        else:
            return "very_heavy"  # 激しい雨

    def get_comfort_level(self) -> str:
        """快適度レベルを取得

        Returns:
            快適度レベル（'comfortable', 'moderate', 'uncomfortable'）
        """
        if self.is_good_weather():
            return "comfortable"
        elif self.is_severe_weather():
            return "uncomfortable"
        else:
            return "moderate"


@dataclass
class WeatherForecastCollection:
    """複数の天気予報データを管理するコレクション

    Attributes:
        location: 地点名
        forecasts: 天気予報のリスト
        generated_at: データ生成日時
    """

    location: str
    forecasts: List[WeatherForecast]
    generated_at: datetime = field(default_factory=datetime.now)

    def get_current_forecast(self) -> Optional[WeatherForecast]:
        """現在時刻に最も近い予報を取得

        Returns:
            現在時刻に最も近い天気予報（なければNone）
        """
        if not self.forecasts:
            return None

        import pytz

        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst)

        return self.get_nearest_forecast(now)

    def get_nearest_forecast(self, target_datetime: datetime) -> Optional[WeatherForecast]:
        """指定日時に最も近い予報を取得

        Args:
            target_datetime: 対象日時

        Returns:
            指定日時に最も近い天気予報（なければNone）
        """
        if not self.forecasts:
            return None

        # タイムゾーン対応: target_datetimeとforecast.datetimeの両方を比較可能にする
        def get_comparable_datetime(dt: datetime) -> datetime:
            """datetimeオブジェクトを比較可能な形式に変換"""
            if dt.tzinfo is None:
                # naiveな場合はJSTとして扱う
                import pytz

                jst = pytz.timezone("Asia/Tokyo")
                return jst.localize(dt)
            return dt

        target_dt_aware = get_comparable_datetime(target_datetime)

        closest_forecast = min(
            self.forecasts,
            key=lambda f: abs(
                (get_comparable_datetime(f.datetime) - target_dt_aware).total_seconds()
            ),
        )
        return closest_forecast

    def get_forecast_by_hour(self, target_hour: int) -> Optional[WeatherForecast]:
        """指定時刻の予報を取得

        Args:
            target_hour: 対象時刻（0-23）

        Returns:
            指定時刻の天気予報（なければNone）
        """
        for forecast in self.forecasts:
            if forecast.datetime.hour == target_hour:
                return forecast
        return None

    def get_daily_summary(self) -> Dict[str, Any]:
        """日次サマリーを取得

        Returns:
            日次サマリー辞書
        """
        if not self.forecasts:
            return {}

        temperatures = [f.temperature for f in self.forecasts]
        precipitations = [f.precipitation for f in self.forecasts]

        return {
            "max_temperature": max(temperatures),
            "min_temperature": min(temperatures),
            "avg_temperature": sum(temperatures) / len(temperatures),
            "total_precipitation": sum(precipitations),
            "max_precipitation": max(precipitations),
            "forecast_count": len(self.forecasts),
        }

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            予報コレクションの辞書
        """
        return {
            "location": self.location,
            "generated_at": self.generated_at.isoformat(),
            "forecasts": [f.to_dict() for f in self.forecasts],
            "summary": self.get_daily_summary(),
        }
