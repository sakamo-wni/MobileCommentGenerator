"""最適化されたコメントリポジトリ - クエリベースのキャッシュを実装

季節、タイプ、制限数ごとに個別にキャッシュすることで、
効率的なメモリ使用と高速なアクセスを実現。
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.local_comment_repository import LocalCommentRepository
from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class OptimizedCommentRepository(LocalCommentRepository):
    """クエリベースのキャッシュを使用する最適化されたリポジトリ"""
    
    def _generate_cache_key(self, seasons: List[str], limit: Optional[int] = None) -> str:
        """キャッシュキーを生成"""
        season_part = "_".join(sorted(seasons))
        limit_part = f"_limit{limit}" if limit else ""
        return f"comments_{season_part}{limit_part}"
    
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """全ての利用可能なコメントを取得（キャッシュ最適化版）"""
        if self.use_index:
            # インデックス版はすでに最適化済み
            return super().get_all_available_comments(max_per_season_per_type)
        
        # キャッシュキーを生成
        cache_key = f"all_available_{max_per_season_per_type}"
        
        # キャッシュから取得を試みる
        cached_comments = self.cache.get(cache_key)
        if cached_comments is not None:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_comments
        
        # キャッシュミスの場合は通常の処理
        logger.info(f"Cache miss for key: {cache_key}, loading from files...")
        
        # 全コメントを取得（デフォルトキーでキャッシュされている可能性）
        all_comments = self.cache.get()
        if all_comments is None:
            logger.info("Base cache miss, loading all comments...")
            self.refresh_cache()
            all_comments = self.cache.get() or []
        
        # 季節別・タイプ別に制限して返す
        filtered_comments = []
        
        for season in self.SEASONS:
            for comment_type in self.COMMENT_TYPES:
                from src.repositories.comment_cache import SeasonalCommentFilter
                type_comments = SeasonalCommentFilter.filter_by_type_and_season(
                    all_comments, comment_type, season, max_per_season_per_type
                )
                filtered_comments.extend(type_comments)
        
        # 結果をキャッシュ
        self.cache.set(filtered_comments, cache_key)
        
        logger.info(f"Retrieved and cached {len(filtered_comments)} comments")
        return filtered_comments
    
    def get_comments_by_season(self, seasons: List[str], limit: int = 100) -> List[PastComment]:
        """指定された季節のコメントを取得（キャッシュ最適化版）"""
        if self.use_index:
            # インデックス版はすでに最適化済み
            return super().get_comments_by_season(seasons, limit)
        
        # キャッシュキーを生成
        cache_key = self._generate_cache_key(seasons, limit)
        
        # キャッシュから取得を試みる
        cached_comments = self.cache.get(cache_key)
        if cached_comments is not None:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_comments
        
        # キャッシュミスの場合は通常の処理
        logger.info(f"Cache miss for key: {cache_key}, loading from base cache...")
        
        # 全コメントを取得
        all_comments = self.cache.get()
        if all_comments is None:
            logger.info("Base cache miss, loading all comments...")
            self.refresh_cache()
            all_comments = self.cache.get() or []
        
        # フィルタリング
        from src.repositories.comment_cache import SeasonalCommentFilter
        filtered_comments = SeasonalCommentFilter.filter_by_season(all_comments, seasons)
        
        # 制限を適用
        if limit and len(filtered_comments) > limit:
            filtered_comments = filtered_comments[:limit]
        
        # 結果をキャッシュ
        self.cache.set(filtered_comments, cache_key)
        
        logger.info(f"Retrieved and cached {len(filtered_comments)} comments for seasons: {seasons}")
        return filtered_comments
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得"""
        stats = self.cache.get_stats()
        
        # 追加の統計情報
        if 'keys' in stats:
            stats['query_cache_count'] = len([k for k in stats['keys'] if k != '__all_comments__'])
            stats['unique_queries'] = stats['query_cache_count']
        
        return stats