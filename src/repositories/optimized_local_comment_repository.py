"""最適化されたローカルコメントリポジトリ - インデックスを使用した高速版

このモジュールは、IndexedCSVHandlerを使用して高速なコメント検索を提供します。
既存のLocalCommentRepositoryと完全な互換性を保ちます。
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.data.past_comment import PastComment, CommentType
from src.repositories.indexed_csv_handler import IndexedCSVHandler
from src.repositories.base_repository import CommentRepositoryInterface
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)


class OptimizedLocalCommentRepository(CommentRepositoryInterface):
    """インデックスを使用した高速なローカルコメントリポジトリ"""
    
    DEFAULT_SEASONS = ["春", "夏", "秋", "冬", "梅雨", "台風"]
    DEFAULT_COMMENT_TYPES = ["weather_comment", "advice"]
    
    def __init__(self, csv_directory: Optional[str] = None):
        """
        Args:
            csv_directory: CSVファイルが格納されているディレクトリパス
        """
        # 設定を読み込む
        config = load_config()
        local_csv_config = config.get('local_csv', {})
        
        # CSVディレクトリの設定
        if csv_directory:
            self.csv_directory = Path(csv_directory)
        else:
            self.csv_directory = Path(local_csv_config.get('directory', 'output'))
            
        # インデックスハンドラーの初期化
        cache_dir = Path(local_csv_config.get('cache_directory', './cache/csv_indices'))
        self.indexed_handler = IndexedCSVHandler(cache_dir=cache_dir)
        
        # 設定から季節とコメントタイプを取得
        self.seasons = local_csv_config.get('seasons', self.DEFAULT_SEASONS)
        self.comment_types = local_csv_config.get('comment_types', self.DEFAULT_COMMENT_TYPES)
        
        # 初期ロード
        self._preload_indices()
        
    def _preload_indices(self) -> None:
        """起動時にインデックスをプリロード"""
        logger.info("Preloading CSV indices...")
        loaded_count = 0
        
        for season in self.seasons:
            for comment_type_str in self.comment_types:
                file_path = self._get_csv_file_path(season, comment_type_str)
                if file_path.exists():
                    comment_type = (CommentType.WEATHER_COMMENT 
                                  if comment_type_str == "weather_comment" 
                                  else CommentType.ADVICE)
                    self.indexed_handler.load_indexed_csv(file_path, comment_type, season)
                    loaded_count += 1
                    
        logger.info(f"Preloaded {loaded_count} CSV files into index")
    
    def _get_csv_file_path(self, season: str, comment_type: str) -> Path:
        """CSVファイルのパスを生成"""
        filename = f"{season}_{comment_type}_enhanced100.csv"
        return self.csv_directory / filename
    
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """全ての利用可能なコメントを取得"""
        all_comments = []
        
        for season in self.seasons:
            season_comments = []
            
            for comment_type_str in self.comment_types:
                file_path = self._get_csv_file_path(season, comment_type_str)
                if not file_path.exists():
                    continue
                    
                comment_type = (CommentType.WEATHER_COMMENT 
                              if comment_type_str == "weather_comment" 
                              else CommentType.ADVICE)
                              
                # インデックスからロード
                comments = self.indexed_handler.load_indexed_csv(
                    file_path, comment_type, season
                )
                
                # 制限を適用
                if len(comments) > max_per_season_per_type:
                    comments = comments[:max_per_season_per_type]
                    
                season_comments.extend(comments)
                
            all_comments.extend(season_comments)
            
        logger.info(f"Loaded total {len(all_comments)} comments from all seasons")
        return all_comments
    
    def get_recent_comments(self, location: str = "", limit: int = 100, 
                          days: int = 30) -> List[PastComment]:
        """最近のコメントを取得（CSVベースなので全コメントから制限数を返す）"""
        all_comments = self.get_all_available_comments()
        return all_comments[:limit]
    
    def get_comments_by_season(self, seasons: List[str], limit: int = 100) -> List[PastComment]:
        """指定された季節のコメントを取得"""
        comments = []
        
        for season in seasons:
            if season not in self.seasons:
                continue
                
            for comment_type_str in self.comment_types:
                file_path = self._get_csv_file_path(season, comment_type_str)
                if not file_path.exists():
                    continue
                    
                comment_type = (CommentType.WEATHER_COMMENT 
                              if comment_type_str == "weather_comment" 
                              else CommentType.ADVICE)
                              
                season_comments = self.indexed_handler.load_indexed_csv(
                    file_path, comment_type, season
                )
                comments.extend(season_comments)
                
                if len(comments) >= limit:
                    return comments[:limit]
                    
        return comments
    
    def search_by_weather_condition(self, weather_condition: str, 
                                  location: Optional[str] = None) -> List[PastComment]:
        """天気条件でコメントを検索"""
        results = []
        
        for season in self.seasons:
            for comment_type_str in self.comment_types:
                file_path = self._get_csv_file_path(season, comment_type_str)
                if not file_path.exists():
                    continue
                    
                # インデックスを使った高速検索
                weather_comments = self.indexed_handler.search_by_weather(
                    file_path, weather_condition
                )
                results.extend(weather_comments)
                
        logger.info(f"Found {len(results)} comments for weather '{weather_condition}'")
        return results
    
    def get_least_used_comments(self, comment_type: Optional[CommentType] = None,
                              limit: int = 10) -> List[PastComment]:
        """使用回数の少ないコメントを取得"""
        results = []
        
        for season in self.seasons:
            for comment_type_str in self.comment_types:
                # タイプフィルター
                if comment_type:
                    if (comment_type == CommentType.WEATHER_COMMENT and 
                        comment_type_str != "weather_comment"):
                        continue
                    if (comment_type == CommentType.ADVICE and 
                        comment_type_str != "advice"):
                        continue
                        
                file_path = self._get_csv_file_path(season, comment_type_str)
                if not file_path.exists():
                    continue
                    
                # 使用回数0-5のコメントを検索
                low_usage_comments = self.indexed_handler.search_by_usage_count(
                    file_path, min_count=0, max_count=5
                )
                results.extend(low_usage_comments)
                
        # 使用回数でソート
        results.sort(key=lambda c: c.usage_count)
        return results[:limit]
    
    def refresh_cache(self) -> None:
        """キャッシュをリフレッシュ"""
        logger.info("Refreshing CSV index cache...")
        self.indexed_handler.clear_cache()
        self._preload_indices()
        logger.info("CSV index cache refreshed")
        
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        stats = {
            "total_comments": 0,
            "by_season": {},
            "by_type": {
                CommentType.WEATHER_COMMENT.value: 0,
                CommentType.ADVICE.value: 0
            },
            "indexed_files": 0
        }
        
        for season in self.seasons:
            stats["by_season"][season] = 0
            
            for comment_type_str in self.comment_types:
                file_path = self._get_csv_file_path(season, comment_type_str)
                if not file_path.exists():
                    continue
                    
                comment_type = (CommentType.WEATHER_COMMENT 
                              if comment_type_str == "weather_comment" 
                              else CommentType.ADVICE)
                              
                comments = self.indexed_handler.load_indexed_csv(
                    file_path, comment_type, season
                )
                
                count = len(comments)
                stats["total_comments"] += count
                stats["by_season"][season] += count
                stats["by_type"][comment_type.value] += count
                stats["indexed_files"] += 1
                
        return stats