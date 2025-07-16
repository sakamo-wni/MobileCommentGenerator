"""APIリクエストのキャッシュ機能を提供するユーティリティ"""

from __future__ import annotations
import time
import hashlib
import json
import inspect
import threading
import sys
from typing import Any, TypeVar
from collections.abc import Callable
from functools import wraps
import logging

# Import type definitions for Python 3.13+
from src.types.cache_types import CacheEntry, CacheStats, CacheKey

logger = logging.getLogger(__name__)

# Type variable for generic cache values
T = TypeVar('T')


class TTLCache:
    """TTL（Time To Live）付きキャッシュ（スレッドセーフ版）
    
    指定された期間だけデータをメモリにキャッシュし、
    期限切れのデータは自動的に削除される。
    threadingモジュールのRLockを使用してスレッドセーフを保証。
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int | None = None,
                 auto_cleanup: bool = True, cleanup_interval: int = 60):
        """初期化
        
        Args:
            default_ttl: デフォルトのTTL（秒）。デフォルトは5分
            max_size: キャッシュの最大サイズ（エントリ数）。Noneの場合は無制限
            auto_cleanup: 自動クリーンアップを有効にするか。デフォルトはTrue
            cleanup_interval: クリーンアップの実行間隔（秒）。デフォルトは60秒
        """
        self._cache: dict[CacheKey, CacheEntry[Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._stats: dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        # RLock（再入可能ロック）を使用してスレッドセーフを保証
        self._lock = threading.RLock()
        
        # 自動クリーンアップ機能
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self._cleanup_thread: threading.Thread | None = None
        self._stop_cleanup = threading.Event()
        
        if self.auto_cleanup:
            self._start_cleanup_thread()
    
    def get(self, key: CacheKey) -> Any | None:
        """キャッシュからデータを取得（スレッドセーフ）
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされたデータ、存在しないか期限切れの場合はNone
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                current_time = time.time()
                if current_time < entry["expire_at"]:
                    self._stats["hits"] += 1
                    # アクセス情報を更新
                    entry["access_count"] += 1
                    entry["last_accessed"] = current_time
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
        """データをキャッシュに保存（スレッドセーフ）
        
        Args:
            key: キャッシュキー
            value: キャッシュするデータ
            ttl: TTL（秒）。Noneの場合はdefault_ttlを使用
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # 最大サイズチェック
            if self.max_size and len(self._cache) >= self.max_size:
                # LRU（Least Recently Used）エビクション
                self._evict_lru()
            
            current_time = time.time()
            self._cache[key] = CacheEntry(
                value=value,
                expire_at=current_time + ttl,
                created_at=current_time,
                access_count=0,
                last_accessed=current_time
            )
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def _evict_lru(self):
        """最も最近使われていないエントリを削除（内部メソッド）"""
        # ロックは既に取得済みの前提
        if not self._cache:
            return
        
        # 最も古いアクセス時刻を持つキーを探す
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k]["last_accessed"])
        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug(f"LRU eviction: {lru_key}")
    
    def evict_lru(self, count: int = 1) -> int:
        """指定された数のLRUエントリを削除（スレッドセーフ）
        
        Args:
            count: 削除するエントリ数（デフォルト: 1）
            
        Returns:
            実際に削除されたエントリ数
        """
        with self._lock:
            evicted = 0
            for _ in range(min(count, len(self._cache))):
                if self._cache:
                    self._evict_lru()
                    evicted += 1
                else:
                    break
            return evicted
    
    def clear(self):
        """キャッシュをクリア（スレッドセーフ）"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """期限切れのエントリを削除（スレッドセーフ）"""
        with self._lock:
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
        """キャッシュの統計情報を取得（スレッドセーフ）"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
            
            # Calculate memory usage
            memory_usage = self._estimate_memory_usage()
            
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
    
    def _estimate_memory_usage(self) -> int:
        """キャッシュのメモリ使用量を推定（バイト単位）"""
        # ロックは既に取得済みの前提
        try:
            # より正確なメモリ計算を試みる
            from src.utils.memory_utils import estimate_cache_memory_usage
            
            # キャッシュエントリのみのメモリ使用量を計算
            cache_memory = estimate_cache_memory_usage(self._cache)
            
            # その他のオーバーヘッドを追加
            overhead = sys.getsizeof(self._stats) + sys.getsizeof(self._lock)
            
            return cache_memory["total_size"] + overhead
            
        except ImportError:
            # フォールバック: 従来の簡易計算
            total_size = 0
            
            # 基本的なオーバーヘッド（辞書、統計情報など）
            total_size += sys.getsizeof(self._cache)
            total_size += sys.getsizeof(self._stats)
            
            # 各エントリのサイズを推定
            for key, entry in self._cache.items():
                # キーのサイズ
                total_size += sys.getsizeof(key)
                # エントリのサイズ（辞書のオーバーヘッド含む）
                total_size += sys.getsizeof(entry)
                # 値のサイズ（深い推定は避け、表層のみ）
                total_size += sys.getsizeof(entry["value"])
            
            return total_size
    
    def _start_cleanup_thread(self):
        """自動クリーンアップスレッドを開始"""
        def cleanup_worker():
            """クリーンアップワーカー"""
            while not self._stop_cleanup.is_set():
                # 指定された間隔で待機
                if self._stop_cleanup.wait(self.cleanup_interval):
                    break
                
                # 期限切れエントリをクリーンアップ
                try:
                    self.cleanup_expired()
                    logger.debug("Automatic cache cleanup executed")
                except Exception as e:
                    logger.error(f"Error during automatic cache cleanup: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info(f"Started automatic cache cleanup thread (interval: {self.cleanup_interval}s)")
    
    def stop_cleanup(self):
        """自動クリーンアップを停止"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
            logger.info("Stopped automatic cache cleanup thread")
    
    def __del__(self):
        """デストラクタ - クリーンアップスレッドを停止"""
        try:
            self.stop_cleanup()
        except Exception:
            pass  # デストラクタでのエラーは無視


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
# 自動クリーンアップを有効化、60秒間隔でクリーンアップ
_global_cache = TTLCache(default_ttl=300, auto_cleanup=True, cleanup_interval=60)


def get_global_cache() -> TTLCache:
    """グローバルキャッシュインスタンスを取得"""
    return _global_cache