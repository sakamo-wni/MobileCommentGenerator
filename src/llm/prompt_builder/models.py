"""
Prompt builder data models

プロンプトビルダーのデータモデル定義
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """プロンプトテンプレート
    
    Attributes:
        base_template: 基本テンプレート
        weather_specific: 天気別テンプレート
        seasonal_adjustments: 季節調整テンプレート
        time_specific: 時間帯別テンプレート
        fallback_template: フォールバックテンプレート
        example_templates: 例文テンプレート
    """

    base_template: str
    weather_specific: dict[str, str]
    seasonal_adjustments: dict[str, str]
    time_specific: dict[str, str]
    fallback_template: str
    example_templates: dict[str, str]