"""コメントのキャッシュ管理を担当するクラス"""

from __future__ import annotations
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from src.data.past_comment import PastComment, CommentType
from src.repositories.lru_comment_cache import LRUCommentCache
from src.repositories.multilevel_comment_cache import MultiLevelCommentCache

logger = logging.getLogger(__name__)


class CommentCache:
    """コメントのキャッシュを管理
    
    互換性のため既存のインターフェースを維持しながら、
    内部でLRUキャッシュとマルチレベルキャッシュを使用して効率を改善。
    """
    
    DEFAULT_CACHE_KEY = "__all_comments__"
    
    def __init__(self, cache_ttl_minutes: int = 60, max_size: int = 1000, max_memory_mb: float = 100):
        """
        Args:
            cache_ttl_minutes: キャッシュの有効期限（分）
            max_size: キャッシュに保持する最大エントリ数
            max_memory_mb: 最大メモリ使用量（MB）
        """
        # 内部でLRUキャッシュを使用
        self._lru_cache = LRUCommentCache(
            max_size=max_size,
            cache_ttl_minutes=cache_ttl_minutes,
            max_memory_mb=max_memory_mb
        )
        
        # マルチレベルキャッシュを追加
        self._multilevel_cache = MultiLevelCommentCache(
            max_size_per_level=max_size // 3,  # 各レベルで1/3ずつ割り当て
            cache_ttl_minutes=cache_ttl_minutes,
            max_memory_mb_per_level=max_memory_mb / 3
        )
        
        # 互換性のため統計情報を転送
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0
    
    def is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかを確認（互換性のため維持）"""
        return self._lru_cache.get(self.DEFAULT_CACHE_KEY) is not None
    
    def get(self, key: str | None = None) -> list[PastComment | None]:
        """キャッシュを取得（有効な場合のみ）"""
        # 互換性のため、keyが指定されない場合はデフォルトキーを使用
        cache_key = key or self.DEFAULT_CACHE_KEY
        result = self._lru_cache.get(cache_key)
        
        # 統計情報を同期
        stats = self._lru_cache.get_stats()
        self._cache_hits = stats['hits']
        self._cache_misses = stats['misses']
        self._total_requests = stats['total_requests']
        
        return result
    
    def set(self, comments: list[PastComment], key: str | None = None) -> None:
        """キャッシュを設定"""
        # 互換性のため、keyが指定されない場合はデフォルトキーを使用
        cache_key = key or self.DEFAULT_CACHE_KEY
        self._lru_cache.set(cache_key, comments)
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self._lru_cache.clear()
    
    def get_hit_rate(self) -> float:
        """キャッシュヒット率を計算"""
        return self._lru_cache.get_hit_rate()
    
    def get_stats(self) -> dict[str, Any]:
        """キャッシュの統計情報を取得"""
        return self._lru_cache.get_stats()
    
    # LRUキャッシュの追加機能を公開
    def invalidate(self, key: str) -> bool:
        """特定のキーのキャッシュを無効化"""
        return self._lru_cache.invalidate(key)
    
    def cleanup_expired(self) -> int:
        """期限切れのエントリをクリーンアップ"""
        return self._lru_cache.cleanup_expired()
    
    # マルチレベルキャッシュのメソッドを追加
    def get_by_type_season_region(self,
                                  comment_type: Optional[CommentType] = None,
                                  season: Optional[str] = None,
                                  region: Optional[str] = None) -> Optional[list[PastComment]]:
        """タイプ・季節・地域でコメントを取得（マルチレベルキャッシュ使用）
        
        Args:
            comment_type: コメントタイプ
            season: 季節
            region: 地域
            
        Returns:
            キャッシュされたコメントリスト（見つからない場合はNone）
        """
        return self._multilevel_cache.get(comment_type, season, region)
    
    def set_by_type_season_region(self,
                                 comments: list[PastComment],
                                 comment_type: Optional[CommentType] = None,
                                 season: Optional[str] = None,
                                 region: Optional[str] = None) -> None:
        """タイプ・季節・地域でコメントを設定（マルチレベルキャッシュ使用）
        
        Args:
            comments: コメントリスト
            comment_type: コメントタイプ
            season: 季節
            region: 地域
        """
        self._multilevel_cache.set(comments, comment_type, season, region)
    
    def invalidate_multilevel(self,
                            comment_type: Optional[CommentType] = None,
                            season: Optional[str] = None,
                            region: Optional[str] = None) -> int:
        """マルチレベルキャッシュの無効化
        
        Args:
            comment_type: コメントタイプ
            season: 季節
            region: 地域
            
        Returns:
            無効化されたエントリ数
        """
        return self._multilevel_cache.invalidate(comment_type, season, region)
    
    def get_multilevel_stats(self) -> dict[str, Any]:
        """マルチレベルキャッシュの統計情報を取得"""
        return self._multilevel_cache.get_stats()


class SeasonalCommentFilter:
    """季節に基づくコメントのフィルタリング"""
    
    @staticmethod
    def get_relevant_seasons(month: int) -> list[str]:
        """月から関連する季節を取得"""
        season_map = {
            (3, 4): ["春", "梅雨"],
            (5,): ["春", "梅雨", "夏"],
            (6,): ["春", "梅雨", "夏"],
            (7, 8): ["夏", "梅雨", "台風"],
            (9,): ["夏", "台風", "秋"],
            (10, 11): ["秋", "台風", "冬"],
            (12, 1, 2): ["冬", "春"]
        }
        
        for months, seasons in season_map.items():
            if month in months:
                return seasons
        
        # フォールバック
        return ["春", "夏", "秋", "冬", "梅雨", "台風"]
    
    @staticmethod
    def filter_by_season(comments: list[PastComment], seasons: list[str]) -> list[PastComment]:
        """指定された季節のコメントのみをフィルタ"""
        return [c for c in comments if c.raw_data.get('season') in seasons]
    
    @staticmethod
    def filter_by_type_and_season(
        comments: list[PastComment], 
        comment_type: str, 
        season: str, 
        limit: int | None = None
    ) -> list[PastComment]:
        """タイプと季節でフィルタリング"""
        filtered = [
            c for c in comments 
            if c.raw_data.get('season') == season and c.comment_type.value == comment_type
        ]
        
        # カウント順でソート
        filtered.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
        
        if limit:
            return filtered[:limit]
        return filtered