"""統合設定モジュール

アプリケーション全体の設定を一元管理します。
設定は論理的なグループに分割され、settings/ディレクトリ内の各モジュールで定義されています。
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any
from functools import lru_cache

from .settings import (
    APIConfig,
    WeatherConfig, WeatherConstants,
    AppSettings, ServerConfig, SystemConstants,
    LLMConfig, LangGraphConfig,
    CommentConfig, SevereWeatherConfig,
    UISettings, GenerationSettings, DataSettings
)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """設定エラー"""
    pass


@dataclass
class Config:
    """統合設定クラス
    
    アプリケーション全体の設定を一元管理するメインクラスです。
    シングルトンパターンで実装され、アプリケーション全体で同一の設定インスタンスを使用します。
    
    Attributes:
        api: API関連の設定
        weather: 天気予報関連の設定
        app: アプリケーション全体の設定
        server: サーバー関連の設定
        llm: LLM関連の設定
        weather_constants: 天気関連の定数
        system_constants: システム定数
        langgraph: LangGraph統合機能の設定
        comment: コメント関連の設定
        severe_weather: 悪天候関連の設定
        ui: UI関連の設定
        generation: コメント生成関連の設定
        data: データ関連の設定
    """
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
        """初期化後の検証処理"""
        # 本番環境での必須設定の検証
        if self.app.env == "production":
            missing_keys = []
            
            # WxTech APIキーは必須
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
        
        # 気温の妥当性チェック
        if not (wc.temperature.COLD_WEATHER <= wc.temperature.COOL_WEATHER <= 
                wc.temperature.WARM_WEATHER <= wc.temperature.HOT_WEATHER):
            raise ConfigurationError(
                "気温閾値が不正です: COLD < COOL < WARM < HOT の関係を保つ必要があります"
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
            raise ConfigurationError("リトライ回数は0-10回の範囲で設定してください")
    
    def _validate_weather_config(self):
        """天気設定の妥当性を検証"""
        # 予報時間の範囲チェック
        if not (1 <= self.weather.forecast_hours <= self.system_constants.MAX_FORECAST_HOURS):
            raise ConfigurationError(
                f"予報時間は1-{self.system_constants.MAX_FORECAST_HOURS}時間の範囲で設定してください"
            )
        
        # キャッシュTTLの範囲チェック
        if not (60 <= self.weather.cache_ttl_seconds <= 86400):  # 1分～1日
            raise ConfigurationError("キャッシュTTLは60-86400秒の範囲で設定してください")
    
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
        if self.app.debug:
            logger.info("デバッグモードが有効です。本番環境では無効にしてください。")
    
    
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
    


# シングルトンパターンで設定インスタンスを管理
@lru_cache(maxsize=1)
def get_config() -> Config:
    """設定インスタンスを取得"""
    return Config()


# 互換性のためのヘルパー関数（app_config.pyで使用されている）
def get_api_config() -> APIConfig:
    """API設定を取得"""
    return get_config().api


def get_weather_config() -> WeatherConfig:
    """天気設定を取得"""
    return get_config().weather


def get_app_settings() -> AppSettings:
    """アプリケーション設定を取得"""
    return get_config().app


def get_ui_settings() -> UISettings:
    """UI設定を取得"""
    return get_config().ui


def get_generation_settings() -> GenerationSettings:
    """生成設定を取得"""
    return get_config().generation


def get_data_settings() -> DataSettings:
    """データ設定を取得"""
    return get_config().data


def get_comment_config() -> CommentConfig:
    """コメント設定を取得"""
    return get_config().comment


def get_severe_weather_config() -> SevereWeatherConfig:
    """悪天候設定を取得"""
    return get_config().severe_weather


def get_system_constants() -> SystemConstants:
    """システム定数を取得"""
    return get_config().system_constants


def get_weather_constants() -> WeatherConstants:
    """天気関連の定数を取得"""
    return get_config().weather_constants


def get_langgraph_config() -> LangGraphConfig:
    """LangGraph設定を取得"""
    return get_config().langgraph


def get_server_config() -> ServerConfig:
    """サーバー設定を取得"""
    return get_config().server


def get_llm_config() -> LLMConfig:
    """LLM設定を取得"""
    return get_config().llm


