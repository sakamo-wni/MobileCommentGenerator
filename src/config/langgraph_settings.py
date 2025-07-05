"""
LangGraph統合機能の設定管理

LangGraph関連の設定を管理する
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class LangGraphConfig:
    """LangGraph統合機能の設定クラス

    Attributes:
        enable_weather_integration: 天気統合の有効化
        auto_location_detection: 自動地点検出の有効化
        weather_context_window: 天気情報のコンテキスト窓
        min_confidence_threshold: 最小信頼度閾値
    """

    enable_weather_integration: bool = field(default=True)
    auto_location_detection: bool = field(default=False)
    weather_context_window: int = field(default=24)
    min_confidence_threshold: float = field(default=0.7)
    
    def __post_init__(self):
        """環境変数から設定を読み込む"""
        self.enable_weather_integration = os.getenv("LANGGRAPH_ENABLE_WEATHER", "true" if self.enable_weather_integration else "false").lower() == "true"
        self.auto_location_detection = os.getenv("LANGGRAPH_AUTO_LOCATION", "true" if self.auto_location_detection else "false").lower() == "true"
        self.weather_context_window = int(os.getenv("LANGGRAPH_WEATHER_CONTEXT_WINDOW", str(self.weather_context_window)))
        self.min_confidence_threshold = float(os.getenv("LANGGRAPH_MIN_CONFIDENCE", str(self.min_confidence_threshold)))

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "enable_weather_integration": self.enable_weather_integration,
            "auto_location_detection": self.auto_location_detection,
            "weather_context_window": self.weather_context_window,
            "min_confidence_threshold": self.min_confidence_threshold,
        }