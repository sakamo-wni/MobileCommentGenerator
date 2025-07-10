"""統一設定システムのテスト"""

import os
import pytest
from unittest import mock
from pathlib import Path

from src.config.unified_config import (
    UnifiedConfig,
    APIConfig,
    AppConfig,
    WeatherConfig,
    ServerConfig,
    get_unified_config,
    get_api_config,
    get_weather_config,
    get_app_config,
    get_server_config,
    config
)
from src.config.config import reset_config


class TestAPIConfig:
    """APIConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            api_config = APIConfig()
            
            assert api_config.wxtech_api_key == ""
            assert api_config.openai_api_key == ""
            assert api_config.gemini_api_key == ""
            assert api_config.anthropic_api_key == ""
            assert api_config.gemini_model == "gemini-1.5-flash"
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "OPENAI_API_KEY": "test_openai_key",
            "GEMINI_API_KEY": "test_gemini_key",
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "WXTECH_API_KEY": "test_wxtech_key",
            "GEMINI_MODEL": "gemini-1.5-pro"
        }
        
        with mock.patch.dict(os.environ, env_vars, clear=True):
            api_config = APIConfig()
            
            assert api_config.openai_api_key == "test_openai_key"
            assert api_config.gemini_api_key == "test_gemini_key"
            assert api_config.anthropic_api_key == "test_anthropic_key"
            assert api_config.wxtech_api_key == "test_wxtech_key"
            assert api_config.gemini_model == "gemini-1.5-pro"


class TestWeatherConfig:
    """WeatherConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            weather_config = WeatherConfig()
            
            assert weather_config.forecast_hours_ahead == 12
            assert weather_config.forecast_days == 3
            assert weather_config.cache_ttl_seconds == 3600
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "WEATHER_FORECAST_HOURS_AHEAD": "24"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            weather_config = WeatherConfig()
            
            assert weather_config.forecast_hours_ahead == 24


class TestAppConfig:
    """AppConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            app_config = AppConfig()
            
            assert app_config.env == "development"
            assert app_config.log_level == "INFO"
            assert app_config.data_dir == Path("output")
            assert app_config.cache_dir == Path("data/forecast_cache")
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "APP_ENV": "production",
            "LOG_LEVEL": "DEBUG"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            app_config = AppConfig()
            
            assert app_config.env == "production"
            assert app_config.log_level == "DEBUG"


class TestServerConfig:
    """ServerConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with mock.patch.dict(os.environ, {}, clear=True):
            server_config = ServerConfig()
            
            assert server_config.api_port == 8000
            assert server_config.frontend_port == 3000
            assert "http://localhost:3000" in server_config.cors_origins
            assert "http://localhost:5173" in server_config.cors_origins
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "API_PORT": "9000",
            "FRONTEND_PORT": "4000",
            "CORS_ORIGINS": "http://example.com,http://test.com"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            server_config = ServerConfig()
            
            assert server_config.api_port == 9000
            assert server_config.frontend_port == 4000
            assert server_config.cors_origins == ["http://example.com", "http://test.com"]


class TestUnifiedConfig:
    """UnifiedConfigクラスのテスト"""
    
    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        config1 = UnifiedConfig()
        config2 = UnifiedConfig()
        
        assert config1 is config2
    
    def test_initialization(self):
        """初期化のテスト"""
        unified_config = UnifiedConfig()
        
        assert hasattr(unified_config, 'api')
        assert hasattr(unified_config, 'weather')
        assert hasattr(unified_config, 'app')
        assert hasattr(unified_config, 'server')
        assert isinstance(unified_config.api, APIConfig)
        assert isinstance(unified_config.weather, WeatherConfig)
        assert isinstance(unified_config.app, AppConfig)
        assert isinstance(unified_config.server, ServerConfig)
    
    def test_get_api_key(self):
        """APIキー取得のテスト"""
        env_vars = {
            "OPENAI_API_KEY": "test_openai",
            "GEMINI_API_KEY": "test_gemini",
            "ANTHROPIC_API_KEY": "test_anthropic",
            "WXTECH_API_KEY": "test_wxtech"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            # 新しいインスタンスを作成するため、一度リセット
            UnifiedConfig._instance = None
            unified_config = UnifiedConfig()
            
            assert unified_config.get_api_key("openai") == "test_openai"
            assert unified_config.get_api_key("gemini") == "test_gemini"
            assert unified_config.get_api_key("anthropic") == "test_anthropic"
            assert unified_config.get_api_key("wxtech") == "test_wxtech"
            assert unified_config.get_api_key("unknown") is None
    
    def test_is_production(self):
        """本番環境判定のテスト"""
        # 開発環境
        with mock.patch.dict(os.environ, {"APP_ENV": "development"}):
            reset_config()
            UnifiedConfig._instance = None
            unified_config = UnifiedConfig()
            assert unified_config.is_production() is False
        
        # 本番環境
        with mock.patch.dict(os.environ, {"APP_ENV": "production"}):
            reset_config()
            UnifiedConfig._instance = None
            unified_config = UnifiedConfig()
            assert unified_config.is_production() is True
    
    def test_get_cors_origins(self):
        """CORS origins取得のテスト"""
        # 開発環境
        with mock.patch.dict(os.environ, {"APP_ENV": "development"}):
            reset_config()
            UnifiedConfig._instance = None
            unified_config = UnifiedConfig()
            origins = unified_config.get_cors_origins()
            assert "http://localhost:3000" in origins
        
        # 本番環境
        with mock.patch.dict(os.environ, {
            "APP_ENV": "production",
            "CORS_ORIGINS_PROD": "https://prod1.com,https://prod2.com"
        }):
            reset_config()
            UnifiedConfig._instance = None
            unified_config = UnifiedConfig()
            origins = unified_config.get_cors_origins()
            assert origins == ["https://prod1.com", "https://prod2.com"]
    
    def test_yaml_config_loading(self):
        """YAML設定読み込みのテスト"""
        unified_config = UnifiedConfig()
        
        # キャッシュが初期化されていることを確認
        assert hasattr(unified_config, '_config_cache')
        assert isinstance(unified_config._config_cache, dict)
        
        # 存在しない設定を取得した場合は空の辞書が返る
        non_existent = unified_config.get_yaml_config("non_existent")
        assert non_existent == {}


class TestConvenienceFunctions:
    """便利関数のテスト"""
    
    def test_get_unified_config(self):
        """get_unified_config関数のテスト"""
        unified = get_unified_config()
        assert isinstance(unified, UnifiedConfig)
        assert unified is config  # グローバルインスタンスと同じ
    
    def test_get_api_config(self):
        """get_api_config関数のテスト"""
        api = get_api_config()
        assert isinstance(api, APIConfig)
        assert api is config.api
    
    def test_get_weather_config(self):
        """get_weather_config関数のテスト"""
        weather = get_weather_config()
        assert isinstance(weather, WeatherConfig)
        assert weather is config.weather
    
    def test_get_app_config(self):
        """get_app_config関数のテスト"""
        app = get_app_config()
        assert isinstance(app, AppConfig)
        assert app is config.app
    
    def test_get_server_config(self):
        """get_server_config関数のテスト"""
        server = get_server_config()
        assert isinstance(server, ServerConfig)
        assert server is config.server