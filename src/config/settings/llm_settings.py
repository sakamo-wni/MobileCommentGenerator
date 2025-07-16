"""LLM（大規模言語モデル）関連の設定モジュール"""

from __future__ import annotations
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from pathlib import Path

# 環境変数の読み込み
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.shared", override=False)


@dataclass
class LLMConfig:
    """LLM関連の設定
    
    大規模言語モデル（LLM）の設定を管理します。
    プロバイダー、モデル名、生成パラメータなどを設定できます。
    """
    default_provider: str = field(default="gemini")
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=1000)
    
    # プロバイダー別の設定
    openai_model: str = field(default="gpt-4o-mini")
    anthropic_model: str = field(default="claude-3-haiku-20240307")
    gemini_model: str = field(default="gemini-1.5-flash")
    
    # パフォーマンスモード（高速モデルを使用）
    performance_mode: bool = field(default=False)
    performance_openai_model: str = field(default="gpt-3.5-turbo")
    performance_anthropic_model: str = field(default="claude-3-haiku-20240307")
    performance_gemini_model: str = field(default="gemini-1.5-flash")
    
    def __post_init__(self):
        """環境変数から値を読み込む"""
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", self.default_provider)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", str(self.temperature)))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", str(self.max_tokens)))
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.anthropic_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        
        # パフォーマンスモードの設定
        self.performance_mode = os.getenv("LLM_PERFORMANCE_MODE", "false").lower() == "true"
        self.performance_openai_model = os.getenv("PERFORMANCE_OPENAI_MODEL", self.performance_openai_model)
        self.performance_anthropic_model = os.getenv("PERFORMANCE_ANTHROPIC_MODEL", self.performance_anthropic_model)
        self.performance_gemini_model = os.getenv("PERFORMANCE_GEMINI_MODEL", self.performance_gemini_model)


@dataclass
class LangGraphConfig:
    """LangGraph統合機能の設定"""
    enable_weather_integration: bool = field(default=True)
    auto_location_detection: bool = field(default=False)
    weather_context_window: int = field(default=24)
    min_confidence_threshold: float = field(default=0.7)
    
    def __post_init__(self):
        """環境変数から設定を読み込む"""
        self.enable_weather_integration = os.getenv("LANGGRAPH_ENABLE_WEATHER_INTEGRATION", "true" if self.enable_weather_integration else "false").lower() == "true"
        self.auto_location_detection = os.getenv("LANGGRAPH_AUTO_LOCATION_DETECTION", "true" if self.auto_location_detection else "false").lower() == "true"
        self.weather_context_window = int(os.getenv("LANGGRAPH_WEATHER_CONTEXT_WINDOW", str(self.weather_context_window)))
        self.min_confidence_threshold = float(os.getenv("LANGGRAPH_MIN_CONFIDENCE_THRESHOLD", str(self.min_confidence_threshold)))