"""
Cache-related type definitions for Python 3.13+.
This module contains type definitions for TTL cache implementation.
"""

from typing import TypedDict, Any, Generic, TypeVar
from datetime import datetime

# Type variable for cached values
T = TypeVar('T')

# Python 3.13 type alias syntax
type CacheKey = str
type ExpirationTime = float


class CacheEntry(TypedDict, Generic[T]):
    """Structure for a single cache entry."""
    value: T
    expire_at: float
    created_at: float
    access_count: int
    last_accessed: float


class CacheStats(TypedDict):
    """Cache statistics information."""
    size: int
    hits: int
    misses: int
    evictions: int
    hit_rate: float
    total_requests: int
    memory_usage_bytes: int | None
    oldest_entry_age_seconds: float | None
    newest_entry_age_seconds: float | None


class CacheConfig(TypedDict):
    """Configuration for cache behavior."""
    default_ttl_seconds: float
    max_size: int | None
    eviction_policy: str  # "lru", "fifo", "ttl_only"
    enable_stats: bool
    cleanup_interval_seconds: float | None