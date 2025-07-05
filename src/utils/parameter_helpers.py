"""Helper functions for standardizing function parameters"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime

def standardize_weather_params(
    location_name: str,
    target_datetime: Optional[datetime] = None,
    **kwargs: Any
) -> Dict[str, Any]:
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

def extract_location_coords(location_name: str) -> Tuple[str, Optional[float], Optional[float]]:
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
    target_datetime: Optional[datetime] = None,
    llm_provider: Optional[str] = None,
    exclude_previous: bool = False,
    **kwargs: Any
) -> Dict[str, Any]:
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