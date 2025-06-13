"""
天気予報統合機能の設定管理

環境変数やデフォルト設定を管理する
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv


@dataclass
class WeatherConfig:
    """天気予報機能の設定クラス

    Attributes:
        wxtech_api_key: WxTech API キー
        default_location: デフォルト地点名
        forecast_hours: デフォルト予報時間数
        forecast_hours_ahead: 何時間後の予報を取得するか（デフォルト12時間）
        api_timeout: API タイムアウト（秒）
        max_retries: 最大リトライ回数
        rate_limit_delay: レート制限回避遅延（秒）
        cache_ttl: キャッシュTTL（秒）
        enable_caching: キャッシュ有効化フラグ
        forecast_cache_retention_days: 予報キャッシュ保持日数
        temp_diff_threshold_previous_day: 前日との有意な温度差閾値（℃）
        temp_diff_threshold_12hours: 12時間前との有意な温度差閾値（℃）
        daily_temp_range_threshold_large: 大きな日較差閾値（℃）
        daily_temp_range_threshold_medium: 中程度の日較差閾値（℃）
    """

    wxtech_api_key: str = field(default="")
    default_location: str = field(default="東京")
    forecast_hours: int = field(default=24)
    forecast_hours_ahead: int = field(default=12)
    api_timeout: int = field(default=30)
    max_retries: int = field(default=3)
    rate_limit_delay: float = field(default=0.1)
    cache_ttl: int = field(default=300)  # 5分
    enable_caching: bool = field(default=True)
    
    # 予報キャッシュ設定
    forecast_cache_retention_days: int = field(default=7)
    
    # 温度差閾値設定（気象学的根拠に基づく）
    temp_diff_threshold_previous_day: float = field(default=5.0)  # 前日比5℃: 人体が明確に体感できる温度差
    temp_diff_threshold_12hours: float = field(default=3.0)  # 12時間前比3℃: 体調管理に影響する可能性がある基準値
    daily_temp_range_threshold_large: float = field(default=15.0)  # 日較差15℃: 健康影響リスクが高まる閾値
    daily_temp_range_threshold_medium: float = field(default=10.0)  # 日較差10℃: 注意が必要な閾値
    
    # 温度分類の閾値（気象庁の基準に基づく）
    temp_threshold_hot: float = field(default=30.0)  # 真夏日の基準
    temp_threshold_warm: float = field(default=25.0)  # 夏日の基準
    temp_threshold_cool: float = field(default=10.0)  # 肌寒く感じる温度
    temp_threshold_cold: float = field(default=5.0)  # 冬日に近い温度

    def __post_init__(self):
        """環境変数からの読み込みと設定の検証"""
        # 環境変数から設定を読み込む
        self.wxtech_api_key = os.getenv("WXTECH_API_KEY", self.wxtech_api_key)
        self.default_location = os.getenv("DEFAULT_WEATHER_LOCATION", self.default_location)
        self.forecast_hours = int(os.getenv("WEATHER_FORECAST_HOURS", str(self.forecast_hours)))
        self.forecast_hours_ahead = int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", str(self.forecast_hours_ahead)))
        self.api_timeout = int(os.getenv("WEATHER_API_TIMEOUT", str(self.api_timeout)))
        self.max_retries = int(os.getenv("WEATHER_API_MAX_RETRIES", str(self.max_retries)))
        self.rate_limit_delay = float(os.getenv("WEATHER_API_RATE_LIMIT_DELAY", str(self.rate_limit_delay)))
        self.cache_ttl = int(os.getenv("WEATHER_CACHE_TTL", str(self.cache_ttl)))
        self.enable_caching = os.getenv("WEATHER_ENABLE_CACHING", "true" if self.enable_caching else "false").lower() == "true"
        
        # 予報キャッシュ設定
        self.forecast_cache_retention_days = int(os.getenv("FORECAST_CACHE_RETENTION_DAYS", str(self.forecast_cache_retention_days)))
        
        # 温度差閾値設定
        self.temp_diff_threshold_previous_day = float(os.getenv("TEMP_DIFF_THRESHOLD_PREVIOUS_DAY", str(self.temp_diff_threshold_previous_day)))
        self.temp_diff_threshold_12hours = float(os.getenv("TEMP_DIFF_THRESHOLD_12HOURS", str(self.temp_diff_threshold_12hours)))
        self.daily_temp_range_threshold_large = float(os.getenv("DAILY_TEMP_RANGE_THRESHOLD_LARGE", str(self.daily_temp_range_threshold_large)))
        self.daily_temp_range_threshold_medium = float(os.getenv("DAILY_TEMP_RANGE_THRESHOLD_MEDIUM", str(self.daily_temp_range_threshold_medium)))
        
        # 温度分類の閾値
        self.temp_threshold_hot = float(os.getenv("TEMP_THRESHOLD_HOT", str(self.temp_threshold_hot)))
        self.temp_threshold_warm = float(os.getenv("TEMP_THRESHOLD_WARM", str(self.temp_threshold_warm)))
        self.temp_threshold_cool = float(os.getenv("TEMP_THRESHOLD_COOL", str(self.temp_threshold_cool)))
        self.temp_threshold_cold = float(os.getenv("TEMP_THRESHOLD_COLD", str(self.temp_threshold_cold)))
        
        # 検証
        if not self.wxtech_api_key:
            raise ValueError("WXTECH_API_KEY環境変数が設定されていません")

        if self.forecast_hours <= 0:
            raise ValueError("forecast_hoursは1以上である必要があります")

        if self.api_timeout <= 0:
            raise ValueError("api_timeoutは1以上である必要があります")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（ログ出力用、APIキーはマスク）

        Returns:
            設定情報の辞書
        """
        return {
            "wxtech_api_key": "***" if self.wxtech_api_key else "",
            "default_location": self.default_location,
            "forecast_hours": self.forecast_hours,
            "forecast_hours_ahead": self.forecast_hours_ahead,
            "api_timeout": self.api_timeout,
            "max_retries": self.max_retries,
            "rate_limit_delay": self.rate_limit_delay,
            "cache_ttl": self.cache_ttl,
            "enable_caching": self.enable_caching,
            "forecast_cache_retention_days": self.forecast_cache_retention_days,
            "temp_diff_threshold_previous_day": self.temp_diff_threshold_previous_day,
            "temp_diff_threshold_12hours": self.temp_diff_threshold_12hours,
            "daily_temp_range_threshold_large": self.daily_temp_range_threshold_large,
            "daily_temp_range_threshold_medium": self.daily_temp_range_threshold_medium,
        }


