"""UIおよびデータ関連設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch
from pathlib import Path

from src.config.settings.ui_data_settings import UISettings, GenerationSettings, DataSettings


class TestUISettings:
    """UISettingsクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            settings = UISettings()
            
            # 基本設定
            assert settings.page_title == "天気コメント生成システム"
            assert settings.page_icon == "☀️"
            assert settings.layout == "wide"
            assert settings.sidebar_state == "expanded"
            assert settings.theme == "light"
            
            # コンポーネント設定
            assert settings.max_locations_per_generation == 30
            assert settings.default_llm_provider == "gemini"
            assert settings.show_debug_info is False
            
            # 表示設定
            assert settings.date_format == "%Y年%m月%d日 %H時%M分"
            assert settings.timezone == "Asia/Tokyo"
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "MAX_LOCATIONS_PER_GENERATION": "50",
            "DEFAULT_LLM_PROVIDER": "openai"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = UISettings()
            
            assert settings.max_locations_per_generation == 50
            assert settings.default_llm_provider == "openai"
    
    def test_theme_values(self):
        """テーマ値のテスト"""
        settings = UISettings()
        assert settings.theme in ["light", "dark"]
    
    def test_layout_values(self):
        """レイアウト値のテスト"""
        settings = UISettings()
        assert settings.layout in ["wide", "centered"]


class TestGenerationSettings:
    """GenerationSettingsクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            settings = GenerationSettings()
            
            assert settings.timeout == 60000  # ミリ秒
            assert settings.max_retries == 3
            assert settings.batch_size == 10
            assert settings.concurrent_requests == 5
            assert settings.cache_enabled is True
            assert settings.cache_ttl_hours == 24
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "GENERATION_TIMEOUT": "120000",
            "GENERATION_MAX_RETRIES": "5",
            "GENERATION_BATCH_SIZE": "20",
            "GENERATION_CACHE_ENABLED": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = GenerationSettings()
            
            assert settings.timeout == 120000
            assert settings.max_retries == 5
            assert settings.batch_size == 20
            assert settings.cache_enabled is False
    
    def test_numeric_validation(self):
        """数値パラメータの検証テスト"""
        settings = GenerationSettings()
        
        # タイムアウトは正の値
        assert settings.timeout > 0
        
        # リトライ回数は非負の値
        assert settings.max_retries >= 0
        
        # バッチサイズは正の値
        assert settings.batch_size > 0
        
        # 同時実行数は正の値
        assert settings.concurrent_requests > 0
    
    def test_boolean_parsing(self):
        """ブール値の解析テスト"""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("1", False),  # "true"以外はFalse
            ("0", False)
        ]
        
        for value, expected in test_cases:
            with patch.dict(os.environ, {"GENERATION_CACHE_ENABLED": value}):
                settings = GenerationSettings()
                assert settings.cache_enabled is expected


class TestDataSettings:
    """DataSettingsクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            settings = DataSettings()
            
            # ディレクトリ設定
            assert settings.data_dir == Path("data")
            assert settings.forecast_cache_dir == Path("data/forecast_cache")
            assert settings.generation_history_file == Path("data/generation_history.json")
            assert settings.locations_file == Path("data/locations.json")
            assert settings.csv_output_dir == Path("output")
            
            # CSV関連設定
            assert settings.use_local_csv is True
            assert settings.csv_encoding == "utf-8"
            assert settings.csv_delimiter == ","
            
            # 履歴管理
            assert settings.max_history_records == 1000
            assert settings.history_retention_days == 30
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "DATA_DIR": "/tmp/data",
            "FORECAST_CACHE_DIR": "/tmp/forecast",
            "CSV_OUTPUT_DIR": "/tmp/output",
            "USE_LOCAL_CSV": "false",
            "MAX_HISTORY_RECORDS": "2000",
            "HISTORY_RETENTION_DAYS": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = DataSettings()
            
            assert settings.data_dir == Path("/tmp/data")
            assert settings.forecast_cache_dir == Path("/tmp/forecast")
            assert settings.csv_output_dir == Path("/tmp/output")
            assert settings.use_local_csv is False
            assert settings.max_history_records == 2000
            assert settings.history_retention_days == 60
    
    def test_path_type_handling(self):
        """パス型の処理テスト"""
        settings = DataSettings()
        
        # すべてのパス設定がPath型であることを確認
        assert isinstance(settings.data_dir, Path)
        assert isinstance(settings.forecast_cache_dir, Path)
        assert isinstance(settings.generation_history_file, Path)
        assert isinstance(settings.locations_file, Path)
        assert isinstance(settings.csv_output_dir, Path)
    
    def test_csv_settings(self):
        """CSV設定のテスト"""
        settings = DataSettings()
        
        # エンコーディングが有効な値であることを確認
        assert settings.csv_encoding in ["utf-8", "shift_jis", "cp932", "utf-8-sig"]
        
        # デリミタが有効な値であることを確認
        assert settings.csv_delimiter in [",", "\t", ";", "|"]
    
    def test_history_settings_validation(self):
        """履歴設定の検証テスト"""
        settings = DataSettings()
        
        # 最大履歴レコード数は正の値
        assert settings.max_history_records > 0
        
        # 履歴保持日数は正の値
        assert settings.history_retention_days > 0