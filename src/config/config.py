"""
統一された設定管理システム

すべての設定を一元管理し、環境変数の読み込みと検証を行う
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List
from functools import lru_cache

from dotenv import load_dotenv
from src.data.weather_data import WeatherCondition


class ConfigurationError(Exception):
    """設定エラー用のカスタム例外"""
    pass


logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env.shared", override=False)


@dataclass
class APIConfig:
    """API関連の設定"""
    # API Keys
    wxtech_api_key: str = field(default="")
    openai_api_key: str = field(default="")
    anthropic_api_key: str = field(default="")
    gemini_api_key: str = field(default="")
    
    # API Settings
    api_timeout: int = field(default=30)  # seconds
    retry_count: int = field(default=3)
    
    # AWS設定
    aws_access_key_id: str = field(default="")
    aws_secret_access_key: str = field(default="")
    aws_region: str = field(default="ap-northeast-1")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.wxtech_api_key = os.getenv("WXTECH_API_KEY", self.wxtech_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.api_timeout = int(os.getenv("API_TIMEOUT", str(self.api_timeout)))
        
        # AWS設定
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", self.aws_access_key_id)
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", self.aws_secret_access_key)
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", self.aws_region)
    
    def get_llm_key(self, provider: str) -> str:
        """LLMプロバイダーに対応するAPIキーを取得"""
        provider_map = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "anthropic": self.anthropic_api_key
        }
        return provider_map.get(provider.lower(), "")
    
    def validate_keys(self) -> Dict[str, bool]:
        """APIキーの存在を検証"""
        return {
            "openai": bool(self.openai_api_key),
            "gemini": bool(self.gemini_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "wxtech": bool(self.wxtech_api_key),
            "aws": bool(self.aws_access_key_id and self.aws_secret_access_key)
        }
    
    def mask_sensitive_data(self) -> Dict[str, Any]:
        """機密データをマスクした設定を返す"""
        return {
            "wxtech_api_key": "***" if self.wxtech_api_key else "",
            "openai_api_key": "***" if self.openai_api_key else "",
            "anthropic_api_key": "***" if self.anthropic_api_key else "",
            "gemini_api_key": "***" if self.gemini_api_key else "",
            "aws_access_key_id": "***" if self.aws_access_key_id else "",
            "aws_secret_access_key": "***" if self.aws_secret_access_key else "",
            "aws_region": self.aws_region,
            "api_timeout": self.api_timeout,
            "retry_count": self.retry_count
        }
    
    def is_secure(self) -> bool:
        """すべての必須セキュリティ設定が適切に設定されているかチェック"""
        # 最低限1つのLLM APIキーが設定されている必要がある
        has_llm_key = any([
            self.openai_api_key,
            self.gemini_api_key,
            self.anthropic_api_key
        ])
        
        # wxtech APIキーは必須
        has_weather_key = bool(self.wxtech_api_key)
        
        return has_llm_key and has_weather_key


@dataclass
class WeatherConfig:
    """天気予報関連の設定"""
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


@dataclass(frozen=True)
class SystemConstants:
    """システム全体の定数"""
    # API設定のデフォルト値
    DEFAULT_API_TIMEOUT: int = 30              # APIタイムアウト（秒）
    DEFAULT_MAX_RETRIES: int = 3               # 最大リトライ回数
    DEFAULT_RATE_LIMIT_DELAY: float = 0.1      # レート制限回避遅延（秒）
    DEFAULT_CACHE_TTL: int = 300               # キャッシュTTL（5分）
    
    # 予報設定のデフォルト値
    DEFAULT_FORECAST_HOURS: int = 24           # デフォルト予報時間数
    DEFAULT_FORECAST_HOURS_AHEAD: int = 0      # 現在時刻から予報を取得
    MAX_FORECAST_HOURS: int = 168              # 最大予報時間（7日間）
    DEFAULT_FORECAST_CACHE_RETENTION_DAYS: int = 7  # 予報キャッシュ保持日数
    
    # コメント関連
    DEFAULT_COMMENT_LIMIT: int = 15            # デフォルトコメント文字数制限
    MAX_COMMENTS_PER_SEASON: int = 20          # 季節あたりの最大コメント数
    SEASONAL_CACHE_LIMIT: int = 3              # 季節別キャッシュの最大保持数
    DEFAULT_RECENT_COMMENTS_LIMIT: int = 100   # デフォルト最近コメント取得数
    
    # 文字列制限
    MAX_COMMENT_LENGTH: int = 50               # 最大コメント長
    WARNING_COMMENT_LENGTH: int = 15           # コメント長警告閾値
    MAX_LOCATION_NAME_LENGTH: int = 20         # 最大地点名長
    MAX_ERROR_MESSAGE_LENGTH: int = 200        # 最大エラーメッセージ長
    
    # 検証用の制限値
    MAX_API_TIMEOUT: int = 300                 # 最大APIタイムアウト（5分）
    VALID_LOG_LEVELS: List[str] = field(default_factory=lambda: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])


@dataclass
class AppSettings:
    """アプリケーション全体の設定"""
    env: str = field(default="development")
    debug: bool = field(default=False)
    log_level: str = field(default="INFO")
    
    # データ設定
    data_dir: Path = field(default_factory=lambda: Path("output"))
    csv_dir: Path = field(default_factory=lambda: Path("output"))
    
    # バッチ処理設定
    batch_concurrent_limit: int = field(default=3)
    batch_request_timeout: int = field(default=120000)  # milliseconds
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.env = os.getenv("APP_ENV", self.env)
        self.debug = os.getenv("DEBUG", str(self.debug)).lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.data_dir)))
        self.csv_dir = Path(os.getenv("CSV_DIR", str(self.csv_dir)))


@dataclass
class ServerConfig:
    """サーバー関連の設定"""
    api_host: str = field(default="0.0.0.0")
    api_port: int = field(default=8000)
    frontend_port: int = field(default=3000)
    cors_origins: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", str(self.api_port)))
        self.frontend_port = int(os.getenv("FRONTEND_PORT", str(self.frontend_port)))
        
        # CORS origins
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            self.cors_origins = [origin.strip() for origin in cors_env.split(",")]
        else:
            # デフォルトのCORS origins
            self.cors_origins = [
                f"http://localhost:{self.frontend_port}",
                f"http://127.0.0.1:{self.frontend_port}",
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]


@dataclass
class LLMConfig:
    """LLM関連の設定"""
    default_provider: str = field(default="gemini")
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=1000)
    
    # プロバイダー別の設定
    openai_model: str = field(default="gpt-4o-mini")
    anthropic_model: str = field(default="claude-3-haiku-20240307")
    gemini_model: str = field(default="gemini-1.5-flash")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", self.default_provider)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(self.temperature)))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", str(self.max_tokens)))
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.anthropic_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)


@dataclass
class LangGraphConfig:
    """LangGraph統合機能の設定"""
    enable_weather_integration: bool = field(default=True)
    auto_location_detection: bool = field(default=False)
    weather_context_window: int = field(default=24)
    min_confidence_threshold: float = field(default=0.7)
    
    def __post_init__(self):
        """環境変数から設定を読み込む"""
        self.enable_weather_integration = os.getenv("LANGGRAPH_ENABLE_WEATHER", "true" if self.enable_weather_integration else "false").lower() == "true"
        self.auto_location_detection = os.getenv("LANGGRAPH_AUTO_LOCATION", "true" if self.auto_location_detection else "false").lower() == "true"
        self.weather_context_window = int(os.getenv("LANGGRAPH_WEATHER_CONTEXT_WINDOW", str(self.weather_context_window)))
        self.min_confidence_threshold = float(os.getenv("LANGGRAPH_MIN_CONFIDENCE", str(self.min_confidence_threshold)))


@dataclass
class CommentConfig:
    """コメント生成の設定"""
    # 温度閾値
    heat_warning_threshold: float = field(default=30.0)  # 熱中症警告温度
    cold_warning_threshold: float = field(default=15.0)  # 防寒警告温度
    
    # トレンド分析期間
    trend_hours_ahead: int = field(default=12)  # 気象変化を分析する時間（時間）
    
    # 天気スコア（良い天気ほど高いスコア）
    weather_scores: Dict[WeatherCondition, int] = field(default_factory=lambda: {
        WeatherCondition.CLEAR: 5,
        WeatherCondition.PARTLY_CLOUDY: 4,
        WeatherCondition.CLOUDY: 3,
        WeatherCondition.RAIN: 2,
        WeatherCondition.HEAVY_RAIN: 0,
        WeatherCondition.SNOW: 1,
        WeatherCondition.HEAVY_SNOW: 0,
        WeatherCondition.STORM: 0,
        WeatherCondition.FOG: 2,
        WeatherCondition.UNKNOWN: 2,
    })
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.heat_warning_threshold = float(os.getenv("COMMENT_HEAT_WARNING_THRESHOLD", str(self.heat_warning_threshold)))
        self.cold_warning_threshold = float(os.getenv("COMMENT_COLD_WARNING_THRESHOLD", str(self.cold_warning_threshold)))
        self.trend_hours_ahead = int(os.getenv("COMMENT_TREND_HOURS_AHEAD", str(self.trend_hours_ahead)))


@dataclass
class SevereWeatherConfig:
    """悪天候時の特別なコメント選択設定"""
    # 悪天候として特別扱いする条件
    severe_weather_conditions: List[WeatherCondition] = field(default_factory=lambda: [
        WeatherCondition.SEVERE_STORM,  # 大雨・嵐
        WeatherCondition.STORM,         # 嵐
        WeatherCondition.THUNDER,       # 雷
        WeatherCondition.HEAVY_RAIN,    # 大雨
        WeatherCondition.RAIN,          # 雨
        WeatherCondition.FOG,           # 霧
        WeatherCondition.HEAVY_SNOW,    # 大雪
        WeatherCondition.SNOW,          # 雪
    ])
    
    # 悪天候時に推奨される天気コメント
    severe_weather_comments: Dict[str, List[str]] = field(default_factory=lambda: {
        "大雨・嵐": [
            "大荒れの空",
            "激しい雨に警戒",
            "外出は控えめに",
            "安全第一の一日",
            "荒天に要注意"
        ],
        "雨": [
            "雨雲が広がる空",
            "本格的な雨に注意",
            "濡れ対策が必要",
            "雨が続く空模様",
            "雨脚が強まる可能性"
        ],
        "雷": [
            "雷に注意",
            "不安定な空模様",
            "急な雷雨に警戒",
            "空の様子に注意",
            "雷鳴轟く空"
        ],
        "霧": [
            "視界不良に注意",
            "霧に包まれる朝",
            "見通し悪い空",
            "慎重な行動を",
            "霧が立ち込める"
        ],
        "暴風": [
            "強風に警戒",
            "風が強い一日",
            "飛来物に注意",
            "外出時は要注意",
            "荒れ模様の空"
        ]
    })
    
    # 悪天候時に推奨されるアドバイスコメント
    severe_weather_advice: Dict[str, List[str]] = field(default_factory=lambda: {
        "大雨・嵐": [
            "室内で安全に",
            "無理な外出は避けて",
            "最新情報をチェック",
            "早めの帰宅を",
            "安全確保を優先"
        ],
        "雨": [
            "傘がお守り",
            "足元に注意を",
            "濡れ対策を忘れずに",
            "室内で過ごすのも",
            "雨具の準備を"
        ],
        "雷": [
            "建物内で待機を",
            "高い場所は避けて",
            "電気製品に注意",
            "屋内で安全に",
            "金属類から離れて"
        ],
        "霧": [
            "車の運転は慎重に",
            "ゆっくり移動を",
            "時間に余裕を持って",
            "足元に注意して",
            "明るい服装で"
        ],
        "暴風": [
            "飛来物に注意",
            "窓から離れて",
            "外出は最小限に",
            "しっかり固定を",
            "安全な場所で"
        ]
    })
    
    # 悪天候時の除外キーワード（これらを含むコメントは選ばない）
    exclude_keywords_severe: List[str] = field(default_factory=lambda: [
        "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い",
        "青空", "晴れ", "快晴", "日差し", "太陽",
        "散歩", "ピクニック", "お出かけ", "外出日和",
        "洗濯日和", "布団干し", "外遊び",
        "ニワカ雨が心配", "スッキリしない", "蒸し暑い"
    ])
    
    # 天気条件の日本語マッピング
    weather_condition_japanese: Dict[WeatherCondition, str] = field(default_factory=lambda: {
        WeatherCondition.SEVERE_STORM: "大雨・嵐",
        WeatherCondition.STORM: "嵐",
        WeatherCondition.THUNDER: "雷",
        WeatherCondition.HEAVY_RAIN: "大雨",
        WeatherCondition.RAIN: "雨",
        WeatherCondition.FOG: "霧",
        WeatherCondition.HEAVY_SNOW: "大雪",
        WeatherCondition.SNOW: "雪",
    })
    
    def is_severe_weather(self, condition: WeatherCondition) -> bool:
        """指定された天気条件が悪天候かどうか判定"""
        return condition in self.severe_weather_conditions
    
    def get_recommended_comments(self, condition: WeatherCondition) -> Dict[str, List[str]]:
        """指定された天気条件に推奨されるコメントを取得"""
        japanese_name = self.weather_condition_japanese.get(condition, "")
        
        return {
            "weather": self.severe_weather_comments.get(japanese_name, []),
            "advice": self.severe_weather_advice.get(japanese_name, [])
        }


@dataclass
class UISettings:
    """UI関連の設定"""
    # 基本設定
    page_title: str = field(default="天気コメント生成システム")
    page_icon: str = field(default="☀️")
    layout: str = field(default="wide")
    sidebar_state: str = field(default="expanded")
    theme: str = field(default="light")
    
    # コンポーネント設定
    max_locations_per_generation: int = field(default=30)
    default_llm_provider: str = field(default="gemini")
    show_debug_info: bool = field(default=False)
    
    # 表示設定
    date_format: str = field(default="%Y年%m月%d日 %H時%M分")
    timezone: str = field(default="Asia/Tokyo")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        if os.getenv("MAX_LOCATIONS_PER_GENERATION"):
            self.max_locations_per_generation = int(os.getenv("MAX_LOCATIONS_PER_GENERATION"))
        if os.getenv("DEFAULT_LLM_PROVIDER"):
            self.default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER")


@dataclass
class GenerationSettings:
    """コメント生成関連の設定"""
    # タイムアウト設定
    generation_timeout: int = field(default=300)  # 秒
    api_timeout: int = field(default=30)  # 秒
    
    # リトライ設定
    max_retries: int = field(default=3)
    retry_delay: float = field(default=1.0)
    
    # キャッシュ設定
    cache_enabled: bool = field(default=True)
    cache_ttl: int = field(default=3600)  # 秒
    
    # バッチ処理設定
    batch_size: int = field(default=5)
    concurrent_requests: int = field(default=3)
    
    # 品質設定
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=200)
    
    # NGワード設定
    ng_words_file: str = field(default="config/ng_words.yaml")
    expression_rules_file: str = field(default="config/expression_rules.yaml")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.generation_timeout = int(os.getenv("GENERATION_TIMEOUT", str(self.generation_timeout)))
        self.max_retries = int(os.getenv("GENERATION_MAX_RETRIES", str(self.max_retries)))
        self.retry_delay = float(os.getenv("GENERATION_RETRY_DELAY", str(self.retry_delay)))
        self.batch_size = int(os.getenv("GENERATION_BATCH_SIZE", str(self.batch_size)))
        self.concurrent_requests = int(os.getenv("GENERATION_CONCURRENT_REQUESTS", str(self.concurrent_requests)))


@dataclass
class DataSettings:
    """データ関連の設定"""
    # パス設定
    data_dir: Path = field(default_factory=lambda: Path("data"))
    forecast_cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))
    generation_history_file: Path = field(default_factory=lambda: Path("data/generation_history.json"))
    locations_file: Path = field(default_factory=lambda: Path("src/data/Chiten.csv"))
    
    # CSVファイル設定
    csv_output_dir: Path = field(default_factory=lambda: Path("output"))
    use_local_csv: bool = field(default=True)
    
    # データ保持設定
    max_history_records: int = field(default=1000)
    history_retention_days: int = field(default=30)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.data_dir)))
        self.forecast_cache_dir = Path(os.getenv("FORECAST_CACHE_DIR", str(self.forecast_cache_dir)))
        self.generation_history_file = Path(os.getenv("GENERATION_HISTORY_FILE", str(self.generation_history_file)))
        self.locations_file = Path(os.getenv("LOCATIONS_FILE", str(self.locations_file)))
        self.csv_output_dir = Path(os.getenv("CSV_OUTPUT_DIR", str(self.csv_output_dir)))
        self.use_local_csv = os.getenv("USE_LOCAL_CSV", "true" if self.use_local_csv else "false").lower() == "true"
        self.max_history_records = int(os.getenv("MAX_HISTORY_RECORDS", str(self.max_history_records)))
        self.history_retention_days = int(os.getenv("HISTORY_RETENTION_DAYS", str(self.history_retention_days)))


@dataclass
class Config:
    """統一された設定クラス"""
    api: APIConfig = field(default_factory=APIConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    app: AppSettings = field(default_factory=AppSettings)
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    weather_constants: WeatherConstants = field(default_factory=WeatherConstants)
    system_constants: SystemConstants = field(default_factory=SystemConstants)
    langgraph: LangGraphConfig = field(default_factory=LangGraphConfig)
    comment: CommentConfig = field(default_factory=CommentConfig)
    severe_weather: SevereWeatherConfig = field(default_factory=SevereWeatherConfig)
    ui: UISettings = field(default_factory=UISettings)
    generation: GenerationSettings = field(default_factory=GenerationSettings)
    data: DataSettings = field(default_factory=DataSettings)
    
    def __post_init__(self):
        """設定の検証"""
        self._validate()
        
        # ログレベルの設定
        logging.basicConfig(level=getattr(logging, self.app.log_level))
        
        if self.app.debug:
            logger.debug("Debug mode is enabled")
            logger.debug(f"Configuration loaded: {self.to_dict()}")
    
    def _validate(self):
        """設定の検証"""
        # 必須APIキーの確認（開発環境以外）
        if self.app.env == "production":
            missing_keys = []
            
            # 本番環境では必須のAPIキーをチェック
            if not self.api.wxtech_api_key:
                missing_keys.append("WXTECH_API_KEY")
            
            # 少なくとも1つのLLM APIキーが必要
            llm_keys = [
                self.api.openai_api_key,
                self.api.anthropic_api_key,
                self.api.gemini_api_key
            ]
            if not any(llm_keys):
                missing_keys.append("At least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY")
            
            if missing_keys:
                raise ConfigurationError(
                    f"Missing required configuration for production environment: {', '.join(missing_keys)}"
                )
        
        # 数値範囲の検証
        self._validate_weather_constants()
        self._validate_api_settings()
        self._validate_weather_config()
        self._validate_langgraph_config()
        
        # セキュリティ設定の検証
        self._validate_security_settings()
        
        # ディレクトリの作成は必要に応じて遅延実行（ensure_directories()メソッドを使用）
    
    def _validate_weather_constants(self):
        """天気関連定数の妥当性を検証"""
        wc = self.weather_constants
        
        # 温度閾値の妥当性チェック
        if not (-50 <= wc.temperature.COLD_WEATHER <= wc.temperature.COOL_WEATHER <= 
                wc.temperature.WARM_WEATHER <= wc.temperature.HOT_WEATHER <= 60):
            raise ConfigurationError(
                "温度閾値が不正です: COLD < COOL < WARM < HOT の関係を保つ必要があります"
            )
        
        # 湿度の範囲チェック
        if not (0 <= wc.humidity.VERY_LOW_HUMIDITY <= wc.humidity.LOW_HUMIDITY <= 
                wc.humidity.HIGH_HUMIDITY <= wc.humidity.VERY_HIGH_HUMIDITY <= 100):
            raise ConfigurationError(
                "湿度閾値が不正です: 0-100%の範囲で VERY_LOW < LOW < HIGH < VERY_HIGH の関係を保つ必要があります"
            )
        
        # 降水量の妥当性チェック
        if not (0 <= wc.precipitation.LIGHT_RAIN <= wc.precipitation.MODERATE_RAIN <= 
                wc.precipitation.HEAVY_RAIN <= wc.precipitation.VERY_HEAVY_RAIN):
            raise ConfigurationError(
                "降水量閾値が不正です: LIGHT < MODERATE < HEAVY < VERY_HEAVY の関係を保つ必要があります"
            )
        
        # 風速の妥当性チェック
        if not (0 <= wc.wind.LIGHT_BREEZE <= wc.wind.MODERATE_BREEZE <= 
                wc.wind.STRONG_BREEZE <= wc.wind.GALE):
            raise ConfigurationError(
                "風速閾値が不正です: LIGHT < MODERATE < STRONG < GALE の関係を保つ必要があります"
            )
        
        # 検証範囲の妥当性チェック
        val = wc.validation
        if val.MIN_TEMPERATURE >= val.MAX_TEMPERATURE:
            raise ConfigurationError("最低気温が最高気温以上に設定されています")
        if val.MIN_HUMIDITY >= val.MAX_HUMIDITY:
            raise ConfigurationError("最低湿度が最高湿度以上に設定されています")
        if val.MIN_WIND_SPEED >= val.MAX_WIND_SPEED:
            raise ConfigurationError("最低風速が最高風速以上に設定されています")
        if val.MIN_PRECIPITATION >= val.MAX_PRECIPITATION:
            raise ConfigurationError("最低降水量が最高降水量以上に設定されています")
    
    def _validate_api_settings(self):
        """API設定の妥当性を検証"""
        # APIタイムアウトの範囲チェック
        if not (1 <= self.api.api_timeout <= self.system_constants.MAX_API_TIMEOUT):
            raise ConfigurationError(
                f"APIタイムアウトは1-{self.system_constants.MAX_API_TIMEOUT}秒の範囲で設定してください"
            )
        
        # リトライ回数の範囲チェック
        if not (0 <= self.api.retry_count <= 10):
            raise ConfigurationError("リトライ回数は0-10の範囲で設定してください")
        
        # LLM温度パラメータの範囲チェック
        if not (0 <= self.llm.temperature <= 2):
            raise ConfigurationError("LLM温度パラメータは0-2の範囲で設定してください")
        
        # ログレベルの検証
        if self.app.log_level not in self.system_constants.VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"無効なログレベル: {self.app.log_level}. 有効な値: {', '.join(self.system_constants.VALID_LOG_LEVELS)}"
            )
    
    def _validate_weather_config(self):
        """天気設定の妥当性を検証"""
        # 予報時間の検証
        if self.weather.forecast_hours <= 0:
            raise ConfigurationError("forecast_hoursは1以上である必要があります")
        
        if self.weather.forecast_hours_ahead < 0:
            raise ConfigurationError("forecast_hours_aheadは0以上である必要があります")
        
        # 予報期間の妥当性検証
        if self.weather.forecast_hours + self.weather.forecast_hours_ahead > self.system_constants.MAX_FORECAST_HOURS:
            raise ConfigurationError(
                f"予報期間の合計が{self.system_constants.MAX_FORECAST_HOURS}時間を超えています"
            )
        
        # キャッシュ保持日数の検証
        if not (1 <= self.weather.forecast_cache_retention_days <= 30):
            raise ConfigurationError("forecast_cache_retention_daysは1-30日の範囲で設定してください")
    
    def _validate_langgraph_config(self):
        """LangGraph設定の妥当性を検証"""
        # 信頼度閾値の検証
        if not (0 <= self.langgraph.min_confidence_threshold <= 1):
            raise ConfigurationError("min_confidence_thresholdは0.0-1.0の範囲で設定してください")
        
        # コンテキスト窓の検証
        if not (1 <= self.langgraph.weather_context_window <= 168):
            raise ConfigurationError("weather_context_windowは1-168時間の範囲で設定してください")
    
    def _validate_security_settings(self):
        """セキュリティ設定の検証"""
        # APIキーのセキュリティチェック
        if not self.api.is_secure():
            logger.warning(
                "セキュリティ警告: 必須のAPIキーが設定されていません。"
                "最低限1つのLLM APIキーとWXTECH_API_KEYが必要です。"
            )
        
        # APIキーが環境変数から正しく読み込まれているか確認
        if self.api.wxtech_api_key and self.api.wxtech_api_key.startswith("sk-"):
            logger.warning("警告: APIキーが公開される可能性があります。環境変数を確認してください。")
        
        # デバッグモードでのセキュリティ警告
        if hasattr(self.app, 'debug_mode') and self.app.debug_mode:
            logger.info("デバッグモードが有効です。本番環境では無効にしてください。")
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す（機密データはマスク済み）"""
        masked_api = self.api.mask_sensitive_data()
        return {
            "api": masked_api,
            "weather": {
                "default_location": self.weather.default_location,
                "forecast_hours": self.weather.forecast_hours,
                "forecast_hours_ahead": self.weather.forecast_hours_ahead,
                "forecast_days": self.weather.forecast_days,
                "cache_ttl_seconds": self.weather.cache_ttl_seconds,
                "cache_dir": str(self.weather.cache_dir),
                "enable_caching": self.weather.enable_caching,
                "forecast_cache_retention_days": self.weather.forecast_cache_retention_days,
                "use_optimized_forecast": self.weather.use_optimized_forecast,
            },
            "app": {
                "env": self.app.env,
                "debug": self.app.debug,
                "log_level": self.app.log_level,
                "data_dir": str(self.app.data_dir),
                "csv_dir": str(self.app.csv_dir),
                "batch_concurrent_limit": self.app.batch_concurrent_limit,
                "batch_request_timeout": self.app.batch_request_timeout,
            },
            "server": {
                "api_host": self.server.api_host,
                "api_port": self.server.api_port,
                "frontend_port": self.server.frontend_port,
                "cors_origins": self.server.cors_origins,
            },
            "llm": {
                "default_provider": self.llm.default_provider,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "openai_model": self.llm.openai_model,
                "anthropic_model": self.llm.anthropic_model,
                "gemini_model": self.llm.gemini_model,
            },
            "weather_constants": {
                "temperature": self.weather_constants.temperature.__dict__,
                "humidity": self.weather_constants.humidity.__dict__,
                "precipitation": self.weather_constants.precipitation.__dict__,
                "wind": self.weather_constants.wind.__dict__,
                "validation": self.weather_constants.validation.__dict__,
            },
            "system_constants": self.system_constants.__dict__,
            "langgraph": {
                "enable_weather_integration": self.langgraph.enable_weather_integration,
                "auto_location_detection": self.langgraph.auto_location_detection,
                "weather_context_window": self.langgraph.weather_context_window,
                "min_confidence_threshold": self.langgraph.min_confidence_threshold,
            },
            "comment": {
                "heat_warning_threshold": self.comment.heat_warning_threshold,
                "cold_warning_threshold": self.comment.cold_warning_threshold,
                "trend_hours_ahead": self.comment.trend_hours_ahead,
                "weather_scores": {k.name: v for k, v in self.comment.weather_scores.items()},
            },
            "severe_weather": {
                "severe_weather_conditions": [c.name for c in self.severe_weather.severe_weather_conditions],
                "exclude_keywords_severe": self.severe_weather.exclude_keywords_severe,
            },
            "ui": {
                "page_title": self.ui.page_title,
                "page_icon": self.ui.page_icon,
                "layout": self.ui.layout,
                "max_locations_per_generation": self.ui.max_locations_per_generation,
                "default_llm_provider": self.ui.default_llm_provider,
                "show_debug_info": self.ui.show_debug_info,
            },
            "generation": {
                "generation_timeout": self.generation.generation_timeout,
                "max_retries": self.generation.max_retries,
                "batch_size": self.generation.batch_size,
                "concurrent_requests": self.generation.concurrent_requests,
                "cache_enabled": self.generation.cache_enabled,
            },
            "data": {
                "data_dir": str(self.data.data_dir),
                "csv_output_dir": str(self.data.csv_output_dir),
                "use_local_csv": self.data.use_local_csv,
                "max_history_records": self.data.max_history_records,
            }
        }
    
    def ensure_directories(self) -> None:
        """必要なディレクトリを作成（遅延実行用）"""
        directories = [
            self.app.data_dir,
            self.app.csv_dir,
            self.weather.cache_dir,
            self.data.data_dir,
            self.data.forecast_cache_dir,
            self.data.csv_output_dir
        ]
        
        for directory in directories:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"ディレクトリを作成しました: {directory}")
                except Exception as e:
                    logger.error(f"ディレクトリの作成に失敗しました {directory}: {e}")
                    raise ConfigurationError(f"ディレクトリの作成に失敗しました: {directory}")
    
    def ensure_directory(self, directory_name: str) -> Path:
        """特定のディレクトリを確実に作成して返す"""
        directory_map = {
            "data": self.app.data_dir,
            "csv": self.app.csv_dir,
            "cache": self.weather.cache_dir,
            "forecast_cache": self.data.forecast_cache_dir,
            "csv_output": self.data.csv_output_dir
        }
        
        directory = directory_map.get(directory_name)
        if not directory:
            raise ValueError(f"Unknown directory name: {directory_name}")
        
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"ディレクトリを作成しました: {directory}")
        
        return directory


