"""Validation-related constants."""

# Comment length constraints
MAX_COMMENT_LENGTH = 200
MIN_COMMENT_LENGTH = 10

# Location constraints
MAX_LOCATION_NAME_LENGTH = 100

# Retry and timeout settings
MAX_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds

# Cache settings
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_MAX_SIZE = 1000

# Duplicate detection thresholds
SIMILARITY_THRESHOLD_HIGH = 0.9
SIMILARITY_THRESHOLD_MEDIUM = 0.7