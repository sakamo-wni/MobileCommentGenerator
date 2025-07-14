"""Constants module for MobileCommentGenerator."""

from .weather_constants import *
from .validation_constants import *
from .system_constants import *
from .time_constants import *
from .content_constants import *
from .validation_thresholds import *

__all__ = [
    # Weather constants
    "TEMPERATURE_MIN",
    "TEMPERATURE_MAX",
    "HUMIDITY_MIN",
    "HUMIDITY_MAX",
    "WIND_SPEED_MIN",
    "WIND_SPEED_MAX",
    "PRECIPITATION_THRESHOLD_LIGHT",
    "PRECIPITATION_THRESHOLD_MODERATE",
    "PRECIPITATION_THRESHOLD_HEAVY",
    "WIND_SPEED_THRESHOLD_STRONG",
    "TEMPERATURE_COMFORTABLE_MIN",
    "TEMPERATURE_COMFORTABLE_MAX",
    
    # Validation constants
    "MAX_COMMENT_LENGTH",
    "MIN_COMMENT_LENGTH",
    "MAX_LOCATION_NAME_LENGTH",
    "MAX_RETRY_COUNT",
    "CACHE_TTL_SECONDS",
    
    # System constants
    "DEFAULT_BATCH_SIZE",
    "MAX_CONCURRENT_REQUESTS",
    "REQUEST_TIMEOUT_SECONDS",
    "DEFAULT_ENCODING",
    
    # Time constants
    "MORNING_START_HOUR",
    "MORNING_END_HOUR",
    "NOON_START_HOUR",
    "NOON_END_HOUR",
    "EVENING_START_HOUR",
    "EVENING_END_HOUR",
    
    # Content constants
    "SEVERE_WEATHER_PATTERNS",
    "FORBIDDEN_PHRASES",
]