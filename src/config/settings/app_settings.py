"""アプリケーション全体の設定モジュール"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.shared", override=False)


@dataclass
class AppSettings:
    """アプリケーション全体の設定
    
    環境、ログレベル、ディレクトリパスなどの基本設定を管理します。
    環境変数からの設定オーバーライドをサポートします。
    """
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
        
        # ディレクトリ作成は行わない - Config.ensure_directories()で必要時に作成


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
        # 本番環境用の特殊処理（後方互換性）
        app_env = os.getenv("APP_ENV", "development")
        if app_env == "production":
            cors_env = os.getenv("CORS_ORIGINS_PROD", "")
        else:
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