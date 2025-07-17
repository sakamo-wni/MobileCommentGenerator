"""CSV行データの検証"""

from __future__ import annotations
import logging
from .base_csv_validator import BaseCSVValidator, ValidationError

logger = logging.getLogger(__name__)


class CSVRowValidator(BaseCSVValidator):
    """CSV行データの検証クラス"""
    
    def validate_row(self, row: dict[str, str], line_num: int, 
                    expected_column: str | None, 
                    seen_comments: set) -> list[ValidationError]:
        """行データを検証
        
        Args:
            row: 検証する行データ
            line_num: 行番号
            expected_column: 期待されるコメントカラム名
            seen_comments: 既に見たコメントのセット（重複チェック用）
            
        Returns:
            検証エラーのリスト
        """
        errors = []
        
        # コメントテキストの検証
        if expected_column:
            errors.extend(self._validate_comment(
                row, line_num, expected_column, seen_comments
            ))
        
        # count値の検証
        if "count" in row:
            errors.extend(self._validate_count(row, line_num))
        
        return errors
    
    def _validate_comment(self, row: dict[str, str], line_num: int,
                         expected_column: str, seen_comments: set) -> list[ValidationError]:
        """コメントテキストを検証"""
        errors = []
        config = self.config["validation"]
        quality_config = self.config["data_quality"]
        
        comment = row.get(expected_column, "").strip()
        
        # 空チェック
        if not comment and quality_config["remove_empty"]:
            errors.append(ValidationError(
                file_path="",
                line_number=line_num,
                column=expected_column,
                error_type="empty_comment",
                message="空のコメント",
                severity="warning"
            ))
        
        if comment:
            # 長さチェック
            errors.extend(self._check_comment_length(
                comment, line_num, expected_column, config
            ))
            
            # NGワードチェック
            errors.extend(self._check_ng_words(
                comment, line_num, expected_column, quality_config
            ))
            
            # 重複チェック
            if comment in seen_comments and quality_config["remove_duplicates"]:
                errors.append(ValidationError(
                    file_path="",
                    line_number=line_num,
                    column=expected_column,
                    error_type="duplicate",
                    message="重複するコメント",
                    severity="warning"
                ))
            seen_comments.add(comment)
        
        return errors
    
    def _check_comment_length(self, comment: str, line_num: int,
                             column: str, config: dict) -> list[ValidationError]:
        """コメント長をチェック"""
        errors = []
        
        if len(comment) > config["max_comment_length"]:
            errors.append(ValidationError(
                file_path="",
                line_number=line_num,
                column=column,
                error_type="comment_too_long",
                message=f"コメントが長すぎます ({len(comment)}文字)",
                severity="error"
            ))
        elif len(comment) > config["warning_length"]:
            errors.append(ValidationError(
                file_path="",
                line_number=line_num,
                column=column,
                error_type="comment_long",
                message=f"コメントが長めです ({len(comment)}文字)",
                severity="warning"
            ))
        
        return errors
    
    def _check_ng_words(self, comment: str, line_num: int,
                       column: str, quality_config: dict) -> list[ValidationError]:
        """NGワードをチェック"""
        errors = []
        
        for ng_word in quality_config["ng_words"]:
            if ng_word in comment:
                errors.append(ValidationError(
                    file_path="",
                    line_number=line_num,
                    column=column,
                    error_type="ng_word",
                    message=f"NGワード '{ng_word}' が含まれています",
                    severity="error"
                ))
        
        return errors
    
    def _validate_count(self, row: dict[str, str], line_num: int) -> list[ValidationError]:
        """count値を検証"""
        errors = []
        config = self.config["validation"]
        count_str = row["count"].strip()
        
        if count_str:
            try:
                count = int(count_str)
                count_range = config["count_range"]
                if count < count_range["min"] or count > count_range["max"]:
                    errors.append(ValidationError(
                        file_path="",
                        line_number=line_num,
                        column="count",
                        error_type="count_out_of_range",
                        message=f"count値が範囲外です: {count}",
                        severity="error"
                    ))
            except ValueError:
                errors.append(ValidationError(
                    file_path="",
                    line_number=line_num,
                    column="count",
                    error_type="invalid_count",
                    message=f"count値が数値ではありません: '{count_str}'",
                    severity="error"
                ))
        else:
            errors.append(ValidationError(
                file_path="",
                line_number=line_num,
                column="count",
                error_type="empty_count",
                message="count値が空です",
                severity="warning"
            ))
        
        return errors