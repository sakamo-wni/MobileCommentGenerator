"""ローカルCSVファイルからコメントデータを読み込むリポジトリ

このモジュールは、S3ではなくローカルのCSVファイルから過去コメントを読み込みます。
CSVファイルは output/ ディレクトリに季節別・タイプ別に保存されています。
"""

import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from src.data.past_comment import PastComment, CommentType
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class LocalCommentRepository:
    """ローカルCSVファイルからコメントを読み込む"""
    
    def __init__(self, output_dir: str = "output"):
        """初期化処理
        
        Args:
            output_dir: CSVファイルが格納されているディレクトリ
        """
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            logger.warning(f"Output directory not found: {output_dir}, creating it...")
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # キャッシュを初期化時に読み込み
        self._comment_cache = None
        self._cache_loaded = False
        self._load_cache()
    
    def _read_csv_comments(self, file_path: Path, comment_type: str) -> List[PastComment]:
        """Read comments from a CSV file and convert to PastComment objects."""
        comments = []
        
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return comments
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # CSVヘッダーの検証
                if reader.fieldnames is None:
                    logger.error(f"CSV file {file_path} has no headers")
                    return comments
                
                expected_column = 'weather_comment' if comment_type == "weather_comment" else 'advice'
                if expected_column not in reader.fieldnames:
                    logger.error(f"CSV file {file_path} missing expected column '{expected_column}'. Found columns: {reader.fieldnames}")
                    return comments
                
                if 'count' not in reader.fieldnames:
                    logger.warning(f"CSV file {file_path} missing 'count' column. Using default value 0.")
                
                for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is line 1)
                    try:
                        # Get the comment text (first column, which varies by type)
                        comment_text = row.get('weather_comment') or row.get('advice', '')
                        
                        # Validate and parse count
                        count_str = row.get('count', '0')
                        try:
                            count = int(count_str) if count_str else 0
                        except ValueError:
                            logger.warning(f"Invalid count value '{count_str}' in {file_path} line {row_num}. Using 0.")
                            count = 0
                        
                        # Skip empty comments
                        if not comment_text or comment_text.strip() == '':
                            logger.debug(f"Skipping empty comment in {file_path} line {row_num}")
                            continue
                        
                        # Validate comment length
                        if len(comment_text) > 200:
                            logger.warning(f"Comment too long ({len(comment_text)} chars) in {file_path} line {row_num}. Truncating.")
                            comment_text = comment_text[:200]
                        
                        comment = PastComment(
                            location="全国",  # CSV doesn't have location info
                            datetime=datetime.now(),  # CSV doesn't have datetime info
                            weather_condition="不明",  # CSV doesn't have weather condition
                            comment_text=comment_text.strip(),
                            comment_type=CommentType.WEATHER_COMMENT if comment_type == "weather_comment" else CommentType.ADVICE,
                            raw_data={
                                'count': count,
                                'source': 'local_csv',
                                'file': file_path.name,
                                'line': row_num
                            }
                        )
                        comments.append(comment)
                    
                    except Exception as e:
                        logger.error(f"Error processing row {row_num} in {file_path}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
        
        return comments
    
    def _load_cache(self):
        """初期化時に全コメントをキャッシュに読み込み"""
        try:
            logger.info("Loading comment cache...")
            self._comment_cache = self._load_all_comments()
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._comment_cache)} comments into cache")
        except Exception as e:
            logger.error(f"Failed to load comment cache: {e}")
            self._comment_cache = []
            self._cache_loaded = False
    
    def _load_all_comments(self) -> List[PastComment]:
        """全季節の全コメントを読み込み"""
        all_comments = []
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        
        for season in seasons:
            # Read weather comments for this season (using enhanced100.csv)
            weather_comment_file = self.output_dir / f"{season}_weather_comment_enhanced100.csv"
            weather_comments = self._read_csv_comments(weather_comment_file, "weather_comment")
            
            # Add season info to metadata
            for comment in weather_comments:
                comment.raw_data['season'] = season
            all_comments.extend(weather_comments)
            
            # Read advice comments for this season (using enhanced100.csv)
            advice_file = self.output_dir / f"{season}_advice_enhanced100.csv"
            advice_comments = self._read_csv_comments(advice_file, "advice")
            
            # Add season info to metadata
            for comment in advice_comments:
                comment.raw_data['season'] = season
            all_comments.extend(advice_comments)
        
        return all_comments
    
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """Get all available comments from all seasons for LLM to choose from."""
        if self._comment_cache is None:
            logger.warning("Comment cache not initialized, loading now...")
            self._load_cache()
        
        # キャッシュから季節別・タイプ別に制限して返す
        filtered_comments = []
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        
        for season in seasons:
            weather_comments = [c for c in (self._comment_cache or [])
                                if c.raw_data.get('season') == season and c.comment_type.value == 'weather_comment']
            advice_comments = [c for c in (self._comment_cache or [])
                               if c.raw_data.get('season') == season and c.comment_type.value == 'advice']
            
            filtered_comments.extend(weather_comments[:max_per_season_per_type])
            filtered_comments.extend(advice_comments[:max_per_season_per_type])
        
        logger.info(f"Retrieved {len(filtered_comments)} comments from cache for LLM selection")
        return filtered_comments
    
    def get_recent_comments(self, limit: int = 100) -> List[PastComment]:
        """現在の月に関連する季節からコメントを取得してLLMに選択させる"""
        from datetime import datetime
        
        current_month = datetime.now().month
        relevant_seasons = self._get_relevant_seasons(current_month)
        
        logger.info(f"現在月: {current_month}月 → 関連季節: {relevant_seasons}")
        
        # 関連する季節からコメントを取得
        comments = self._get_comments_from_seasons(relevant_seasons, limit)
        
        logger.info(f"季節別コメント取得完了: {len(comments)}件")
        return comments
    
    def _get_relevant_seasons(self, month: int) -> list[str]:
        """現在の月から関連する季節を取得"""
        if month in [3, 4]:
            return ["春", "梅雨"]  # 春〜梅雨前
        elif month == 5:
            return ["春", "梅雨", "夏"]  # 春〜初夏
        elif month == 6:
            return ["春", "梅雨", "夏"]  # 梅雨メイン + 前後
        elif month in [7, 8]:
            return ["夏", "梅雨", "台風"]  # 夏メイン + 台風可能性
        elif month == 9:
            return ["夏", "台風", "秋"]  # 台風〜秋
        elif month in [10, 11]:
            return ["秋", "台風", "冬"]  # 秋〜初冬
        elif month in [12, 1, 2]:
            return ["冬", "春"]  # 冬〜春準備
        else:
            return ["春", "夏", "秋", "冬", "梅雨", "台風"]  # フォールバック
    
    def _get_comments_from_seasons(self, seasons: list[str], total_limit: int) -> list[PastComment]:
        """指定された季節からコメントを取得"""
        if self._comment_cache is None:
            logger.warning("Comment cache not initialized, loading now...")
            self._load_cache()
        
        all_comments = []
        
        # 各季節から100件ずつ取得（天気コメント50件 + アドバイス50件）
        for season in seasons:
            weather_comments = [c for c in (self._comment_cache or [])
                                if c.raw_data.get('season') == season and c.comment_type.value == 'weather_comment']
            advice_comments = [c for c in (self._comment_cache or [])
                               if c.raw_data.get('season') == season and c.comment_type.value == 'advice']
            
            # 各タイプから50件ずつ（人気順）
            weather_comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
            advice_comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
            
            season_comments = weather_comments[:50] + advice_comments[:50]
            all_comments.extend(season_comments)
            
            logger.info(f"季節「{season}」: 天気{len(weather_comments[:50])}件 + アドバイス{len(advice_comments[:50])}件")
        
        # 全体を人気順でソートして制限
        all_comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
        
        return all_comments[:total_limit]
