"""型定義モジュール"""

from .common import (
    LLMProvider,
    WeatherCondition,
    CommentStyle,
    Season,
    WeatherData,
    GenerationMetadata,
    GenerationResult,
    LocationResult,
    BatchGenerationResult,
    HistoryItem,
    CommentPair,
    ValidationResult,
    APIResponse
)

from .aliases import (
    JsonDict,
    JsonList,
    NullableJsonDict,
    ConfigDict,
    StringMapping,
    WeatherMetadata,
    TemperatureDifferences,
    HistoryEntry,
    HistoryList,
    ProgressCallback,
    NumericStats,
    FloatStats,
    ApiResponse,
    ApiErrorDetail,
    BatchResult,
    LocationResults
)

__all__ = [
    # From common
    'LLMProvider',
    'WeatherCondition',
    'CommentStyle',
    'Season',
    'WeatherData',
    'GenerationMetadata',
    'GenerationResult',
    'LocationResult',
    'BatchGenerationResult',
    'HistoryItem',
    'CommentPair',
    'ValidationResult',
    'APIResponse',
    # From aliases
    'JsonDict',
    'JsonList',
    'NullableJsonDict',
    'ConfigDict',
    'StringMapping',
    'WeatherMetadata',
    'TemperatureDifferences',
    'HistoryEntry',
    'HistoryList',
    'ProgressCallback',
    'NumericStats',
    'FloatStats',
    'ApiResponse',
    'ApiErrorDetail',
    'BatchResult',
    'LocationResults'
]