@dataclass
class LangGraphConfig:
    """LangGraph統合機能の設定クラス

    Attributes:
        enable_weather_integration: 天気統合の有効化
        auto_location_detection: 自動地点検出の有効化
        weather_context_window: 天気情報のコンテキスト窓
        min_confidence_threshold: 最小信頼度閾値
    """

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

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "enable_weather_integration": self.enable_weather_integration,
            "auto_location_detection": self.auto_location_detection,
            "weather_context_window": self.weather_context_window,
            "min_confidence_threshold": self.min_confidence_threshold,
        }


@dataclass
class AppConfig:
    """アプリケーション全体の設定クラス

    Attributes:
        weather: 天気予報設定
        langgraph: LangGraph設定
        debug_mode: デバッグモード
        log_level: ログレベル
    """

    weather: WeatherConfig = field(default_factory=WeatherConfig)
    langgraph: LangGraphConfig = field(default_factory=LangGraphConfig)
    debug_mode: bool = field(default=False)
    log_level: str = field(default="INFO")
    
    def __post_init__(self):
        """環境変数から設定を読み込む"""
        self.debug_mode = os.getenv("DEBUG", "true" if self.debug_mode else "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "weather": self.weather.to_dict(),
            "langgraph": self.langgraph.to_dict(),
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
        }


# グローバル設定インスタンス
_config = None
_env_loaded = False


