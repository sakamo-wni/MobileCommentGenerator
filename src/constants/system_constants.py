"""System-related constants."""

# Batch processing
DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 100

# Concurrent processing
MAX_CONCURRENT_REQUESTS = 5
MAX_WORKERS = 4

# Network settings
REQUEST_TIMEOUT_SECONDS = 30
CONNECTION_TIMEOUT_SECONDS = 10

# File system
DEFAULT_ENCODING = "utf-8"
CSV_ENCODING = "utf-8-sig"  # UTF-8 with BOM

# API rate limiting
API_RATE_LIMIT_PER_MINUTE = 60
API_RATE_LIMIT_BURST = 10