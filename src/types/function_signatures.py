"""Standardized function signatures for consistency across the codebase"""

from typing import Protocol, Optional, Dict, Any, List
from datetime import datetime

from .common import LLMProvider, PastComment, WeatherForecast

# Standard parameter order convention:
# 1. Primary identifier (location_name)
# 2. Time-related parameters (target_datetime, start_date, end_date)
# 3. Provider/configuration (llm_provider)
# 4. Optional flags (exclude_previous, force_refresh, etc.)
# 5. Additional options (**kwargs)

class CommentGeneratorProtocol(Protocol):
    """Standard interface for comment generation functions"""
    
    def __call__(
        self,
        location_name: str,
        target_datetime: Optional[datetime] = None,
        llm_provider: Optional[LLMProvider] = None,
        exclude_previous: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        ...

class CommentRetrieverProtocol(Protocol):
    """Standard interface for comment retrieval functions"""
    
    def __call__(
        self,
        location_name: str,
        target_datetime: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs: Any
    ) -> List[PastComment]:
        ...

class WeatherFetcherProtocol(Protocol):
    """Standard interface for weather data fetching"""
    
    def __call__(
        self,
        location_name: str,
        target_datetime: Optional[datetime] = None,
        force_refresh: bool = False,
        **kwargs: Any
    ) -> WeatherForecast:
        ...

class CommentEvaluatorProtocol(Protocol):
    """Standard interface for comment evaluation"""
    
    def __call__(
        self,
        comment: str,
        location_name: str,
        target_datetime: Optional[datetime] = None,
        weather_data: Optional[WeatherForecast] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        ...