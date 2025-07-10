"""天気予報関連の設定モジュール"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.shared", override=False)


# 天気関連の定数クラス群
@dataclass
class TemperatureThresholds:
    """気温閾値の定数（環境変数でオーバーライド可能）"""
    HOT_WEATHER: float = 30.0          # 暑い天気の閾値
    WARM_WEATHER: float = 25.0         # 暖かい天気の閾値
    COOL_WEATHER: float = 10.0         # 涼しい天気の閾値
    COLD_WEATHER: float = 5.0          # 寒い天気の閾値
    COLD_COMMENT_THRESHOLD: float = 12.0  # 寒さコメントの閾値
    
    # 気温差の閾値
    SIGNIFICANT_DAILY_DIFF: float = 5.0     # 前日との有意な気温差
    HOURLY_SIGNIFICANT_DIFF: float = 3.0    # 12時間での有意な気温差
    LARGE_DAILY_RANGE: float = 15.0         # 大きな日較差
    MEDIUM_DAILY_RANGE: float = 10.0        # 中程度の日較差
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.HOT_WEATHER = float(os.getenv("TEMP_HOT_WEATHER_THRESHOLD", str(self.HOT_WEATHER)))
        self.WARM_WEATHER = float(os.getenv("TEMP_WARM_WEATHER_THRESHOLD", str(self.WARM_WEATHER)))
        self.COOL_WEATHER = float(os.getenv("TEMP_COOL_WEATHER_THRESHOLD", str(self.COOL_WEATHER)))
        self.COLD_WEATHER = float(os.getenv("TEMP_COLD_WEATHER_THRESHOLD", str(self.COLD_WEATHER)))
        self.COLD_COMMENT_THRESHOLD = float(os.getenv("TEMP_COLD_COMMENT_THRESHOLD", str(self.COLD_COMMENT_THRESHOLD)))
        self.SIGNIFICANT_DAILY_DIFF = float(os.getenv("TEMP_SIGNIFICANT_DAILY_DIFF", str(self.SIGNIFICANT_DAILY_DIFF)))
        self.HOURLY_SIGNIFICANT_DIFF = float(os.getenv("TEMP_HOURLY_SIGNIFICANT_DIFF", str(self.HOURLY_SIGNIFICANT_DIFF)))
        self.LARGE_DAILY_RANGE = float(os.getenv("TEMP_LARGE_DAILY_RANGE", str(self.LARGE_DAILY_RANGE)))
        self.MEDIUM_DAILY_RANGE = float(os.getenv("TEMP_MEDIUM_DAILY_RANGE", str(self.MEDIUM_DAILY_RANGE)))


@dataclass
class HumidityThresholds:
    """湿度閾値の定数（環境変数でオーバーライド可能）"""
    HIGH_HUMIDITY: float = 80.0        # 高湿度の閾値
    LOW_HUMIDITY: float = 30.0         # 低湿度の閾値
    VERY_HIGH_HUMIDITY: float = 90.0   # 非常に高い湿度
    VERY_LOW_HUMIDITY: float = 20.0    # 非常に低い湿度
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.HIGH_HUMIDITY = float(os.getenv("HUMIDITY_HIGH_THRESHOLD", str(self.HIGH_HUMIDITY)))
        self.LOW_HUMIDITY = float(os.getenv("HUMIDITY_LOW_THRESHOLD", str(self.LOW_HUMIDITY)))
        self.VERY_HIGH_HUMIDITY = float(os.getenv("HUMIDITY_VERY_HIGH_THRESHOLD", str(self.VERY_HIGH_HUMIDITY)))
        self.VERY_LOW_HUMIDITY = float(os.getenv("HUMIDITY_VERY_LOW_THRESHOLD", str(self.VERY_LOW_HUMIDITY)))


@dataclass
class PrecipitationThresholds:
    """降水量閾値の定数（環境変数でオーバーライド可能）"""
    LIGHT_RAIN: float = 1.0            # 小雨の閾値
    MODERATE_RAIN: float = 5.0         # 中雨の閾値
    HEAVY_RAIN: float = 10.0           # 大雨の閾値
    VERY_HEAVY_RAIN: float = 30.0      # 激しい雨の閾値
    THUNDER_STRONG_THRESHOLD: float = 5.0  # 雷雨強弱判定の閾値
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.LIGHT_RAIN = float(os.getenv("PRECIP_LIGHT_RAIN_THRESHOLD", str(self.LIGHT_RAIN)))
        self.MODERATE_RAIN = float(os.getenv("PRECIP_MODERATE_RAIN_THRESHOLD", str(self.MODERATE_RAIN)))
        self.HEAVY_RAIN = float(os.getenv("PRECIP_HEAVY_RAIN_THRESHOLD", str(self.HEAVY_RAIN)))
        self.VERY_HEAVY_RAIN = float(os.getenv("PRECIP_VERY_HEAVY_RAIN_THRESHOLD", str(self.VERY_HEAVY_RAIN)))
        self.THUNDER_STRONG_THRESHOLD = float(os.getenv("PRECIP_THUNDER_STRONG_THRESHOLD", str(self.THUNDER_STRONG_THRESHOLD)))


@dataclass
class WindSpeedThresholds:
    """風速閾値の定数（環境変数でオーバーライド可能）"""
    LIGHT_BREEZE: float = 3.0          # 軽い風
    MODERATE_BREEZE: float = 7.0       # 中程度の風
    STRONG_BREEZE: float = 12.0        # 強い風
    GALE: float = 20.0                 # 強風
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.LIGHT_BREEZE = float(os.getenv("WIND_LIGHT_BREEZE_THRESHOLD", str(self.LIGHT_BREEZE)))
        self.MODERATE_BREEZE = float(os.getenv("WIND_MODERATE_BREEZE_THRESHOLD", str(self.MODERATE_BREEZE)))
        self.STRONG_BREEZE = float(os.getenv("WIND_STRONG_BREEZE_THRESHOLD", str(self.STRONG_BREEZE)))
        self.GALE = float(os.getenv("WIND_GALE_THRESHOLD", str(self.GALE)))


@dataclass
class DataValidationRanges:
    """データ検証用の値域（環境変数でオーバーライド可能）"""
    MIN_TEMPERATURE: float = -50.0     # 最低気温
    MAX_TEMPERATURE: float = 60.0      # 最高気温
    MIN_HUMIDITY: float = 0.0          # 最低湿度
    MAX_HUMIDITY: float = 100.0        # 最高湿度
    MIN_WIND_SPEED: float = 0.0        # 最低風速
    MAX_WIND_SPEED: float = 200.0      # 最高風速（台風含む）
    MIN_PRECIPITATION: float = 0.0     # 最低降水量
    MAX_PRECIPITATION: float = 500.0   # 最高降水量（極端な場合）
    MIN_WIND_DIRECTION: float = 0.0    # 最小風向
    MAX_WIND_DIRECTION: float = 360.0  # 最大風向
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.MIN_TEMPERATURE = float(os.getenv("VALIDATION_MIN_TEMPERATURE", str(self.MIN_TEMPERATURE)))
        self.MAX_TEMPERATURE = float(os.getenv("VALIDATION_MAX_TEMPERATURE", str(self.MAX_TEMPERATURE)))
        self.MIN_HUMIDITY = float(os.getenv("VALIDATION_MIN_HUMIDITY", str(self.MIN_HUMIDITY)))
        self.MAX_HUMIDITY = float(os.getenv("VALIDATION_MAX_HUMIDITY", str(self.MAX_HUMIDITY)))
        self.MIN_WIND_SPEED = float(os.getenv("VALIDATION_MIN_WIND_SPEED", str(self.MIN_WIND_SPEED)))
        self.MAX_WIND_SPEED = float(os.getenv("VALIDATION_MAX_WIND_SPEED", str(self.MAX_WIND_SPEED)))
        self.MIN_PRECIPITATION = float(os.getenv("VALIDATION_MIN_PRECIPITATION", str(self.MIN_PRECIPITATION)))
        self.MAX_PRECIPITATION = float(os.getenv("VALIDATION_MAX_PRECIPITATION", str(self.MAX_PRECIPITATION)))
        self.MIN_WIND_DIRECTION = float(os.getenv("VALIDATION_MIN_WIND_DIRECTION", str(self.MIN_WIND_DIRECTION)))
        self.MAX_WIND_DIRECTION = float(os.getenv("VALIDATION_MAX_WIND_DIRECTION", str(self.MAX_WIND_DIRECTION)))


@dataclass
class WeatherConstants:
    """天気関連の統合定数（環境変数でオーバーライド可能）"""
    temperature: TemperatureThresholds = field(default_factory=TemperatureThresholds)
    humidity: HumidityThresholds = field(default_factory=HumidityThresholds)
    precipitation: PrecipitationThresholds = field(default_factory=PrecipitationThresholds)
    wind: WindSpeedThresholds = field(default_factory=WindSpeedThresholds)
    validation: DataValidationRanges = field(default_factory=DataValidationRanges)
    
    # その他の天気定数
    HEATSTROKE_WARNING_TEMP: float = 34.0  # 熱中症警戒開始温度
    HEATSTROKE_SEVERE_TEMP: float = 35.0   # 熱中症厳重警戒温度
    COLD_WARNING_TEMP: float = 15.0        # 防寒対策が不要になる温度
    WEATHER_CHANGE_THRESHOLD: int = 2       # 「変わりやすい」と判定する変化回数の閾値
    
    # 天気タイプキーワード
    SUNNY_WEATHER_KEYWORDS: List[str] = field(default_factory=lambda: ["晴", "快晴", "晴天"])
    
    # 天気タイプ分類用キーワード
    WEATHER_TYPE_KEYWORDS: Dict[str, List[str]] = field(default_factory=lambda: {
        'sunny': ["晴", "快晴"],
        'cloudy': ["曇", "くもり", "うすぐもり", "薄曇"],
        'rainy': ["雨", "rain"]
    })
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.HEATSTROKE_WARNING_TEMP = float(os.getenv("WEATHER_HEATSTROKE_WARNING_TEMP", str(self.HEATSTROKE_WARNING_TEMP)))
        self.HEATSTROKE_SEVERE_TEMP = float(os.getenv("WEATHER_HEATSTROKE_SEVERE_TEMP", str(self.HEATSTROKE_SEVERE_TEMP)))
        self.COLD_WARNING_TEMP = float(os.getenv("WEATHER_COLD_WARNING_TEMP", str(self.COLD_WARNING_TEMP)))
        self.WEATHER_CHANGE_THRESHOLD = int(os.getenv("WEATHER_CHANGE_THRESHOLD", str(self.WEATHER_CHANGE_THRESHOLD)))


@dataclass
class WeatherConfig:
    """天気予報関連の設定
    
    天気情報の取得、キャッシュ、予報期間などの設定を管理します。
    温度差や降水量の闾値など、天気コメント生成に必要なパラメータも含まれます。
    """
    # 基本設定
    default_location: str = field(default="東京")
    forecast_hours: int = field(default=24)  # デフォルト予報時間数
    forecast_hours_ahead: int = field(default=12)
    forecast_days: int = field(default=3)
    
    # キャッシュ設定
    cache_ttl_seconds: int = field(default=3600)  # 1 hour
    cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))
    enable_caching: bool = field(default=True)
    forecast_cache_retention_days: int = field(default=7)
    
    # API設定
    use_optimized_forecast: bool = field(default=True)  # 最適化された翌日予報取得を使用
    
    # 温度差閾値設定（temperature_analysis.pyで使用）
    temp_diff_threshold_previous_day: float = field(default=5.0)  # 前日との有意な気温差
    temp_diff_threshold_12hours: float = field(default=3.0)  # 12時間での有意な気温差
    daily_temp_range_threshold_large: float = field(default=15.0)  # 大きな日較差
    daily_temp_range_threshold_medium: float = field(default=10.0)  # 中程度の日較差
    
    # 温度分類の閾値（後方互換性のため）
    temp_threshold_hot: float = field(default=30.0)
    temp_threshold_warm: float = field(default=25.0)
    temp_threshold_cool: float = field(default=10.0)
    temp_threshold_cold: float = field(default=5.0)
    
    # 閾値設定（廃止予定 - weather_constantsを使用）
    high_temp_threshold: float = field(default=30.0)
    low_temp_threshold: float = field(default=10.0)
    heavy_rain_threshold: float = field(default=30.0)
    strong_wind_threshold: float = field(default=15.0)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.default_location = os.getenv("DEFAULT_WEATHER_LOCATION", self.default_location)
        self.forecast_hours = int(os.getenv("WEATHER_FORECAST_HOURS", str(self.forecast_hours)))
        self.forecast_hours_ahead = int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", str(self.forecast_hours_ahead)))
        self.forecast_days = int(os.getenv("WEATHER_FORECAST_DAYS", str(self.forecast_days)))
        self.cache_ttl_seconds = int(os.getenv("WEATHER_CACHE_TTL", str(self.cache_ttl_seconds)))
        self.cache_dir = Path(os.getenv("WEATHER_CACHE_DIR", str(self.cache_dir)))
        self.enable_caching = os.getenv("WEATHER_ENABLE_CACHING", "true" if self.enable_caching else "false").lower() == "true"
        self.use_optimized_forecast = os.getenv("WEATHER_USE_OPTIMIZED_FORECAST", "true" if self.use_optimized_forecast else "false").lower() == "true"
        self.forecast_cache_retention_days = int(os.getenv("FORECAST_CACHE_RETENTION_DAYS", str(self.forecast_cache_retention_days)))
        
        # 温度差閾値設定の読み込み
        self.temp_diff_threshold_previous_day = float(os.getenv("TEMP_DIFF_THRESHOLD_PREVIOUS_DAY", str(self.temp_diff_threshold_previous_day)))
        self.temp_diff_threshold_12hours = float(os.getenv("TEMP_DIFF_THRESHOLD_12HOURS", str(self.temp_diff_threshold_12hours)))
        self.daily_temp_range_threshold_large = float(os.getenv("DAILY_TEMP_RANGE_THRESHOLD_LARGE", str(self.daily_temp_range_threshold_large)))
        self.daily_temp_range_threshold_medium = float(os.getenv("DAILY_TEMP_RANGE_THRESHOLD_MEDIUM", str(self.daily_temp_range_threshold_medium)))
        
        # 温度分類の閾値の読み込み
        self.temp_threshold_hot = float(os.getenv("TEMP_THRESHOLD_HOT", str(self.temp_threshold_hot)))
        self.temp_threshold_warm = float(os.getenv("TEMP_THRESHOLD_WARM", str(self.temp_threshold_warm)))
        self.temp_threshold_cool = float(os.getenv("TEMP_THRESHOLD_COOL", str(self.temp_threshold_cool)))
        self.temp_threshold_cold = float(os.getenv("TEMP_THRESHOLD_COLD", str(self.temp_threshold_cold)))
        
        # キャッシュディレクトリを作成（権限エラーを考慮）
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # 権限エラーの場合は警告のみ（Config.ensure_directories()で後から作成可能）
            pass