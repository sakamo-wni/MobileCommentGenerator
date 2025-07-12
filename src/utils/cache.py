"""APIリクエストのキャッシュ機能を提供するユーティリティ"""

import time
import hashlib
import json
from typing import Any, Dict, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


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
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
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
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """データをキャッシュに保存
        
        Args:
            key: キャッシュキー
            value: キャッシュするデータ
            ttl: TTL（秒）。Noneの場合はdefault_ttlを使用
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl,
            "created_at": time.time()
        }
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
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }


def generate_cache_key(*args, **kwargs) -> str:
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


def async_cached_method(ttl: Optional[int] = None, cache_attr: str = "_cache"):
    """非同期メソッドの結果をキャッシュするデコレータ
    
    Args:
        ttl: TTL（秒）。Noneの場合はキャッシュのデフォルト値を使用
        cache_attr: キャッシュオブジェクトの属性名
        
    Returns:
        デコレートされた非同期メソッド
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
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
                return cached_result
            
            # キャッシュにない場合は実行してキャッシュに保存
            result = await func(self, *args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cached_method(ttl: Optional[int] = None, cache_attr: str = "_cache"):
    """メソッドの結果をキャッシュするデコレータ
    
    Args:
        ttl: TTL（秒）。Noneの場合はキャッシュのデフォルト値を使用
        cache_attr: キャッシュオブジェクトの属性名
        
    Returns:
        デコレートされたメソッド
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
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
                return cached_result
            
            # キャッシュにない場合は実行してキャッシュに保存
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# グローバルキャッシュインスタンス（オプション）
_global_cache = TTLCache(default_ttl=300)


def get_global_cache() -> TTLCache:
    """グローバルキャッシュインスタンスを取得"""
    return _global_cache