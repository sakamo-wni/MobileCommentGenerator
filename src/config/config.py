"""
統一された設定管理システム

すべての設定を一元管理し、環境変数の読み込みと検証を行う
"""


class ConfigurationError(Exception):
    """設定エラー用のカスタム例外"""
    pass

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

from dotenv import load_dotenv

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
    gemini_model: str = field(default="gemini-1.5-flash")
    api_timeout: int = field(default=30)  # seconds
    retry_count: int = field(default=3)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.wxtech_api_key = os.getenv("WXTECH_API_KEY", self.wxtech_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        self.api_timeout = int(os.getenv("API_TIMEOUT", str(self.api_timeout)))


@dataclass
class WeatherConfig:
    """天気予報関連の設定"""
    forecast_hours_ahead: int = field(default=12)
    forecast_days: int = field(default=3)
    cache_ttl_seconds: int = field(default=3600)  # 1 hour
    cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))
    
    # 閾値設定
    high_temp_threshold: float = field(default=30.0)
    low_temp_threshold: float = field(default=10.0)
    heavy_rain_threshold: float = field(default=30.0)
    strong_wind_threshold: float = field(default=15.0)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.forecast_hours_ahead = int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", str(self.forecast_hours_ahead)))
        self.forecast_days = int(os.getenv("WEATHER_FORECAST_DAYS", str(self.forecast_days)))
        self.cache_ttl_seconds = int(os.getenv("WEATHER_CACHE_TTL", str(self.cache_ttl_seconds)))
        self.cache_dir = Path(os.getenv("WEATHER_CACHE_DIR", str(self.cache_dir)))


# 天気関連の定数クラス群
@dataclass(frozen=True)
class TemperatureThresholds:
    """気温閾値の定数"""
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


@dataclass(frozen=True)
class HumidityThresholds:
    """湿度閾値の定数"""
    HIGH_HUMIDITY: float = 80.0        # 高湿度の閾値
    LOW_HUMIDITY: float = 30.0         # 低湿度の閾値
    VERY_HIGH_HUMIDITY: float = 90.0   # 非常に高い湿度
    VERY_LOW_HUMIDITY: float = 20.0    # 非常に低い湿度


@dataclass(frozen=True)
class PrecipitationThresholds:
    """降水量閾値の定数"""
    LIGHT_RAIN: float = 1.0            # 小雨の閾値
    MODERATE_RAIN: float = 5.0         # 中雨の閾値
    HEAVY_RAIN: float = 10.0           # 大雨の閾値
    VERY_HEAVY_RAIN: float = 30.0      # 激しい雨の閾値
    THUNDER_STRONG_THRESHOLD: float = 5.0  # 雷雨強弱判定の閾値


@dataclass(frozen=True)
class WindSpeedThresholds:
    """風速閾値の定数"""
    LIGHT_BREEZE: float = 3.0          # 軽い風
    MODERATE_BREEZE: float = 7.0       # 中程度の風
    STRONG_BREEZE: float = 12.0        # 強い風
    GALE: float = 20.0                 # 強風


@dataclass(frozen=True)
class DataValidationRanges:
    """データ検証用の値域"""
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


@dataclass(frozen=True)
class WeatherConstants:
    """天気関連の統合定数"""
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
class Config:
    """統一された設定クラス"""
    api: APIConfig = field(default_factory=APIConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    app: AppSettings = field(default_factory=AppSettings)
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    weather_constants: WeatherConstants = field(default_factory=WeatherConstants)
    system_constants: SystemConstants = field(default_factory=SystemConstants)
    
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
        
        # ディレクトリの作成
        self.app.data_dir.mkdir(parents=True, exist_ok=True)
        self.app.csv_dir.mkdir(parents=True, exist_ok=True)
        self.weather.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        return {
            "api": {
                "wxtech_api_key": "***" if self.api.wxtech_api_key else "",
                "openai_api_key": "***" if self.api.openai_api_key else "",
                "anthropic_api_key": "***" if self.api.anthropic_api_key else "",
                "gemini_api_key": "***" if self.api.gemini_api_key else "",
                "gemini_model": self.api.gemini_model,
                "api_timeout": self.api.api_timeout,
                "retry_count": self.api.retry_count,
            },
            "weather": {
                "forecast_hours_ahead": self.weather.forecast_hours_ahead,
                "forecast_days": self.weather.forecast_days,
                "cache_ttl_seconds": self.weather.cache_ttl_seconds,
                "cache_dir": str(self.weather.cache_dir),
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
            "system_constants": self.system_constants.__dict__
        }


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