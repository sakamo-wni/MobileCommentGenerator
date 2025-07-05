"""
天気予報機能の設定管理

天気関連の設定を管理する
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


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
    forecast_hours_ahead: int = field(default=0)  # 現在時刻から予報を取得
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
            "wxtech_api_key": f"{self.wxtech_api_key[:8]}...{self.wxtech_api_key[-4:]}" if len(self.wxtech_api_key) > 12 else "***",
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
            "temp_threshold_hot": self.temp_threshold_hot,
            "temp_threshold_warm": self.temp_threshold_warm,
            "temp_threshold_cool": self.temp_threshold_cool,
            "temp_threshold_cold": self.temp_threshold_cold,
        }