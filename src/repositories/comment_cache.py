"""コメントのキャッシュ管理を担当するクラス"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class CommentCache:
    """コメントのキャッシュを管理"""
    
    def __init__(self, cache_ttl_minutes: int = 60):
        """
        Args:
            cache_ttl_minutes: キャッシュの有効期限（分）
        """
        self._cache: Optional[List[PastComment]] = None
        self._cache_loaded_at: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
    
    def is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかを確認"""
        if self._cache is None or self._cache_loaded_at is None:
            return False
        
        elapsed = datetime.now() - self._cache_loaded_at
        return elapsed < self._cache_ttl
    
    def get(self) -> Optional[List[PastComment]]:
        """キャッシュを取得（有効な場合のみ）"""
        if self.is_cache_valid():
            return self._cache
        return None
    
    def set(self, comments: List[PastComment]) -> None:
        """キャッシュを設定"""
        self._cache = comments
        self._cache_loaded_at = datetime.now()
        logger.info(f"Cache updated with {len(comments)} comments")
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self._cache = None
        self._cache_loaded_at = None
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得"""
        return {
            'is_valid': self.is_cache_valid(),
            'size': len(self._cache) if self._cache else 0,
            'loaded_at': self._cache_loaded_at.isoformat() if self._cache_loaded_at else None,
            'ttl_minutes': self._cache_ttl.total_seconds() / 60
        }


class SeasonalCommentFilter:
    """季節に基づくコメントのフィルタリング"""
    
    @staticmethod
    def get_relevant_seasons(month: int) -> List[str]:
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
    def filter_by_season(comments: List[PastComment], seasons: List[str]) -> List[PastComment]:
        """指定された季節のコメントのみをフィルタ"""
        return [c for c in comments if c.raw_data.get('season') in seasons]
    
    @staticmethod
    def filter_by_type_and_season(
        comments: List[PastComment], 
        comment_type: str, 
        season: str, 
        limit: Optional[int] = None
    ) -> List[PastComment]:
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