"""共通の型定義"""

from typing import TypedDict, Any, Literal
from datetime import datetime
from dataclasses import dataclass


# リテラル型の定義
LLMProvider = Literal["openai", "gemini", "anthropic"]
# 天気条件は文字列で柔軟に受け入れる
WeatherCondition = str  # "晴れ", "曇り", "くもり", "雨", "雪", "不明" など
CommentStyle = Literal["カジュアル", "フォーマル", "親しみやすい"]
Season = Literal["春", "夏", "秋", "冬", "梅雨", "台風"]


class WeatherData(TypedDict):
    """天気データの型定義"""
    temperature: float
    weather_condition: WeatherCondition
    wind_speed: float | None
    humidity: float | None
    precipitation: float | None
    forecast_time: str
    location: str


class GenerationMetadata(TypedDict, total=False):
    """生成メタデータの型定義"""
    execution_time_ms: int
    temperature: float
    weather_condition: WeatherCondition
    wind_speed: float | None
    humidity: float | None
    forecast_time: str
    retry_count: int
    llm_provider: LLMProvider
    validation_score: float | None
    weather_timeline: dict[str, Any | None]
    selected_past_comments: list[dict[str, str | None]]
    selection_metadata: dict[str, Any | None]


class GenerationResult(TypedDict):
    """生成結果の型定義"""
    success: bool
    final_comment: str | None
    error: str | None
    generation_metadata: GenerationMetadata | None


class LocationResult(TypedDict):
    """地点別結果の型定義"""
    location: str
    result: GenerationResult | None
    success: bool
    comment: str
    error: str | None
    source_files: list[str | None]


class BatchGenerationResult(TypedDict):
    """バッチ生成結果の型定義"""
    success: bool
    total_locations: int
    success_count: int
    results: list[LocationResult]
    final_comment: str
    errors: list[str]


class HistoryItem(TypedDict):
    """履歴項目の型定義"""
    timestamp: str
    location: str
    llm_provider: LLMProvider
    success: bool
    final_comment: str | None
    generation_metadata: GenerationMetadata | None


@dataclass
class CommentPair:
    """コメントペアのデータクラス"""
    weather_comment: str
    advice_comment: str
    source_file: str | None = None
    score: float | None = None


@dataclass
class ValidationResult:
    """バリデーション結果のデータクラス"""
    is_valid: bool
    score: float
    errors: list[str]
    warnings: list[str]


@dataclass
class APIResponse:
    """API応答の基本データクラス"""
    success: bool
    data: Any | None = None
    error: str | None = None
    error_details: dict[str, Any | None] = None