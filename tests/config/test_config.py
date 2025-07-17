"""統一設定システムのテスト"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.config.config import Config, get_config, reset_config
from src.exceptions import ConfigError as ConfigurationError


class TestConfig:
    """Configクラスのテスト"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """テスト用の環境変数をモック"""
        env_vars = {
            "APP_ENV": "test",
            "DEBUG": "true",
            "WXTECH_API_KEY": "test_wxtech_key",
            "OPENAI_API_KEY": "test_openai_key",
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "GEMINI_API_KEY": "test_gemini_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_KEY": "test_azure_key",
            "AZURE_API_VERSION": "2024-02-01",
            "WEATHER_CACHE_TTL": "120",
            "REQUEST_TIMEOUT": "60",
            "WEATHER_CACHE_DIR": "/tmp/test_cache",
            "LOG_LEVEL": "DEBUG"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            yield env_vars
    
    def test_config_initialization(self, mock_env_vars):
        """設定の初期化テスト"""
        config = Config()
        
        # AppConfig
        assert config.app.env == "test"
        assert config.app.debug is True
        assert config.app.log_level == "DEBUG"
        
        # APIConfig
        assert config.api.wxtech_api_key == "test_wxtech_key"
        assert config.api.openai_api_key == "test_openai_key"
        assert config.api.anthropic_api_key == "test_anthropic_key"
        assert config.api.gemini_api_key == "test_gemini_key"
        
        # WeatherConfig
        assert config.weather.cache_ttl_seconds == 120
        assert config.weather.cache_dir == Path("/tmp/test_cache")
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            # デフォルト値の確認
            assert config.app.env == "development"
            assert config.app.debug is False
            assert config.weather.cache_ttl_seconds == 3600  # デフォルト値
            assert config.api.api_timeout == 30
            assert config.app.log_level == "INFO"
    
    def test_production_validation_success(self):
        """本番環境での検証成功テスト"""
        env_vars = {
            "APP_ENV": "production",
            "WXTECH_API_KEY": "prod_wxtech_key",
            "OPENAI_API_KEY": "prod_openai_key"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # エラーが発生しないことを確認
            config = Config()
            assert config.app.env == "production"
    
    def test_production_validation_missing_wxtech_key(self):
        """本番環境でWxTech APIキーが欠落している場合"""
        env_vars = {
            "APP_ENV": "production",
            "OPENAI_API_KEY": "prod_openai_key"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config()
            assert "WXTECH_API_KEY" in str(exc_info.value)
    
    def test_production_validation_missing_llm_key(self):
        """本番環境でLLM APIキーが欠落している場合"""
        env_vars = {
            "APP_ENV": "production",
            "WXTECH_API_KEY": "prod_wxtech_key"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config()
            assert "OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY" in str(exc_info.value)
    
    def test_production_validation_multiple_missing_keys(self):
        """本番環境で複数のキーが欠落している場合"""
        env_vars = {
            "APP_ENV": "production"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config()
            error_message = str(exc_info.value)
            assert "WXTECH_API_KEY" in error_message
            assert "OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY" in error_message
    
    def test_development_validation_allows_missing_keys(self):
        """開発環境では必須キーがなくてもエラーにならない"""
        env_vars = {
            "APP_ENV": "development"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # エラーが発生しないことを確認
            config = Config()
            assert config.app.env == "development"
            assert config.api.wxtech_api_key == ""  # 空文字列がデフォルト
    
    def test_singleton_pattern(self, mock_env_vars):
        """シングルトンパターンのテスト"""
        config1 = get_config()
        config2 = get_config()
        
        # 同じインスタンスであることを確認
        assert config1 is config2
        
        # 値が同じであることを確認
        assert config1.api.wxtech_api_key == config2.api.wxtech_api_key
    
    def test_to_dict_method(self, mock_env_vars):
        """to_dict()メソッドのテスト"""
        config = Config()
        config_dict = config.to_dict()
        
        # 辞書形式であることを確認
        assert isinstance(config_dict, dict)
        
        # 主要な設定が含まれていることを確認
        assert "app" in config_dict
        assert "api" in config_dict
        assert "weather" in config_dict
        # loggin設定はapp内にlog_levelとして存在
        assert "log_level" in config_dict["app"]
        
        # 値が正しいことを確認
        assert config_dict["app"]["env"] == "test"
        # APIキーはマスクされる
        assert config_dict["api"]["wxtech_api_key"] == "***"
    
    def test_directory_creation(self, tmp_path):
        """ディレクトリ作成のテスト"""
        env_vars = {
            "DATA_DIR": str(tmp_path / "data"),
            "CSV_DIR": str(tmp_path / "csv"),
            "CACHE_DIR": str(tmp_path / "cache"),
            "LOG_DIR": str(tmp_path / "logs")
        }
        with patch.dict(os.environ, env_vars):
            config = Config()
            
            # ディレクトリが作成されていることを確認
            assert config.app.data_dir.exists()
            assert config.app.csv_dir.exists()
            assert config.weather.cache_dir.exists()
    
    def test_boolean_parsing(self):
        """ブール値の解析テスト"""
        test_cases = [
            ("true", True),
            ("True", True),   # lower()されるので"true"になる
            ("TRUE", True),   # lower()されるので"true"になる
            ("1", False),     # "true"のみがTrue
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("", False),
            ("anything_else", False)
        ]
        
        for value, expected in test_cases:
            with patch.dict(os.environ, {"DEBUG": value}):
                # シングルトンをクリア
                reset_config()
                config = Config()
                assert config.app.debug is expected, f"Failed for value '{value}', expected {expected} but got {config.app.debug}"
    
    def test_integer_parsing(self):
        """整数値の解析テスト"""
        with patch.dict(os.environ, {"WEATHER_CACHE_TTL": "300"}):
            reset_config()
            config = Config()
            assert config.weather.cache_ttl_seconds == 300
        
        # 不正な値の場合はエラーが発生するかデフォルト値を使用
        with patch.dict(os.environ, {"WEATHER_CACHE_TTL": "invalid"}):
            reset_config()
            try:
                config = Config()
                # int()変換でエラーが発生する場合
            except ValueError:
                pass
    
    def test_environment_specific_values(self):
        """環境別の設定テスト"""
        # 開発環境
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            reset_config()
            config = Config()
            assert config.app.env == "development"
        
        # テスト環境
        with patch.dict(os.environ, {"APP_ENV": "test"}):
            reset_config()
            config = Config()
            assert config.app.env == "test"
        
        # 本番環境（必須キーも設定）
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "WXTECH_API_KEY": "prod_key",
            "OPENAI_API_KEY": "prod_openai"
        }):
            reset_config()
            config = Config()
            assert config.app.env == "production"