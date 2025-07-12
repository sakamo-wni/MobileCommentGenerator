"""APIリクエストのキャッシュ機能を提供するユーティリティ"""

import time
import hashlib
import json
import inspect
from typing import Any, Optional, Callable, TypeVar, cast
from functools import wraps
import logging

# Import type definitions for Python 3.13+
from src.types.cache_types import CacheEntry, CacheStats, CacheKey

logger = logging.getLogger(__name__)

# Type variable for generic cache values
T = TypeVar('T')


class TTLCache:
    """TTL（Time To Live）付きキャッシュ
    
    指定された期間だけデータをメモリにキャッシュし、
    期限切れのデータは自動的に削除される
    """
    
    def __init__(self, default_ttl: int = 300):
        """初期化
        
        Args:
            default_ttl: デフォルトのTTL（秒）。デフォルトは5分
        """
        self._cache: dict[CacheKey, CacheEntry[Any]] = {}
        self.default_ttl = default_ttl
        self._stats: dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def get(self, key: CacheKey) -> Any | None:
        """キャッシュからデータを取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされたデータ、存在しないか期限切れの場合はNone
        """
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expire_at"]:
                self._stats["hits"] += 1
                logger.debug(f"Cache hit: {key}")
                return entry["value"]
            else:
                # 期限切れのエントリを削除
                del self._cache[key]
                self._stats["evictions"] += 1
                logger.debug(f"Cache expired: {key}")
        
        self._stats["misses"] += 1
        return None
    
    def set(self, key: CacheKey, value: Any, ttl: int | None = None):
        """データをキャッシュに保存
        
        Args:
            key: キャッシュキー
            value: キャッシュするデータ
            ttl: TTL（秒）。Noneの場合はdefault_ttlを使用
        """
        if ttl is None:
            ttl = self.default_ttl
        
        current_time = time.time()
        self._cache[key] = CacheEntry(
            value=value,
            expire_at=current_time + ttl,
            created_at=current_time,
            access_count=0,
            last_accessed=current_time
        )
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def clear(self):
        """キャッシュをクリア"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """期限切れのエントリを削除"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time >= entry["expire_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats["evictions"] += 1
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> CacheStats:
        """キャッシュの統計情報を取得"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        # Calculate memory usage and entry ages
        memory_usage = None
        oldest_age = None
        newest_age = None
        
        if self._cache:
            current_time = time.time()
            ages = [current_time - entry["created_at"] for entry in self._cache.values()]
            oldest_age = max(ages)
            newest_age = min(ages)
        
        return CacheStats(
            size=len(self._cache),
            hits=self._stats["hits"],
            misses=self._stats["misses"],
            evictions=self._stats["evictions"],
            hit_rate=hit_rate,
            total_requests=total_requests,
            memory_usage_bytes=memory_usage,
            oldest_entry_age_seconds=oldest_age,
            newest_entry_age_seconds=newest_age
        )


def generate_cache_key(*args, **kwargs) -> CacheKey:
    """引数からキャッシュキーを生成
    
    Args:
        *args: 位置引数
        **kwargs: キーワード引数
        
    Returns:
        ハッシュ化されたキャッシュキー
    """
    # selfを除外（メソッドの場合）
    filtered_args = args[1:] if args and hasattr(args[0], "__class__") else args
    
    # シリアライズ可能な形式に変換
    key_data = {
        "args": filtered_args,
        "kwargs": kwargs
    }
    
    # JSON形式でシリアライズしてハッシュ化
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def universal_cached_method(ttl: int | None = None, cache_attr: str = "_cache"):
    """メソッドの結果をキャッシュする統一デコレータ（同期・非同期両対応）
    
    Args:
        ttl: TTL（秒）。Noneの場合はキャッシュのデフォルト値を使用
        cache_attr: キャッシュオブジェクトの属性名
        
    Returns:
        デコレートされたメソッド（同期または非同期）
    """
    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                # キャッシュオブジェクトを取得
                cache = getattr(self, cache_attr, None)
                if cache is None:
                    # キャッシュがない場合は通常実行
                    return await func(self, *args, **kwargs)
                
                # キャッシュキーを生成
                cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得を試みる
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for async method: {func.__name__}")
                    return cached_result
                
                # キャッシュにない場合は実行してキャッシュに保存
                result = await func(self, *args, **kwargs)
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for async method: {func.__name__}")
                
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                # キャッシュオブジェクトを取得
                cache = getattr(self, cache_attr, None)
                if cache is None:
                    # キャッシュがない場合は通常実行
                    return func(self, *args, **kwargs)
                
                # キャッシュキーを生成
                cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得を試みる
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for sync method: {func.__name__}")
                    return cached_result
                
                # キャッシュにない場合は実行してキャッシュに保存
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, ttl)
                logger.debug(f"Cached result for sync method: {func.__name__}")
                
                return result
            
            return sync_wrapper
    
    return decorator


# 互換性のためのエイリアス
async_cached_method = universal_cached_method
cached_method = universal_cached_method


# グローバルキャッシュインスタンス（オプション）
_global_cache = TTLCache(default_ttl=300)


def get_global_cache() -> TTLCache:
    """グローバルキャッシュインスタンスを取得"""
    return _global_cache