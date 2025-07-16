"""
Multi-level comment cache implementation

マルチレベルコメントキャッシュの実装
"""

from __future__ import annotations
import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from threading import RLock

from src.data.past_comment import PastComment, CommentType
from src.repositories.lru_comment_cache import LRUCommentCache

logger = logging.getLogger(__name__)


class MultiLevelCommentCache:
    """マルチレベルコメントキャッシュ
    
    コメントを以下の粒度でキャッシュ:
    - L1: タイプ + 季節 + 地域 (細かい粒度)
    - L2: タイプ + 季節 (中間粒度)
    - L3: タイプのみ (粗い粒度)
    """
    
    def __init__(self, 
                 max_size_per_level: int = 100,
                 cache_ttl_minutes: int = 60,
                 max_memory_mb_per_level: float = 30):
        """初期化
        
        Args:
            max_size_per_level: 各レベルの最大キャッシュサイズ
            cache_ttl_minutes: キャッシュTTL（分）
            max_memory_mb_per_level: 各レベルの最大メモリ使用量（MB）
        """
        # 各レベルのキャッシュを作成
        self.l1_cache = LRUCommentCache(
            max_size=max_size_per_level,
            cache_ttl_minutes=cache_ttl_minutes,
            max_memory_mb=max_memory_mb_per_level
        )
        self.l2_cache = LRUCommentCache(
            max_size=max_size_per_level * 2,  # L2はより大きく
            cache_ttl_minutes=cache_ttl_minutes * 2,  # TTLも長く
            max_memory_mb=max_memory_mb_per_level * 1.5
        )
        self.l3_cache = LRUCommentCache(
            max_size=max_size_per_level * 3,  # L3は最大
            cache_ttl_minutes=cache_ttl_minutes * 3,  # TTLも最長
            max_memory_mb=max_memory_mb_per_level * 2
        )
        
        self._lock = RLock()
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    def _generate_cache_key(self, 
                           comment_type: Optional[CommentType] = None,
                           season: Optional[str] = None,
                           region: Optional[str] = None) -> tuple[str, str, str]:
        """キャッシュキーを生成
        
        Args:
            comment_type: コメントタイプ
            season: 季節
            region: 地域
            
        Returns:
            (L1キー, L2キー, L3キー) のタプル
        """
        # L3: タイプのみ
        l3_key = f"type:{comment_type.value if comment_type else 'all'}"
        
        # L2: タイプ + 季節
        l2_key = f"{l3_key}:season:{season or 'all'}"
        
        # L1: タイプ + 季節 + 地域
        l1_key = f"{l2_key}:region:{region or 'all'}"
        
        return l1_key, l2_key, l3_key
    
    def get(self, 
            comment_type: Optional[CommentType] = None,
            season: Optional[str] = None,
            region: Optional[str] = None) -> Optional[List[PastComment]]:
        """キャッシュから取得（最も具体的なレベルから検索）
        
        Args:
            comment_type: コメントタイプ
            season: 季節
            region: 地域
            
        Returns:
            キャッシュされたコメントリスト（見つからない場合はNone）
        """
        l1_key, l2_key, l3_key = self._generate_cache_key(comment_type, season, region)
        
        with self._lock:
            self._stats["total_requests"] += 1
            
            # L1キャッシュをチェック
            if region and (result := self.l1_cache.get(l1_key)):
                self._stats["l1_hits"] += 1
                logger.debug(f"L1 cache hit: {l1_key}")
                return result
            
            # L2キャッシュをチェック
            if season and (result := self.l2_cache.get(l2_key)):
                self._stats["l2_hits"] += 1
                logger.debug(f"L2 cache hit: {l2_key}")
                # 必要に応じて地域でフィルタリング
                if region:
                    filtered = self._filter_by_region(result, region)
                    # L1にも追加
                    self.l1_cache.set(l1_key, filtered)
                    return filtered
                return result
            
            # L3キャッシュをチェック
            if comment_type and (result := self.l3_cache.get(l3_key)):
                self._stats["l3_hits"] += 1
                logger.debug(f"L3 cache hit: {l3_key}")
                # 必要に応じて季節・地域でフィルタリング
                filtered = result
                if season:
                    filtered = self._filter_by_season(filtered, season)
                if region:
                    filtered = self._filter_by_region(filtered, region)
                
                # より具体的なキャッシュレベルにも追加
                if season:
                    self.l2_cache.set(l2_key, filtered)
                if region:
                    self.l1_cache.set(l1_key, filtered)
                    
                return filtered
            
            # キャッシュミス
            self._stats["misses"] += 1
            logger.debug(f"Cache miss for type:{comment_type}, season:{season}, region:{region}")
            return None
    
    def set(self, 
            comments: List[PastComment],
            comment_type: Optional[CommentType] = None,
            season: Optional[str] = None,
            region: Optional[str] = None) -> None:
        """キャッシュに設定（適切なレベルに保存）
        
        Args:
            comments: コメントリスト
            comment_type: コメントタイプ
            season: 季節
            region: 地域
        """
        l1_key, l2_key, l3_key = self._generate_cache_key(comment_type, season, region)
        
        with self._lock:
            # 最も具体的なレベルから保存
            if region:
                self.l1_cache.set(l1_key, comments)
                logger.debug(f"Cached to L1: {l1_key}")
            
            if season and not region:
                # 季節レベルのキャッシュ
                self.l2_cache.set(l2_key, comments)
                logger.debug(f"Cached to L2: {l2_key}")
            
            if comment_type and not season and not region:
                # タイプレベルのキャッシュ
                self.l3_cache.set(l3_key, comments)
                logger.debug(f"Cached to L3: {l3_key}")
    
    def invalidate(self, 
                  comment_type: Optional[CommentType] = None,
                  season: Optional[str] = None,
                  region: Optional[str] = None) -> int:
        """指定された条件のキャッシュを無効化
        
        Args:
            comment_type: コメントタイプ
            season: 季節
            region: 地域
            
        Returns:
            無効化されたエントリ数
        """
        count = 0
        
        with self._lock:
            # 最も具体的なレベルから無効化
            if region:
                l1_key, _, _ = self._generate_cache_key(comment_type, season, region)
                if self.l1_cache.invalidate(l1_key):
                    count += 1
            
            if season:
                _, l2_key, _ = self._generate_cache_key(comment_type, season, None)
                # L2の関連エントリを無効化
                for key in list(self.l2_cache._cache.keys()):
                    if key.startswith(l2_key):
                        if self.l2_cache.invalidate(key):
                            count += 1
            
            if comment_type:
                _, _, l3_key = self._generate_cache_key(comment_type, None, None)
                # L3の関連エントリを無効化
                for key in list(self.l3_cache._cache.keys()):
                    if key.startswith(l3_key):
                        if self.l3_cache.invalidate(key):
                            count += 1
        
        logger.info(f"Invalidated {count} cache entries")
        return count
    
    def _filter_by_season(self, comments: List[PastComment], season: str) -> List[PastComment]:
        """季節でフィルタリング"""
        return [c for c in comments if c.raw_data.get('season') == season]
    
    def _filter_by_region(self, comments: List[PastComment], region: str) -> List[PastComment]:
        """地域でフィルタリング"""
        return [c for c in comments if c.raw_data.get('region') == region]
    
    def clear(self) -> None:
        """全キャッシュをクリア"""
        with self._lock:
            self.l1_cache.clear()
            self.l2_cache.clear()
            self.l3_cache.clear()
            self._stats = {
                "l1_hits": 0,
                "l2_hits": 0,
                "l3_hits": 0,
                "misses": 0,
                "total_requests": 0
            }
        logger.info("Cleared all cache levels")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            total_hits = self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["l3_hits"]
            hit_rate = total_hits / self._stats["total_requests"] if self._stats["total_requests"] > 0 else 0.0
            
            return {
                "total_requests": self._stats["total_requests"],
                "total_hits": total_hits,
                "hit_rate": hit_rate,
                "l1_hits": self._stats["l1_hits"],
                "l2_hits": self._stats["l2_hits"],
                "l3_hits": self._stats["l3_hits"],
                "misses": self._stats["misses"],
                "l1_stats": self.l1_cache.get_stats(),
                "l2_stats": self.l2_cache.get_stats(),
                "l3_stats": self.l3_cache.get_stats()
            }