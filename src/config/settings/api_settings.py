"""API関連の設定モジュール"""

import os
from dataclasses import dataclass, field
from typing import Any
from dotenv import load_dotenv
from pathlib import Path

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.shared", override=False)


@dataclass
class APIConfig:
    """API関連の設定
    
    各種APIサービスの認証情報と接続設定を管理します。
    環境変数からの読み込みをサポートし、機密情報の安全な管理を提供します。
    """
    # API Keys
    wxtech_api_key: str = field(default="")
    openai_api_key: str = field(default="")
    anthropic_api_key: str = field(default="")
    gemini_api_key: str = field(default="")
    
    # API Settings
    api_timeout: int = field(default=30)  # seconds
    retry_count: int = field(default=3)
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.wxtech_api_key = os.getenv("WXTECH_API_KEY", self.wxtech_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.api_timeout = int(os.getenv("API_TIMEOUT", str(self.api_timeout)))
    
    def get_llm_key(self, provider: str) -> str | None:
        """LLMプロバイダーに対応するAPIキーを取得"""
        provider_map = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "anthropic": self.anthropic_api_key
        }
        return provider_map.get(provider.lower(), "")
    
    def validate_keys(self) -> dict[str, bool]:
        """APIキーの存在を検証"""
        return {
            "openai": bool(self.openai_api_key),
            "gemini": bool(self.gemini_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "wxtech": bool(self.wxtech_api_key)
        }
    
    def mask_sensitive_data(self) -> dict[str, Any]:
        """機密データをマスクした設定を返す"""
        return {
            "wxtech_api_key": "***" if self.wxtech_api_key else "",
            "openai_api_key": "***" if self.openai_api_key else "",
            "anthropic_api_key": "***" if self.anthropic_api_key else "",
            "gemini_api_key": "***" if self.gemini_api_key else "",
            "api_timeout": self.api_timeout,
            "retry_count": self.retry_count
        }
    
    def is_secure(self) -> bool:
        """すべての必須セキュリティ設定が適切に設定されているかチェック"""
        # 最低限1つのLLM APIキーが設定されている必要がある
        has_llm_key = any([
            self.openai_api_key,
            self.gemini_api_key,
            self.anthropic_api_key
        ])
        
        # wxtech APIキーは必須
        has_weather_key = bool(self.wxtech_api_key)
        
        return has_llm_key and has_weather_key