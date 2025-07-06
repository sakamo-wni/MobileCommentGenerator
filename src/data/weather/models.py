"""
天気予報モデル定義

WxTech APIからの天気予報データを標準化して扱うためのデータクラス
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from src.data.weather.enums import WeatherCondition, WindDirection


@dataclass
class WeatherForecast:
    """天気予報データを表すデータクラス

    Attributes:
        location: 地点名
        date: 予報日時
        weather: 天気状況 (列挙型)
        temperature: 気温 (℃)
        feels_like: 体感温度 (℃)
        humidity: 湿度 (%)
        precipitation_mm: 降水量 (mm)
        wind_speed: 風速 (m/s)
        wind_direction: 風向き (列挙型)
        pressure: 気圧 (hPa)
        visibility: 視程 (km)
        uv_index: UV指数
        cloud_cover: 雲量 (%)
        weather_code: 天気コード (元のAPIコード)
        weather_text: 天気テキスト (元のAPI文字列)
        dew_point: 露点温度 (℃)
        heat_index: 暑さ指数
        raw_data: 生のAPIレスポンスデータ
    """

    location: str
    date: datetime
    weather: WeatherCondition
    temperature: float
    feels_like: float
    humidity: float
    precipitation_mm: float = 0.0
    wind_speed: float = 0.0
    wind_direction: WindDirection = WindDirection.CALM
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    uv_index: Optional[int] = None
    cloud_cover: Optional[float] = None
    weather_code: Optional[str] = None
    weather_text: Optional[str] = None
    dew_point: Optional[float] = None
    heat_index: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """データ型の変換と検証"""
        # 日時がstrの場合は変換
        if isinstance(self.date, str):
            self.date = datetime.fromisoformat(self.date)

        # 天気状況がstrの場合は変換
        if isinstance(self.weather, str):
            try:
                self.weather = WeatherCondition(self.weather)
            except ValueError:
                # 既知の天気状況にマッピング
                weather_mapping = {
                    "晴れ": WeatherCondition.CLEAR,
                    "曇り": WeatherCondition.CLOUDY,
                    "雨": WeatherCondition.RAIN,
                    "雪": WeatherCondition.SNOW,
                }
                self.weather = weather_mapping.get(self.weather, WeatherCondition.UNKNOWN)

        # 風向きがstrの場合は変換
        if isinstance(self.wind_direction, str):
            try:
                self.wind_direction = WindDirection(self.wind_direction)
            except ValueError:
                self.wind_direction = WindDirection.VARIABLE

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "location": self.location,
            "date": self.date.isoformat(),
            "weather": self.weather.value,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "precipitation_mm": self.precipitation_mm,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction.value,
            "pressure": self.pressure,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
            "cloud_cover": self.cloud_cover,
            "weather_code": self.weather_code,
            "weather_text": self.weather_text,
            "dew_point": self.dew_point,
            "heat_index": self.heat_index,
            "raw_data": self.raw_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherForecast":
        """辞書形式からインスタンスを作成"""
        # データのコピーを作成
        data_copy = data.copy()

        # 日時フィールドの正規化
        if "datetime" in data_copy and "date" not in data_copy:
            data_copy["date"] = data_copy.pop("datetime")

        # 気温フィールドの正規化
        if "temp" in data_copy and "temperature" not in data_copy:
            data_copy["temperature"] = data_copy.pop("temp")

        # 体感温度のデフォルト値設定
        if "feels_like" not in data_copy and "temperature" in data_copy:
            data_copy["feels_like"] = data_copy["temperature"]

        # 湿度フィールドの正規化
        if "humid" in data_copy and "humidity" not in data_copy:
            data_copy["humidity"] = data_copy.pop("humid")

        return cls(**data_copy)

    def is_good_weather(self) -> bool:
        """良い天気かどうかを判定

        Returns:
            bool: 晴れまたは曇り時々晴れで、
                 気温が10-30℃、降水量が1mm未満の場合True
        """
        good_conditions = [WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY]

        return (
            self.weather in good_conditions
            and 10 <= self.temperature <= 30
            and self.precipitation_mm < 1.0
        )

    def is_severe_weather(self) -> bool:
        """悪天候かどうかを判定

        Returns:
            bool: 以下の条件のいずれかに該当する場合True
            - 大雨、大雪、嵐、雷
            - 降水量が50mm以上
            - 風速が15m/s以上
            - 気温が35℃以上または0℃未満
        """
        severe_conditions = [
            WeatherCondition.HEAVY_RAIN,
            WeatherCondition.HEAVY_SNOW,
            WeatherCondition.STORM,
            WeatherCondition.THUNDER,
            WeatherCondition.SEVERE_STORM,
        ]

        return (
            self.weather in severe_conditions
            or self.precipitation_mm >= 50
            or self.wind_speed >= 15
            or self.temperature >= 35
            or self.temperature < 0
        )

    def get_precipitation_severity(self) -> str:
        """降水量の強度を取得

        Returns:
            str: なし/小雨/雨/大雨/豪雨
        """
        if self.precipitation_mm < 1:
            return "なし"
        elif self.precipitation_mm < 5:
            return "小雨"
        elif self.precipitation_mm < 20:
            return "雨"
        elif self.precipitation_mm < 50:
            return "大雨"
        else:
            return "豪雨"

    def get_comfort_level(self) -> str:
        """体感的な快適度を取得

        Returns:
            str: 快適/やや快適/普通/やや不快/不快
        """
        # 気温と湿度から不快指数を計算
        discomfort_index = 0.81 * self.temperature + 0.01 * self.humidity * (
            0.99 * self.temperature - 14.3
        ) + 46.3

        if discomfort_index < 60:
            return "快適"
        elif discomfort_index < 70:
            return "やや快適"
        elif discomfort_index < 75:
            return "普通"
        elif discomfort_index < 80:
            return "やや不快"
        else:
            return "不快"
    
    def is_stable_weather(self) -> bool:
        """安定した天気かどうかを判定
        
        天気の変化が少なく、穏やかな状態かを判定
        
        Returns:
            bool: 安定した天気の場合True
        """
        # WeatherValidatorに委譲
        from src.data.weather.validators import WeatherValidator
        return WeatherValidator.is_stable_weather(self)
    
    def get_weather_stability(self) -> str:
        """天気の安定性を文字列で取得
        
        Returns:
            str: 安定/やや不安定/不安定/非常に不安定
        """
        # WeatherValidatorに委譲
        from src.data.weather.validators import WeatherValidator
        return WeatherValidator.get_weather_stability(self)