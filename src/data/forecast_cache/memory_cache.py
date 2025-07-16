"""
In-memory cache layer for forecast cache

予報キャッシュのインメモリキャッシュレイヤー
"""

from __future__ import annotations
import time
import logging
from typing import Optional, Dict, Any, Tuple
from threading import RLock
from collections import OrderedDict
from datetime import datetime

from .models import ForecastCacheEntry

logger = logging.getLogger(__name__)


class ForecastMemoryCache:
    """予報データのインメモリキャッシュ
    
    LRU方式でメモリ上にキャッシュを保持し、
    CSVアクセスの前に高速な検索を提供
    """
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        """初期化
        
        Args:
            max_size: 最大キャッシュエントリ数
            ttl_seconds: キャッシュの有効期限（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[ForecastCacheEntry, float]] = OrderedDict()
        self._lock = RLock()
        self._hits = 0
        self._misses = 0
        
    def _make_key(self, location_name: str, target_datetime: datetime) -> str:
        """キャッシュキーを生成
        
        Args:
            location_name: 地点名
            target_datetime: 対象日時
            
        Returns:
            キャッシュキー
        """
        # 時間は分単位に丸める（秒以下は無視）
        dt_str = target_datetime.strftime("%Y%m%d%H%M")
        return f"{location_name}:{dt_str}"
    
    def get(self, location_name: str, target_datetime: datetime) -> Optional[ForecastCacheEntry]:
        """キャッシュからエントリを取得
        
        Args:
            location_name: 地点名
            target_datetime: 対象日時
            
        Returns:
            キャッシュエントリ（見つからない場合はNone）
        """
        key = self._make_key(location_name, target_datetime)
        
        with self._lock:
            if key in self._cache:
                entry, timestamp = self._cache[key]
                
                # TTLチェック
                if time.time() - timestamp <= self.ttl_seconds:
                    # LRU: 最後に移動
                    self._cache.move_to_end(key)
                    self._hits += 1
                    logger.debug(f"Memory cache hit for {key}")
                    return entry
                else:
                    # 期限切れ
                    del self._cache[key]
                    logger.debug(f"Memory cache expired for {key}")
            
            self._misses += 1
            return None
    
    def put(self, location_name: str, target_datetime: datetime, entry: ForecastCacheEntry) -> None:
        """キャッシュにエントリを追加
        
        Args:
            location_name: 地点名
            target_datetime: 対象日時
            entry: キャッシュエントリ
        """
        key = self._make_key(location_name, target_datetime)
        
        with self._lock:
            # 既存エントリがある場合は削除
            if key in self._cache:
                del self._cache[key]
            
            # サイズ制限チェック
            while len(self._cache) >= self.max_size:
                # LRU: 最も古いエントリを削除
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Evicted {oldest_key} from memory cache")
            
            # 新規追加
            self._cache[key] = (entry, time.time())
            logger.debug(f"Added {key} to memory cache")
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Memory cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得
        
        Returns:
            統計情報の辞書
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds
            }
    
    def cleanup_expired(self) -> int:
        """期限切れエントリをクリーンアップ
        
        Returns:
            削除されたエントリ数
        """
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, (entry, timestamp) in self._cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries from memory cache")
                
        return len(expired_keys)