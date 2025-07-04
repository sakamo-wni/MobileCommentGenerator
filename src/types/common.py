"""共通の型定義"""

from typing import TypedDict, Optional, List, Dict, Any, Union, Literal
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
    wind_speed: Optional[float]
    humidity: Optional[float]
    precipitation: Optional[float]
    forecast_time: str
    location: str


class GenerationMetadata(TypedDict, total=False):
    """生成メタデータの型定義"""
    execution_time_ms: int
    temperature: float
    weather_condition: WeatherCondition
    wind_speed: Optional[float]
    humidity: Optional[float]
    forecast_time: str
    retry_count: int
    llm_provider: LLMProvider
    validation_score: Optional[float]
    weather_timeline: Optional[Dict[str, Any]]
    selected_past_comments: Optional[List[Dict[str, str]]]
    selection_metadata: Optional[Dict[str, Any]]


class GenerationResult(TypedDict):
    """生成結果の型定義"""
    success: bool
    final_comment: Optional[str]
    error: Optional[str]
    generation_metadata: Optional[GenerationMetadata]


class LocationResult(TypedDict):
    """地点別結果の型定義"""
    location: str
    result: Optional[GenerationResult]
    success: bool
    comment: str
    error: Optional[str]
    source_files: Optional[List[str]]


class BatchGenerationResult(TypedDict):
    """バッチ生成結果の型定義"""
    success: bool
    total_locations: int
    success_count: int
    results: List[LocationResult]
    final_comment: str
    errors: List[str]


class HistoryItem(TypedDict):
    """履歴項目の型定義"""
    timestamp: str
    location: str
    llm_provider: LLMProvider
    success: bool
    final_comment: Optional[str]
    generation_metadata: Optional[GenerationMetadata]


@dataclass
class CommentPair:
    """コメントペアのデータクラス"""
    weather_comment: str
    advice_comment: str
    source_file: Optional[str] = None
    score: Optional[float] = None


@dataclass
class ValidationResult:
    """バリデーション結果のデータクラス"""
    is_valid: bool
    score: float
    errors: List[str]
    warnings: List[str]


@dataclass
class APIResponse:
    """API応答の基本データクラス"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None