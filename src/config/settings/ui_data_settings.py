"""UI・データ関連の設定モジュール"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.shared", override=False)


@dataclass
class UISettings:
    """UI関連の設定
    
    Streamlit UIの表示設定を管理します。
    ページタイトル、レイアウト、テーマ、日付フォーマットなどをカスタマイズできます。
    """
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
        max_locations = os.getenv("MAX_LOCATIONS_PER_GENERATION")
        if max_locations:
            self.max_locations_per_generation = int(max_locations)
        
        llm_provider = os.getenv("DEFAULT_LLM_PROVIDER")
        if llm_provider:
            self.default_llm_provider = llm_provider


@dataclass
class GenerationSettings:
    """コメント生成関連の設定
    
    コメント生成の動作パラメータを管理します。
    タイムアウト、リトライ回数、バッチサイズ、同時実行数などを設定できます。
    """
    timeout: int = field(default=60000)  # ミリ秒
    max_retries: int = field(default=3)
    batch_size: int = field(default=10)
    concurrent_requests: int = field(default=5)
    cache_enabled: bool = field(default=True)
    cache_ttl_hours: int = field(default=24)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        timeout = os.getenv("GENERATION_TIMEOUT")
        if timeout:
            self.timeout = int(timeout)
        
        max_retries = os.getenv("GENERATION_MAX_RETRIES")
        if max_retries:
            self.max_retries = int(max_retries)
        
        batch_size = os.getenv("GENERATION_BATCH_SIZE")
        if batch_size:
            self.batch_size = int(batch_size)
        
        cache_enabled = os.getenv("GENERATION_CACHE_ENABLED")
        if cache_enabled is not None:
            self.cache_enabled = cache_enabled.lower() == "true"


@dataclass
class DataSettings:
    """データ関連の設定
    
    データの保存先、CSVファイルの出力設定、履歴管理などを設定します。
    キャッシュディレクトリや最大履歴数などのパラメータも含まれます。
    """
    data_dir: Path = field(default_factory=lambda: Path("data"))
    forecast_cache_dir: Path = field(default_factory=lambda: Path("data/forecast_cache"))
    generation_history_file: Path = field(default_factory=lambda: Path("data/generation_history.json"))
    locations_file: Path = field(default_factory=lambda: Path("data/locations.json"))
    csv_output_dir: Path = field(default_factory=lambda: Path("output"))
    
    # CSV関連設定
    use_local_csv: bool = field(default=True)
    csv_encoding: str = field(default="utf-8")
    csv_delimiter: str = field(default=",")
    
    # 履歴管理
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