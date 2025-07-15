"""
API-related type definitions for Python 3.13+.
This module contains type definitions for API parameters and responses.
"""

from typing import TypedDict, Literal, NotRequired, Any
from dataclasses import dataclass, field
import hashlib
import json

# Python 3.13 type alias syntax
type HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
type StatusCode = int


class WxTechParams(TypedDict):
    """Parameters for WxTech API requests."""
    lat: float
    lon: float
    hours: int
    # Optional parameters
    lang: NotRequired[str]
    units: NotRequired[str]


@dataclass(frozen=True)
class CachedWxTechParams:
    """WxTech API parameters with pre-computed cache key."""
    lat: float
    lon: float
    hours: int
    lang: str = "ja"
    units: str = "metric"
    _cache_key: str = field(init=False, repr=False)
    
    def __post_init__(self):
        """Compute cache key once during initialization."""
        # Create a deterministic string representation
        key_data = {
            "lat": round(self.lat, 6),  # Round to 6 decimal places for consistency
            "lon": round(self.lon, 6),
            "hours": self.hours,
            "lang": self.lang,
            "units": self.units
        }
        key_str = json.dumps(key_data, sort_keys=True)
        cache_key = f"wxtech:{hashlib.md5(key_str.encode()).hexdigest()}"
        object.__setattr__(self, '_cache_key', cache_key)
    
    @property
    def cache_key(self) -> str:
        """Get the pre-computed cache key."""
        return self._cache_key
    
    def to_dict(self) -> dict[str, float | int | str]:
        """Convert to dictionary for API request."""
        return {
            "lat": self.lat,
            "lon": self.lon,
            "hours": self.hours,
            "lang": self.lang,
            "units": self.units
        }


class APIResponse(TypedDict):
    """Generic API response structure."""
    status: StatusCode
    data: dict[str, Any] | list[Any]
    message: NotRequired[str]
    timestamp: NotRequired[str]
    request_id: NotRequired[str]


class APIError(TypedDict):
    """API error response structure."""
    status: StatusCode
    error: str
    message: str
    details: NotRequired[dict[str, Any]]
    timestamp: NotRequired[str]