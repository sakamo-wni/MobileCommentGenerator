"""ローカルCSVファイルからコメントデータを読み込むリポジトリ（リファクタリング版）

このモジュールは、データアクセス層を抽象化し、責務を明確に分離しています。
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.repositories.base_repository import CommentRepositoryInterface
from src.repositories.csv_file_handler import CSVFileHandler, CommentParser
from src.repositories.comment_cache import CommentCache, SeasonalCommentFilter
from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class LocalCommentRepository(CommentRepositoryInterface):
    """ローカルCSVファイルからコメントを読み込むリポジトリ"""
    
    SEASONS = ["春", "夏", "秋", "冬", "梅雨", "台風"]
    COMMENT_TYPES = ["weather_comment", "advice"]
    
    def __init__(self, output_dir: str = "output", cache_ttl_minutes: int = 60):
        """
        Args:
            output_dir: CSVファイルが格納されているディレクトリ
            cache_ttl_minutes: キャッシュの有効期限（分）
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir_exists()
        
        # 依存コンポーネントの初期化
        self.file_handler = CSVFileHandler()
        self.cache = CommentCache(cache_ttl_minutes)
        
        # 初期化時にキャッシュをロード
        self._initialize_cache()
    
    def _ensure_output_dir_exists(self) -> None:
        """出力ディレクトリの存在を確認し、なければ作成"""
        if not self.output_dir.exists():
            logger.warning(f"Output directory not found: {self.output_dir}, creating it...")
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_cache(self) -> None:
        """初期化時にキャッシュをロード"""
        try:
            comments = self._load_all_comments()
            self.cache.set(comments)
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            self.cache.clear()
    
    def _load_all_comments(self) -> List[PastComment]:
        """全季節の全コメントを読み込み"""
        all_comments = []
        
        for season in self.SEASONS:
            season_comments = self._load_season_comments(season)
            all_comments.extend(season_comments)
        
        return all_comments
    
    def _load_season_comments(self, season: str) -> List[PastComment]:
        """特定の季節のコメントを読み込み"""
        comments = []
        
        for comment_type in self.COMMENT_TYPES:
            file_path = self._get_csv_file_path(season, comment_type)
            type_comments = self._load_comments_from_file(file_path, comment_type, season)
            comments.extend(type_comments)
            
            logger.info(f"Loaded {len(type_comments)} {comment_type} comments for season {season}")
        
        return comments
    
    def _get_csv_file_path(self, season: str, comment_type: str) -> Path:
        """CSVファイルのパスを生成"""
        filename = f"{season}_{comment_type}_enhanced100.csv"
        return self.output_dir / filename
    
    def _load_comments_from_file(self, file_path: Path, comment_type: str, season: str) -> List[PastComment]:
        """特定のファイルからコメントを読み込み"""
        rows = self.file_handler.read_csv_file(file_path)
        comments = []
        
        for row in rows:
            comment = CommentParser.parse_comment_row(row, comment_type, season)
            if comment:
                comments.append(comment)
        
        return comments
    
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """全ての利用可能なコメントを取得"""
        cached_comments = self.cache.get()
        if cached_comments is None:
            logger.info("Cache miss or expired, reloading comments...")
            self.refresh_cache()
            cached_comments = self.cache.get() or []
        
        # 季節別・タイプ別に制限して返す
        filtered_comments = []
        
        for season in self.SEASONS:
            for comment_type in self.COMMENT_TYPES:
                type_comments = SeasonalCommentFilter.filter_by_type_and_season(
                    cached_comments, comment_type, season, max_per_season_per_type
                )
                filtered_comments.extend(type_comments)
        
        logger.info(f"Retrieved {len(filtered_comments)} comments for LLM selection")
        return filtered_comments
    
    def get_recent_comments(self, limit: int = 100) -> List[PastComment]:
        """現在の月に関連する季節からコメントを取得"""
        current_month = datetime.now().month
        relevant_seasons = SeasonalCommentFilter.get_relevant_seasons(current_month)
        
        logger.info(f"Current month: {current_month} → Relevant seasons: {relevant_seasons}")
        
        return self.get_comments_by_season(relevant_seasons, limit)
    
    def get_comments_by_season(self, seasons: List[str], limit: int = 100) -> List[PastComment]:
        """指定された季節のコメントを取得"""
        cached_comments = self.cache.get()
        if cached_comments is None:
            logger.info("Cache miss or expired, reloading comments...")
            self.refresh_cache()
            cached_comments = self.cache.get() or []
        
        # 指定された季節のコメントをフィルタ
        seasonal_comments = SeasonalCommentFilter.filter_by_season(cached_comments, seasons)
        
        # カウント順でソート
        seasonal_comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
        
        # より多くのコメントを返す（最低1000件）
        return_limit = max(limit, 1000)
        
        logger.info(f"Retrieved {len(seasonal_comments[:return_limit])} comments from seasons: {seasons}")
        return seasonal_comments[:return_limit]
    
    def refresh_cache(self) -> None:
        """キャッシュをリフレッシュ"""
        try:
            comments = self._load_all_comments()
            self.cache.set(comments)
            logger.info("Cache refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")
            self.cache.clear()
    
    def get_cache_stats(self) -> dict:
        """キャッシュの統計情報を取得"""
        return self.cache.get_stats()