def get_config() -> AppConfig:
    """グローバル設定インスタンスを取得

    Returns:
        アプリケーション設定
    """
    global _config, _env_loaded
    if not _env_loaded:
        load_dotenv()
        _env_loaded = True
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """設定を再読み込み

    Returns:
        新しいアプリケーション設定
    """
    global _config, _env_loaded
    load_dotenv(override=True)  # 環境変数を強制再読み込み
    _env_loaded = True
    _config = AppConfig()
    return _config


# 設定検証関数
def validate_config(config: AppConfig) -> Dict[str, list]:
    """設定の妥当性を検証

    Args:
        config: 検証するアプリケーション設定

    Returns:
        検証エラーの辞書 {'category': [error_messages]}
    """
    errors = {"weather": [], "langgraph": [], "general": []}

    # 天気設定の検証
    try:
        if not config.weather.wxtech_api_key:
            errors["weather"].append("WxTech APIキーが設定されていません")

        if config.weather.forecast_hours > 168:  # 7日 = 168時間
            errors["weather"].append("予報時間数が長すぎます（最大168時間）")

        if config.weather.api_timeout > 300:  # 5分
            errors["weather"].append("APIタイムアウトが長すぎます（最大300秒）")

    except Exception as e:
        errors["weather"].append(f"天気設定エラー: {str(e)}")

    # LangGraph設定の検証
    try:
        if not 0 <= config.langgraph.min_confidence_threshold <= 1:
            errors["langgraph"].append("信頼度閾値は0.0-1.0の範囲で設定してください")

        if config.langgraph.weather_context_window <= 0:
            errors["langgraph"].append("天気コンテキスト窓は1以上で設定してください")

    except Exception as e:
        errors["langgraph"].append(f"LangGraph設定エラー: {str(e)}")

    # 一般設定の検証
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.log_level not in valid_log_levels:
        errors["general"].append(f"無効なログレベル: {config.log_level}")

    return {k: v for k, v in errors.items() if v}  # エラーがあるカテゴリのみ返す


# 環境変数のデフォルト値を設定する関数
def setup_environment_defaults():
    """環境変数のデフォルト値を設定

    開発環境やテスト環境で使用
    """
    defaults = {
        "DEFAULT_WEATHER_LOCATION": "東京",
        "WEATHER_FORECAST_HOURS": "24",
        "WEATHER_FORECAST_HOURS_AHEAD": "12",
        "WEATHER_API_TIMEOUT": "30",
        "WEATHER_API_MAX_RETRIES": "3",
        "WEATHER_API_RATE_LIMIT_DELAY": "0.1",
        "WEATHER_CACHE_TTL": "300",
        "WEATHER_ENABLE_CACHING": "true",
        "FORECAST_CACHE_RETENTION_DAYS": "7",
        "TEMP_DIFF_THRESHOLD_PREVIOUS_DAY": "5.0",
        "TEMP_DIFF_THRESHOLD_12HOURS": "3.0",
        "DAILY_TEMP_RANGE_THRESHOLD_LARGE": "15.0",
        "DAILY_TEMP_RANGE_THRESHOLD_MEDIUM": "10.0",
        "LANGGRAPH_ENABLE_WEATHER": "true",
        "LANGGRAPH_AUTO_LOCATION": "false",
        "LANGGRAPH_WEATHER_CONTEXT_WINDOW": "24",
        "LANGGRAPH_MIN_CONFIDENCE": "0.7",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
    }

    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value


if __name__ == "__main__":
    # 設定テスト
    try:
        setup_environment_defaults()
        config = get_config()
        print("設定読み込み成功:")
        print(config.to_dict())

        # 設定検証
        validation_errors = validate_config(config)
        if validation_errors:
            print("\n設定検証エラー:")
            for category, errors in validation_errors.items():
                print(f"{category}:")
                for error in errors:
                    print(f"  - {error}")
        else:
            print("\n設定検証: 問題なし")

    except Exception as e:
        print(f"設定エラー: {str(e)}")
