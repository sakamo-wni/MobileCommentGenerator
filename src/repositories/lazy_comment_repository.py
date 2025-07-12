"""遅延読み込み対応のコメントリポジトリ

CSVファイルを必要な時だけ読み込むことで、起動時間とメモリ使用量を削減
並列読み込みに対応してパフォーマンスを向上
"""

import logging
from pathlib import Path
from typing import Optional, Union, Any
from datetime import datetime
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from src.repositories.base_repository import CommentRepositoryInterface
from src.repositories.csv_file_handler import CSVFileHandler, CommentParser
from src.data.past_comment import PastComment, CommentType
from src.utils.cache import TTLCache

logger = logging.getLogger(__name__)


class LazyCommentRepository(CommentRepositoryInterface):
    """遅延読み込み対応のコメントリポジトリ
    
    初期化時には何もロードせず、必要な時に必要な分だけCSVを読み込む
    """
    
    DEFAULT_SEASONS = ["春", "夏", "秋", "冬", "梅雨", "台風"]
    DEFAULT_COMMENT_TYPES = ["weather_comment", "advice"]
    
    def __init__(self, output_dir: str = "output", cache_ttl_minutes: int = 60,
                 seasons: Optional[list[str]] = None, 
                 comment_types: Optional[list[str]] = None,
                 max_workers: int | None = None):
        """
        Args:
            output_dir: CSVファイルが格納されているディレクトリ
            cache_ttl_minutes: キャッシュの有効期限（分）
            seasons: 対象とする季節のリスト（省略時はデフォルト値を使用）
            comment_types: 対象とするコメントタイプのリスト（省略時はデフォルト値を使用）
            max_workers: 並列処理の最大ワーカー数（Noneの場合はCPU数ベースで自動設定）
        """
        self.output_dir = Path(output_dir)
        self.SEASONS = seasons or self.DEFAULT_SEASONS
        self.COMMENT_TYPES = comment_types or self.DEFAULT_COMMENT_TYPES
        
        # 並列処理の設定
        self.max_workers = max_workers or min(os.cpu_count() or 1, 4)  # 最大4ワーカー
        
        # ファイルハンドラとパーサー
        self.file_handler = CSVFileHandler()
        self.parser = CommentParser()
        
        # 遅延読み込み用のキャッシュ（ファイル単位）
        self._file_cache = TTLCache(default_ttl=cache_ttl_minutes * 60)
        
        # 読み込み済みファイルのトラッキング
        self._loaded_files: set[str] = set()
        
        # ディレクトリの存在確認のみ実行
        self._ensure_output_dir_exists()
        
        logger.info(f"LazyCommentRepository initialized (no files loaded yet, max_workers={self.max_workers})")
    
    def _ensure_output_dir_exists(self) -> None:
        """出力ディレクトリの存在を確認し、なければ作成"""
        if not self.output_dir.exists():
            logger.warning(f"Output directory not found: {self.output_dir}, creating it...")
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_csv_file_path(self, season: str, comment_type: str) -> Path:
        """CSVファイルのパスを生成"""
        filename = f"{season}_{comment_type}_enhanced100.csv"
        return self.output_dir / filename
    
    def _get_cache_key(self, season: str, comment_type: str) -> str:
        """キャッシュキーを生成"""
        return f"{season}_{comment_type}"
    
    def _load_file_if_needed(self, season: str, comment_type: str) -> list[PastComment]:
        """必要に応じてファイルを読み込む（キャッシュ済みならキャッシュから返す）"""
        cache_key = self._get_cache_key(season, comment_type)
        
        # キャッシュから取得を試みる
        cached_comments = self._file_cache.get(cache_key)
        if cached_comments is not None:
            return cached_comments
        
        # ファイルを読み込む
        file_path = self._get_csv_file_path(season, comment_type)
        comments = self._load_comments_from_file(file_path, comment_type, season)
        
        # キャッシュに保存
        self._file_cache.set(cache_key, comments)
        self._loaded_files.add(cache_key)
        
        logger.info(f"Lazy loaded {len(comments)} {comment_type} comments for season {season}")
        return comments
    
    def _load_comments_from_file(self, file_path: Path, comment_type: str, season: str) -> list[PastComment]:
        """特定のファイルからコメントを読み込み"""
        if not file_path.exists():
            logger.debug(f"File not found: {file_path}")
            return []
        
        # ヘッダー検証
        expected_columns = ['weather_comment'] if comment_type == 'weather_comment' else ['advice']
        if not self.file_handler.validate_csv_headers(file_path, expected_columns):
            logger.warning(f"Invalid CSV headers in {file_path}, expected columns: {expected_columns}")
            return []
        
        rows = self.file_handler.read_csv_file(file_path)
        comments = []
        
        comment_type_enum = CommentType.WEATHER_COMMENT if comment_type == 'weather_comment' else CommentType.ADVICE
        
        for row in rows:
            comment = CommentParser.parse_comment_row(row, comment_type, season)
            if comment:
                comments.append(comment)
        
        return comments
    
    def get_all_comments(self) -> list[PastComment]:
        """全てのコメントを取得（並列遅延読み込み）"""
        all_comments = []
        
        # 読み込むべきファイルの組み合わせを作成
        file_combinations = [(season, comment_type) 
                           for season in self.SEASONS 
                           for comment_type in self.COMMENT_TYPES]
        
        # 並列でファイルを読み込む
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Future オブジェクトとその対応する(season, comment_type)をマッピング
            future_to_params = {
                executor.submit(self._load_file_if_needed, season, comment_type): (season, comment_type)
                for season, comment_type in file_combinations
            }
            
            # 完了したタスクから結果を収集
            for future in as_completed(future_to_params):
                try:
                    comments = future.result()
                    all_comments.extend(comments)
                except Exception as e:
                    season, comment_type = future_to_params[future]
                    logger.error(f"Error loading {comment_type} for {season}: {e}")
        
        logger.info(f"Loaded total of {len(all_comments)} comments using {self.max_workers} workers")
        return all_comments
    
    def get_comments_by_season(self, seasons: Union[str, list[str]], limit: int = 100) -> list[PastComment]:
        """指定された季節のコメントを取得（並列遅延読み込み）
        
        Args:
            seasons: 季節名または季節名のリスト
            limit: 最大取得数
        """
        # 単一の文字列が渡された場合の対応
        if isinstance(seasons, str):
            seasons = [seasons]
        
        # 有効な季節のみフィルタリング
        valid_seasons = [s for s in seasons if s in self.SEASONS]
        if not valid_seasons:
            logger.warning(f"No valid seasons found in: {seasons}")
            return []
        
        comments = []
        
        # 読み込むべきファイルの組み合わせを作成
        file_combinations = [(season, comment_type) 
                           for season in valid_seasons
                           for comment_type in self.COMMENT_TYPES]
        
        # 並列でファイルを読み込む
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_params = {
                executor.submit(self._load_file_if_needed, season, comment_type): (season, comment_type)
                for season, comment_type in file_combinations
            }
            
            for future in as_completed(future_to_params):
                try:
                    season_comments = future.result()
                    comments.extend(season_comments)
                    
                    # limit に達したら早期終了
                    if len(comments) >= limit:
                        # 残りのタスクをキャンセル
                        for f in future_to_params:
                            if not f.done():
                                f.cancel()
                        return comments[:limit]
                except Exception as e:
                    season, comment_type = future_to_params[future]
                    logger.error(f"Error loading {comment_type} for {season}: {e}")
        
        return comments[:limit]
    
    def get_comments_by_season_single(self, season: str) -> list[PastComment]:
        """特定の季節のコメントを取得（遅延読み込み）"""
        comments = []
        
        if season not in self.SEASONS:
            logger.warning(f"Unknown season: {season}")
            return comments
        
        for comment_type in self.COMMENT_TYPES:
            season_comments = self._load_file_if_needed(season, comment_type)
            comments.extend(season_comments)
        
        return comments
    
    def get_weather_comments_by_season(self, season: str) -> list[PastComment]:
        """特定の季節の天気コメントのみを取得（遅延読み込み）"""
        if season not in self.SEASONS:
            logger.warning(f"Unknown season: {season}")
            return []
        
        return self._load_file_if_needed(season, "weather_comment")
    
    def get_advice_by_season(self, season: str) -> list[PastComment]:
        """特定の季節のアドバイスのみを取得（遅延読み込み）"""
        if season not in self.SEASONS:
            logger.warning(f"Unknown season: {season}")
            return []
        
        return self._load_file_if_needed(season, "advice")
    
    def search_comments(self, **criteria) -> list[PastComment]:
        """条件に基づいてコメントを検索（必要なファイルのみ読み込み）"""
        # 季節が指定されている場合は、その季節のみを読み込む
        target_seasons = self.SEASONS
        if 'season' in criteria and criteria['season']:
            target_seasons = [criteria['season']]
        
        # コメントタイプが指定されている場合は、そのタイプのみを読み込む
        target_types = self.COMMENT_TYPES
        if 'comment_type' in criteria and criteria['comment_type']:
            if criteria['comment_type'] == CommentType.WEATHER_COMMENT:
                target_types = ["weather_comment"]
            elif criteria['comment_type'] == CommentType.ADVICE:
                target_types = ["advice"]
        
        # 必要なファイルのみを読み込んで検索
        matching_comments = []
        
        for season in target_seasons:
            for comment_type in target_types:
                comments = self._load_file_if_needed(season, comment_type)
                
                # フィルタリング
                for comment in comments:
                    if self._matches_criteria(comment, criteria):
                        matching_comments.append(comment)
        
        return matching_comments
    
    def _matches_criteria(self, comment: PastComment, criteria: dict[str, Any]) -> bool:
        """コメントが検索条件に一致するかチェック"""
        # 各条件をチェック
        if 'comment_type' in criteria and criteria['comment_type']:
            if comment.comment_type != criteria['comment_type']:
                return False
        
        if 'season' in criteria and criteria['season']:
            # raw_dataから季節情報を取得
            comment_season = comment.raw_data.get('season') if comment.raw_data else None
            if comment_season != criteria['season']:
                return False
        
        if 'location' in criteria and criteria['location']:
            if comment.location != criteria['location']:
                return False
        
        # その他の条件も同様にチェック...
        
        return True
    
    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得"""
        stats = {
            "total_seasons": len(self.SEASONS),
            "total_comment_types": len(self.COMMENT_TYPES),
            "loaded_files": len(self._loaded_files),
            "cache_stats": self._file_cache.get_stats(),
            "loaded_details": {}
        }
        
        # 読み込み済みファイルの詳細
        for cache_key in self._loaded_files:
            cached_comments = self._file_cache.get(cache_key)
            if cached_comments:
                stats["loaded_details"][cache_key] = len(cached_comments)
        
        return stats
    
    def preload_season(self, season: str):
        """特定の季節のデータを事前読み込み（オプション）"""
        if season not in self.SEASONS:
            logger.warning(f"Unknown season: {season}")
            return
        
        for comment_type in self.COMMENT_TYPES:
            self._load_file_if_needed(season, comment_type)
        
        logger.info(f"Preloaded all comment types for season: {season}")
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._file_cache.clear()
        self._loaded_files.clear()
        logger.info("Comment repository cache cleared")
    
    # 抽象メソッドの実装
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> list[PastComment]:
        """全ての利用可能なコメントを取得（遅延読み込み）"""
        all_comments = []
        comments_per_type = {}
        
        for season in self.SEASONS:
            for comment_type in self.COMMENT_TYPES:
                comments = self._load_file_if_needed(season, comment_type)
                
                # 各タイプごとに上限を適用
                key = f"{season}_{comment_type}"
                if key not in comments_per_type:
                    comments_per_type[key] = []
                
                # 上限まで追加
                remaining = max_per_season_per_type - len(comments_per_type[key])
                if remaining > 0:
                    comments_per_type[key].extend(comments[:remaining])
        
        # 全てのコメントを結合
        for comments in comments_per_type.values():
            all_comments.extend(comments)
        
        return all_comments
    
    def get_recent_comments(self, limit: int = 100) -> list[PastComment]:
        """最近のコメントを取得（遅延読み込み）"""
        # 全コメントを取得してから最新のものを返す
        all_comments = self.get_all_comments()
        
        # PastCommentにはcreated_atがないため、datetimeフィールドでソート
        # datetimeが設定されていない場合は現在時刻を使用（CSVからの読み込みの場合）
        sorted_comments = sorted(
            all_comments,
            key=lambda c: c.datetime if c.datetime else datetime.now(),
            reverse=True
        )
        
        return sorted_comments[:limit]
    
    def refresh_cache(self) -> None:
        """キャッシュをリフレッシュ"""
        self.clear_cache()