"""API設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch
from pathlib import Path

from src.config.settings.api_settings import APIConfig


class TestAPIConfig:
    """APIConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = APIConfig()
            
            # APIキーはデフォルトで空文字列
            assert config.wxtech_api_key == ""
            assert config.openai_api_key == ""
            assert config.anthropic_api_key == ""
            assert config.gemini_api_key == ""
            
            # その他のデフォルト値
            assert config.api_timeout == 30
            assert config.retry_count == 3
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "WXTECH_API_KEY": "test_wxtech",
            "OPENAI_API_KEY": "test_openai",
            "ANTHROPIC_API_KEY": "test_anthropic",
            "GEMINI_API_KEY": "test_gemini",
            "API_TIMEOUT": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            config = APIConfig()
            
            assert config.wxtech_api_key == "test_wxtech"
            assert config.openai_api_key == "test_openai"
            assert config.anthropic_api_key == "test_anthropic"
            assert config.gemini_api_key == "test_gemini"
            assert config.api_timeout == 60
    
    def test_validate_keys(self):
        """APIキー検証テスト"""
        # 一部のキーのみ設定、他はクリア
        env_vars = {
            "WXTECH_API_KEY": "test_wxtech",
            "OPENAI_API_KEY": "test_openai",
            "ANTHROPIC_API_KEY": "",  # 明示的に空に設定
            "GEMINI_API_KEY": ""      # 明示的に空に設定
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = APIConfig()
            validation = config.validate_keys()
            
            assert validation["wxtech"] is True
            assert validation["openai"] is True
            assert validation["anthropic"] is False
            assert validation["gemini"] is False
    
    def test_get_llm_key(self):
        """LLMキー取得テスト"""
        env_vars = {
            "OPENAI_API_KEY": "test_openai",
            "ANTHROPIC_API_KEY": "test_anthropic",
            "GEMINI_API_KEY": "test_gemini"
        }
        
        with patch.dict(os.environ, env_vars):
            config = APIConfig()
            
            assert config.get_llm_key("openai") == "test_openai"
            assert config.get_llm_key("anthropic") == "test_anthropic"
            assert config.get_llm_key("gemini") == "test_gemini"
            assert config.get_llm_key("unknown") == ""  # 空文字列を返す
            
            # 大文字小文字を区別しない
            assert config.get_llm_key("OPENAI") == "test_openai"
    
    def test_mask_sensitive_data(self):
        """mask_sensitive_data()メソッドが機密情報をマスクすることをテスト"""
        env_vars = {
            "WXTECH_API_KEY": "secret_wxtech_key",
            "OPENAI_API_KEY": "secret_openai_key"
        }
        
        with patch.dict(os.environ, env_vars):
            config = APIConfig()
            masked_data = config.mask_sensitive_data()
            
            # APIキーがマスクされていることを確認
            assert masked_data["wxtech_api_key"] == "***"
            assert masked_data["openai_api_key"] == "***"
            
            # 非機密情報はそのまま
            assert masked_data["api_timeout"] == 30
            assert masked_data["retry_count"] == 3

