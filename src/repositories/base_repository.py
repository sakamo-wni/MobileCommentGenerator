"""リポジトリの基底クラスとインターフェース定義"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from src.data.past_comment import PastComment


class CommentRepositoryInterface(ABC):
    """コメントリポジトリのインターフェース"""
    
    @abstractmethod
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """全ての利用可能なコメントを取得"""
        pass
    
    @abstractmethod
    def get_recent_comments(self, limit: int = 100) -> List[PastComment]:
        """最近のコメントを取得"""
        pass
    
    @abstractmethod
    def get_comments_by_season(self, seasons: List[str], limit: int = 100) -> List[PastComment]:
        """指定された季節のコメントを取得"""
        pass
    
    @abstractmethod
    def refresh_cache(self) -> None:
        """キャッシュをリフレッシュ"""
        pass