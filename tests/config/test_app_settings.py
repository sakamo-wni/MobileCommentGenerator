"""app_settings.pyのテスト"""

import os
import pytest
from unittest import mock

from src.config.app_settings import (
    AppConfig, 
    get_config, 
    reload_config, 
    validate_config,
    setup_environment_defaults
)


class TestAppConfig:
    """AppConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}, clear=True):
            config = AppConfig()
            
            assert config.debug_mode is False
            assert config.log_level == "INFO"
            assert config.weather is not None
            assert config.langgraph is not None
    
    def test_environment_variable_loading(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "WXTECH_API_KEY": "test_key",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }
        
        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig()
            
            assert config.debug_mode is True
            assert config.log_level == "DEBUG"
    
    def test_to_dict_method(self):
        """to_dict()メソッドのテスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config_dict = config.to_dict()
            
            assert "weather" in config_dict
            assert "langgraph" in config_dict
            assert "debug_mode" in config_dict
            assert "log_level" in config_dict
            
            # ネストされた設定も辞書形式になっていることを確認
            assert isinstance(config_dict["weather"], dict)
            assert isinstance(config_dict["langgraph"], dict)


class TestGetConfig:
    """get_config()関数のテスト"""
    
    def test_singleton_behavior(self):
        """シングルトンとして動作することのテスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            # グローバル変数をリセット
            import src.config.app_settings
            src.config.app_settings._config = None
            src.config.app_settings._env_loaded = False
            
            config1 = get_config()
            config2 = get_config()
            
            assert config1 is config2
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # 無効な設定でエラーハンドリングをテスト
        with mock.patch('src.config.app_settings.AppConfig') as mock_config:
            mock_config.side_effect = Exception("Test error")
            
            # グローバル変数をリセット
            import src.config.app_settings
            src.config.app_settings._config = None
            src.config.app_settings._env_loaded = False
            
            with pytest.raises(RuntimeError, match="設定の読み込みに失敗しました.*Test error"):
                get_config()


class TestReloadConfig:
    """reload_config()関数のテスト"""
    
    def test_config_reload(self):
        """設定の再読み込みテスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key", "LOG_LEVEL": "INFO"}):
            # グローバル変数をリセット
            import src.config.app_settings
            src.config.app_settings._config = None
            src.config.app_settings._env_loaded = False
            
            config1 = get_config()
            assert config1.log_level == "INFO"
            
            # 環境変数を変更
            with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
                config2 = reload_config()
                assert config2.log_level == "DEBUG"
                assert config1 is not config2


class TestValidateConfig:
    """validate_config()関数のテスト"""
    
    def test_valid_config(self):
        """正常な設定の検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            errors = validate_config(config)
            
            assert len(errors) == 0
    
    def test_missing_api_key(self):
        """APIキーが不足している場合の検証テスト"""
        config = AppConfig()
        config.weather.wxtech_api_key = ""
        
        errors = validate_config(config)
        
        assert "weather" in errors
        assert any("APIキーが設定されていません" in error for error in errors["weather"])
    
    def test_invalid_forecast_hours(self):
        """予報時間が長すぎる場合の検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config.weather.forecast_hours = 200  # 168時間を超える
            
            errors = validate_config(config)
            
            assert "weather" in errors
            assert any("予報時間数が長すぎます" in error for error in errors["weather"])
    
    def test_invalid_api_timeout(self):
        """APIタイムアウトが長すぎる場合の検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config.weather.api_timeout = 400  # 300秒を超える
            
            errors = validate_config(config)
            
            assert "weather" in errors
            assert any("APIタイムアウトが長すぎます" in error for error in errors["weather"])
    
    def test_invalid_confidence_threshold(self):
        """信頼度閾値が無効な場合の検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config.langgraph.min_confidence_threshold = 1.5  # 0-1の範囲外
            
            errors = validate_config(config)
            
            assert "langgraph" in errors
            assert any("信頼度閾値は0.0-1.0の範囲で設定してください" in error for error in errors["langgraph"])
    
    def test_invalid_weather_context_window(self):
        """天気コンテキスト窓が無効な場合の検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config.langgraph.weather_context_window = 0
            
            errors = validate_config(config)
            
            assert "langgraph" in errors
            assert any("天気コンテキスト窓は1以上で設定してください" in error for error in errors["langgraph"])
    
    def test_invalid_log_level(self):
        """無効なログレベルの検証テスト"""
        with mock.patch.dict(os.environ, {"WXTECH_API_KEY": "test_key"}):
            config = AppConfig()
            config.log_level = "INVALID"
            
            errors = validate_config(config)
            
            assert "general" in errors
            assert any("無効なログレベル" in error for error in errors["general"])


class TestSetupEnvironmentDefaults:
    """setup_environment_defaults()関数のテスト"""
    
    def test_default_values_set(self):
        """デフォルト値が設定されることのテスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            setup_environment_defaults()
            
            assert os.getenv("DEFAULT_WEATHER_LOCATION") == "東京"
            assert os.getenv("WEATHER_FORECAST_HOURS") == "24"
            assert os.getenv("LOG_LEVEL") == "INFO"
    
    def test_existing_values_not_overwritten(self):
        """既存の環境変数が上書きされないことのテスト"""
        existing_vars = {
            "DEFAULT_WEATHER_LOCATION": "大阪",
            "LOG_LEVEL": "DEBUG"
        }
        
        with mock.patch.dict(os.environ, existing_vars, clear=True):
            setup_environment_defaults()
            
            assert os.getenv("DEFAULT_WEATHER_LOCATION") == "大阪"
            assert os.getenv("LOG_LEVEL") == "DEBUG"
            # デフォルト値が設定されていない項目は追加される
            assert os.getenv("WEATHER_FORECAST_HOURS") == "24"