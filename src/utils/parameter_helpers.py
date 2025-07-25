"""Helper functions for standardizing function parameters"""

from __future__ import annotations
from typing import Any
from datetime import datetime

def standardize_weather_params(
    location_name: str,
    target_datetime: datetime | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Standardize weather-related function parameters
    
    Args:
        location_name: Location name
        target_datetime: Target datetime (optional)
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with standardized parameters
    """
    params = {
        'location_name': location_name,
        'target_datetime': target_datetime or datetime.now(),
    }
    params.update(kwargs)
    return params

def extract_location_coords(location_name: str) -> tuple[str, float | None, float | None]:
    """Extract location name and coordinates from a string
    
    Args:
        location_name: Location string, possibly in format "name,lat,lon"
        
    Returns:
        Tuple of (location_name, latitude, longitude)
    """
    provided_lat = None
    provided_lon = None
    
    if "," in location_name:
        parts = location_name.split(",")
        clean_name = parts[0].strip()
        if len(parts) >= 3:
            try:
                provided_lat = float(parts[1].strip())
                provided_lon = float(parts[2].strip())
            except ValueError:
                pass
        return clean_name, provided_lat, provided_lon
    
    return location_name.strip(), None, None

def standardize_comment_params(
    location_name: str,
    target_datetime: datetime | None = None,
    llm_provider: str | None = None,
    exclude_previous: bool = False,
    **kwargs: Any
) -> dict[str, Any]:
    """Standardize comment generation parameters
    
    Args:
        location_name: Location name
        target_datetime: Target datetime (optional)
        llm_provider: LLM provider name (optional)
        exclude_previous: Whether to exclude previous comments
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with standardized parameters
    """
    params = {
        'location_name': location_name,
        'target_datetime': target_datetime or datetime.now(),
        'llm_provider': llm_provider,
        'exclude_previous': exclude_previous,
    }
    params.update(kwargs)
    return params