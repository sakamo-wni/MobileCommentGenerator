"""CSVファイル操作を担当するクラス"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.data.past_comment import PastComment, CommentType
from src.config.weather_constants import CSV_DEFAULTS

logger = logging.getLogger(__name__)


class CSVFileHandler:
    """CSVファイルの読み込みと解析を担当"""
    
    def __init__(self, encoding: str = 'utf-8-sig'):
        self.encoding = encoding
    
    def read_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """CSVファイルを読み込んで辞書のリストを返す"""
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return []
        
        rows = []
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                
                if reader.fieldnames is None:
                    logger.error(f"CSV file {file_path} has no headers")
                    return []
                
                for row_num, row in enumerate(reader, start=2):
                    row['_line_number'] = row_num
                    row['_file_path'] = file_path
                    rows.append(row)
                    
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            
        return rows
    
    def validate_csv_headers(self, file_path: Path, expected_columns: List[str]) -> bool:
        """CSVファイルのヘッダーを検証"""
        # ファイルが存在しない場合は検証しない（read_csv_fileで警告される）
        if not file_path.exists():
            return True
            
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return False
                
                for column in expected_columns:
                    if column not in reader.fieldnames:
                        logger.error(f"CSV file {file_path} missing expected column '{column}'. Found: {reader.fieldnames}")
                        return False
                return True
                
        except Exception as e:
            logger.error(f"Error validating CSV headers for {file_path}: {e}")
            return False


class CommentParser:
    """CSVデータからPastCommentオブジェクトへの変換を担当"""
    
    @staticmethod
    def parse_comment_row(row: Dict[str, Any], comment_type: str, season: str) -> Optional[PastComment]:
        """CSVの行データからPastCommentオブジェクトを生成"""
        try:
            # コメントテキストの取得
            comment_text = row.get('weather_comment') or row.get('advice', '')
            
            # 空のコメントはスキップ
            if not comment_text or comment_text.strip() == '':
                logger.debug(f"Skipping empty comment at line {row.get('_line_number', 'unknown')}")
                return None
            
            # カウント値の解析
            count = CommentParser._parse_count(row.get('count', '0'), row.get('_line_number', 0))
            
            # コメント長の検証
            comment_text = CommentParser._validate_comment_length(
                comment_text, 
                row.get('_file_path', 'unknown'),
                row.get('_line_number', 0)
            )
            
            # PastCommentオブジェクトの作成
            return PastComment(
                location=CSV_DEFAULTS['location'],  # CSVには地点情報がない
                datetime=datetime.now(),
                weather_condition=CSV_DEFAULTS['weather_condition'],  # CSVには天気条件情報がない
                comment_text=comment_text.strip(),
                comment_type=CommentType.WEATHER_COMMENT if comment_type == "weather_comment" else CommentType.ADVICE,
                raw_data={
                    'count': count,
                    'source': 'local_csv',
                    'file': Path(row.get('_file_path', '')).name,
                    'line': row.get('_line_number', 0),
                    'season': season
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing comment row: {e}, row: {row}")
            return None
    
    @staticmethod
    def _parse_count(count_str: Union[str, int, None], line_number: int) -> int:
        """カウント値を整数に変換
        
        Args:
            count_str: カウント値（文字列、整数、またはNone）
            line_number: CSVファイルの行番号（デバッグ用）
            
        Returns:
            整数に変換されたカウント値
        """
        # すでに整数の場合はそのまま返す
        if isinstance(count_str, int):
            return count_str
        
        # Noneまたは空文字列の場合は0を返す
        if count_str is None or count_str == '':
            return 0
        
        # 文字列を整数に変換
        try:
            return int(count_str)
        except ValueError:
            logger.warning(f"Invalid count value '{count_str}' at line {line_number}. Using 0.")
            return 0
    
    @staticmethod
    def _validate_comment_length(comment_text: str, file_path: str, line_number: int, max_length: int = 200) -> str:
        """コメントの長さを検証し、必要に応じて切り詰める"""
        if len(comment_text) > max_length:
            logger.warning(f"Comment too long ({len(comment_text)} chars) in {file_path} line {line_number}. Truncating.")
            return comment_text[:max_length]
        return comment_text