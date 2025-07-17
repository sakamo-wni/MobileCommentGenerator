"""CSV単一ファイルの検証"""

from __future__ import annotations
import csv
import logging
from pathlib import Path
from .base_csv_validator import BaseCSVValidator, ValidationError, ValidationResult
from .row_validator import CSVRowValidator

logger = logging.getLogger(__name__)


class CSVFileValidator(BaseCSVValidator):
    """単一CSVファイルの検証クラス"""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.row_validator = CSVRowValidator(config)
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """単一のCSVファイルを検証
        
        Args:
            file_path: CSVファイルのパス
            
        Returns:
            検証結果
        """
        errors = []
        warnings = []
        statistics = self._initialize_statistics()
        
        # ファイル存在チェック
        if not file_path.exists():
            errors.append(self._create_file_not_found_error(file_path))
            return ValidationResult(False, errors, warnings, statistics)
        
        # ファイルタイプと必須カラムの判定
        expected_column, required_columns = self._determine_file_type(file_path, warnings)
        
        # ファイル内容の検証
        try:
            self._validate_file_content(
                file_path, expected_column, required_columns,
                errors, warnings, statistics
            )
        except Exception as e:
            errors.append(self._create_read_error(file_path, e))
        
        # 統計情報の最終計算
        self._finalize_statistics(statistics)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, statistics)
    
    def _initialize_statistics(self) -> dict:
        """統計情報の初期化"""
        return {
            "total_rows": 0,
            "valid_rows": 0,
            "empty_rows": 0,
            "duplicate_rows": 0,
            "avg_comment_length": 0,
            "max_count": 0,
            "min_count": float('inf'),
            "comment_lengths": []  # 平均計算用
        }
    
    def _create_file_not_found_error(self, file_path: Path) -> ValidationError:
        """ファイル未発見エラーを作成"""
        return ValidationError(
            file_path=str(file_path),
            line_number=None,
            column=None,
            error_type="file_not_found",
            message=f"ファイルが見つかりません: {file_path}",
            severity="error"
        )
    
    def _create_read_error(self, file_path: Path, exception: Exception) -> ValidationError:
        """ファイル読み込みエラーを作成"""
        return ValidationError(
            file_path=str(file_path),
            line_number=None,
            column=None,
            error_type="read_error",
            message=f"ファイル読み込みエラー: {str(exception)}",
            severity="error"
        )
    
    def _determine_file_type(self, file_path: Path, warnings: list) -> tuple[str | None, list]:
        """ファイルタイプと必須カラムを判定"""
        if "weather_comment" in file_path.name:
            expected_column = "weather_comment"
            required_columns = self.config["validation"]["required_columns"]["weather_comment"]
        elif "advice" in file_path.name:
            expected_column = "advice"
            required_columns = self.config["validation"]["required_columns"]["advice"]
        else:
            warnings.append(ValidationError(
                file_path=str(file_path),
                line_number=None,
                column=None,
                error_type="unknown_file_type",
                message=f"ファイル名から型を判定できません: {file_path.name}",
                severity="warning"
            ))
            expected_column = None
            required_columns = ["count"]
        
        return expected_column, required_columns
    
    def _validate_file_content(self, file_path: Path, expected_column: str | None,
                              required_columns: list, errors: list, warnings: list,
                              statistics: dict) -> None:
        """ファイル内容を検証"""
        seen_comments = set()
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # ヘッダー検証
            if not self._validate_header(reader, file_path, required_columns, errors):
                return
            
            # データ行の検証
            for line_num, row in enumerate(reader, start=2):
                statistics["total_rows"] += 1
                
                # 行の検証
                row_errors = self.row_validator.validate_row(
                    row, line_num, expected_column, seen_comments
                )
                
                # エラーの分類と追加
                for error in row_errors:
                    error.file_path = str(file_path)
                    if error.severity == "error":
                        errors.append(error)
                    else:
                        warnings.append(error)
                
                # 統計情報の更新
                self._update_statistics(row, expected_column, statistics)
        
        # 重複数の計算
        if expected_column:
            statistics["duplicate_rows"] = statistics["total_rows"] - len(seen_comments)
    
    def _validate_header(self, reader: csv.DictReader, file_path: Path,
                        required_columns: list, errors: list) -> bool:
        """ヘッダーを検証"""
        if not reader.fieldnames:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=1,
                column=None,
                error_type="no_header",
                message="ヘッダー行がありません",
                severity="error"
            ))
            return False
        
        # 必須カラムチェック
        for col in required_columns:
            if col not in reader.fieldnames:
                errors.append(ValidationError(
                    file_path=str(file_path),
                    line_number=1,
                    column=col,
                    error_type="missing_column",
                    message=f"必須カラム '{col}' がありません",
                    severity="error"
                ))
        
        return True
    
    def _update_statistics(self, row: dict, expected_column: str | None,
                          statistics: dict) -> None:
        """統計情報を更新"""
        # コメント統計
        if expected_column and row.get(expected_column):
            comment = row[expected_column].strip()
            if comment:
                statistics["comment_lengths"].append(len(comment))
                statistics["valid_rows"] += 1
            else:
                statistics["empty_rows"] += 1
        
        # count値統計
        if "count" in row:
            try:
                count = int(row["count"])
                statistics["max_count"] = max(statistics["max_count"], count)
                statistics["min_count"] = min(statistics["min_count"], count)
            except ValueError:
                pass
    
    def _finalize_statistics(self, statistics: dict) -> None:
        """統計情報の最終計算"""
        # 平均コメント長の計算
        if statistics["comment_lengths"]:
            statistics["avg_comment_length"] = (
                sum(statistics["comment_lengths"]) / len(statistics["comment_lengths"])
            )
        del statistics["comment_lengths"]  # 不要な一時データを削除
        
        # min_countの調整
        if statistics["min_count"] == float('inf'):
            statistics["min_count"] = 0