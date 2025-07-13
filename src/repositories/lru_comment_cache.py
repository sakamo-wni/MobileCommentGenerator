"""LRU (Least Recently Used) キャッシュの実装

メモリ使用量を制限しながら、複数のクエリ結果をキャッシュする高性能なキャッシュシステム。
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import sys

from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class LRUCommentCache:
    """コメントのLRUキャッシュ管理
    
    最近使用されたアイテムを保持し、メモリ使用量を制限する。
    キーベースのキャッシュで、異なるクエリ結果を個別にキャッシュ可能。
    """
    
    def __init__(self, 
                 max_size: int = 1000, 
                 cache_ttl_minutes: int = 60,
                 max_memory_mb: float = 100):
        """
        Args:
            max_size: キャッシュに保持する最大エントリ数
            cache_ttl_minutes: キャッシュの有効期限（分）
            max_memory_mb: 最大メモリ使用量（MB）
        """
        self._cache: OrderedDict[str, Tuple[List[PastComment], datetime]] = OrderedDict()
        self._max_size = max_size
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # 統計情報
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0
        self._eviction_count = 0
        
    def _estimate_memory_usage(self, comments: List[PastComment]) -> int:
        """コメントリストのメモリ使用量を推定（バイト）"""
        # 簡易的な推定: 各コメントのテキスト長 + オーバーヘッド
        total_size = 0
        for comment in comments:
            # テキストサイズ + 属性のオーバーヘッド（推定）
            total_size += len(comment.text.encode('utf-8')) + 200
            # raw_dataの推定サイズ
            total_size += sys.getsizeof(comment.raw_data)
        return total_size
    
    def _get_total_memory_usage(self) -> int:
        """現在のキャッシュの総メモリ使用量を推定"""
        total = 0
        for comments, _ in self._cache.values():
            total += self._estimate_memory_usage(comments)
        return total
    
    def _evict_if_needed(self, new_size: int) -> None:
        """必要に応じて古いエントリを削除"""
        # サイズ制限チェック
        while len(self._cache) >= self._max_size:
            self._evict_oldest()
            
        # メモリ制限チェック
        current_memory = self._get_total_memory_usage()
        while current_memory + new_size > self._max_memory_bytes and self._cache:
            self._evict_oldest()
            current_memory = self._get_total_memory_usage()
    
    def _evict_oldest(self) -> None:
        """最も古いエントリを削除"""
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._eviction_count += 1
            logger.debug(f"Evicted cache entry: {key}")
    
    def _is_entry_valid(self, timestamp: datetime) -> bool:
        """エントリが有効期限内かチェック"""
        return datetime.now() - timestamp < self._cache_ttl
    
    def get(self, key: str) -> Optional[List[PastComment]]:
        """キャッシュからコメントを取得"""
        self._total_requests += 1
        
        if key in self._cache:
            comments, timestamp = self._cache[key]
            
            if self._is_entry_valid(timestamp):
                # LRU: 最近使用されたものを最後に移動
                self._cache.move_to_end(key)
                self._cache_hits += 1
                logger.debug(f"Cache hit for key: {key} (hit rate: {self.get_hit_rate():.1%})")
                return comments
            else:
                # 期限切れのエントリを削除
                del self._cache[key]
                logger.debug(f"Cache entry expired for key: {key}")
        
        self._cache_misses += 1
        logger.debug(f"Cache miss for key: {key} (hit rate: {self.get_hit_rate():.1%})")
        return None
    
    def set(self, key: str, comments: List[PastComment]) -> None:
        """キャッシュにコメントを設定"""
        new_size = self._estimate_memory_usage(comments)
        
        # 既存のエントリがある場合は削除
        if key in self._cache:
            del self._cache[key]
        
        # 必要に応じて古いエントリを削除
        self._evict_if_needed(new_size)
        
        # 新しいエントリを追加
        self._cache[key] = (comments, datetime.now())
        logger.info(f"Cache updated for key: {key} with {len(comments)} comments")
    
    def clear(self) -> None:
        """キャッシュを完全にクリア"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def invalidate(self, key: str) -> bool:
        """特定のキーのキャッシュを無効化"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache for key: {key}")
            return True
        return False
    
    def get_hit_rate(self) -> float:
        """キャッシュヒット率を計算"""
        if self._total_requests == 0:
            return 0.0
        return self._cache_hits / self._total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """詳細なキャッシュ統計を取得"""
        memory_usage_mb = self._get_total_memory_usage() / (1024 * 1024)
        
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'memory_usage_mb': round(memory_usage_mb, 2),
            'max_memory_mb': self._max_memory_bytes / (1024 * 1024),
            'ttl_minutes': self._cache_ttl.total_seconds() / 60,
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total_requests': self._total_requests,
            'hit_rate': self.get_hit_rate(),
            'eviction_count': self._eviction_count,
            'keys': list(self._cache.keys())
        }
    
    def cleanup_expired(self) -> int:
        """期限切れのエントリをクリーンアップ"""
        expired_keys = []
        for key, (_, timestamp) in self._cache.items():
            if not self._is_entry_valid(timestamp):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)