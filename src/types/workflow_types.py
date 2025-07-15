"""
Workflow-related type definitions for Python 3.13+.
This module contains type definitions for LangGraph workflow states and metadata.
"""

from typing import TypedDict, NotRequired, Literal
from datetime import datetime

# Python 3.13 type alias syntax
type CommentType = Literal["weather_comment", "advice"]
type ValidationStatus = Literal["passed", "failed", "skipped"]
type CommentSource = Literal["generated", "past_comment", "fallback"]


class WorkflowError(TypedDict):
    """Error information in workflow execution."""
    message: str
    node: str | None
    timestamp: str
    error_type: NotRequired[str]
    stack_trace: NotRequired[str]


class SelectedCommentInfo(TypedDict):
    """Information about selected past comments."""
    text: str
    type: CommentType
    score: float | None
    original_index: int
    metadata: NotRequired[dict[str, str]]


class WeatherConditionInfo(TypedDict):
    """Weather condition summary for metadata."""
    temperature: float
    description: str
    is_severe: bool
    is_heat_wave: bool
    severity_level: NotRequired[Literal["low", "medium", "high", "extreme"]]


class GenerationMetadata(TypedDict):
    """Comprehensive metadata for comment generation workflow."""
    # Workflow execution info
    workflow_started_at: str
    completed_at: str | None
    execution_time_ms: int | None
    retry_count: int
    
    # Error and warning tracking
    errors: list[WorkflowError]
    warnings: list[WorkflowError]
    has_errors: bool
    has_warnings: bool
    
    # Generation details
    final_comment_source: CommentSource | None
    selected_past_comments: list[SelectedCommentInfo]
    
    # Weather context
    weather_condition: WeatherConditionInfo | None
    
    # Validation results
    validation_status: ValidationStatus | None
    validation_details: NotRequired[dict[str, bool]]
    
    # Additional context
    location_name: NotRequired[str]
    target_datetime: NotRequired[str]
    llm_provider: NotRequired[str]
    llm_model: NotRequired[str]


class CommentCandidate(TypedDict):
    """Structure for comment candidates during selection process."""
    index: int
    original_index: int
    comment_text: str
    priority: Literal["severe", "weather", "other"]
    score: float | None
    validation_status: ValidationStatus
    metadata: dict[str, str | float | bool]
    rejection_reason: NotRequired[str]


class TopographicFeatures(TypedDict):
    """Geographic and topographic features of a location."""
    is_coastal: bool
    distance_to_coast_km: float | None
    topographic_type: Literal[
        "coastal", 
        "near_coastal", 
        "plain", 
        "inland", 
        "mountainous", 
        "unknown"
    ]
    elevation_m: NotRequired[float | None]
    nearest_water_body: NotRequired[str | None]