"""LLM関連設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch

from src.config.settings.llm_settings import LLMConfig, LangGraphConfig


class TestLLMConfig:
    """LLMConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            
            # プロバイダーとモデル設定
            assert config.default_provider == "gemini"
            assert config.openai_model == "gpt-4o-mini"
            assert config.anthropic_model == "claude-3-haiku-20240307"
            assert config.gemini_model == "gemini-1.5-flash"
            
            # パラメータ設定
            assert config.temperature == 0.7
            assert config.max_tokens == 1000
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "DEFAULT_LLM_PROVIDER": "openai",
            "OPENAI_MODEL": "gpt-4",
            "ANTHROPIC_MODEL": "claude-3-opus",
            "GEMINI_MODEL": "gemini-pro",
            "LLM_TEMPERATURE": "0.5",
            "LLM_MAX_TOKENS": "2000"
        }
        
        with patch.dict(os.environ, env_vars):
            config = LLMConfig()
            
            assert config.default_provider == "openai"
            assert config.openai_model == "gpt-4"
            assert config.anthropic_model == "claude-3-opus"
            assert config.gemini_model == "gemini-pro"
            assert config.temperature == 0.5
            assert config.max_tokens == 2000
    
    def test_parameter_validation(self):
        """パラメータ値の範囲チェック"""
        config = LLMConfig()
        
        # temperature は 0.0 から 2.0 の範囲（一般的な範囲）
        assert 0.0 <= config.temperature <= 2.0
        
        # max_tokens は正の値
        assert config.max_tokens > 0
    
    def test_provider_values(self):
        """プロバイダー値のテスト"""
        valid_providers = ["openai", "anthropic", "gemini"]
        
        for provider in valid_providers:
            with patch.dict(os.environ, {"DEFAULT_LLM_PROVIDER": provider}):
                config = LLMConfig()
                assert config.default_provider == provider


class TestLangGraphConfig:
    """LangGraphConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = LangGraphConfig()
            
            assert config.enable_weather_integration is True
            assert config.auto_location_detection is False
            assert config.weather_context_window == 24
            assert config.min_confidence_threshold == 0.7
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "LANGGRAPH_ENABLE_WEATHER_INTEGRATION": "false",
            "LANGGRAPH_AUTO_LOCATION_DETECTION": "true",
            "LANGGRAPH_WEATHER_CONTEXT_WINDOW": "48",
            "LANGGRAPH_MIN_CONFIDENCE_THRESHOLD": "0.8"
        }
        
        with patch.dict(os.environ, env_vars):
            config = LangGraphConfig()
            
            assert config.enable_weather_integration is False
            assert config.auto_location_detection is True
            assert config.weather_context_window == 48
            assert config.min_confidence_threshold == 0.8
    
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
            ("0", False),
            ("yes", False),
            ("no", False)
        ]
        
        for value, expected in test_cases:
            with patch.dict(os.environ, {"LANGGRAPH_ENABLE_WEATHER_INTEGRATION": value}):
                config = LangGraphConfig()
                assert config.enable_weather_integration is expected
    
    def test_numeric_validation(self):
        """数値パラメータの検証テスト"""
        config = LangGraphConfig()
        
        # weather_context_window は正の値
        assert config.weather_context_window > 0
        
        # min_confidence_threshold は 0.0 から 1.0 の範囲
        assert 0.0 <= config.min_confidence_threshold <= 1.0