# シングルトンパターンで設定インスタンスを管理
@lru_cache(maxsize=1)
def get_config() -> Config:
    """設定インスタンスを取得"""
    return Config()


# 互換性のためのヘルパー関数
def get_api_config() -> APIConfig:
    """API設定を取得"""
    return get_config().api


def get_weather_config() -> WeatherConfig:
    """天気設定を取得"""
    return get_config().weather


def get_app_settings() -> AppSettings:
    """アプリケーション設定を取得"""
    return get_config().app


def get_server_config() -> ServerConfig:
    """サーバー設定を取得"""
    return get_config().server


def get_llm_config() -> LLMConfig:
    """LLM設定を取得"""
    return get_config().llm


def get_weather_constants() -> WeatherConstants:
    """天気関連の定数を取得"""
    return get_config().weather_constants


def get_system_constants() -> SystemConstants:
    """システム定数を取得"""
    return get_config().system_constants


def get_langgraph_config() -> LangGraphConfig:
    """LangGraph設定を取得"""
    return get_config().langgraph


def get_comment_config() -> CommentConfig:
    """コメント設定を取得"""
    return get_config().comment


def get_severe_weather_config() -> SevereWeatherConfig:
    """悪天候設定を取得"""
    return get_config().severe_weather


def ensure_config_directories() -> None:
    """設定で定義されたすべてのディレクトリを作成"""
    get_config().ensure_directories()


def get_ui_settings() -> UISettings:
    """UI設定を取得"""
    return get_config().ui


def get_generation_settings() -> GenerationSettings:
    """生成設定を取得"""
    return get_config().generation


def get_data_settings() -> DataSettings:
    """データ設定を取得"""
    return get_config().data