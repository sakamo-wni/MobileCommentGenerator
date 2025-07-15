"""CSVファイル検証ユーティリティ"""

import csv
import logging
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """検証エラー情報"""
    file_path: str
    line_number: int | None
    column: str | None
    error_type: str
    message: str
    severity: str  # "error", "warning", "info"


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    statistics: dict[str, Any]


class CSVValidator:
    """CSVファイルの検証クラス"""
    
    def __init__(self, config: dict[str, Any | None] = None):
        """初期化
        
        Args:
            config: 検証設定（local_csv_config.yamlから読み込み）
        """
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            "validation": {
                "max_comment_length": 200,
                "min_comment_length": 1,
                "count_range": {"min": 0, "max": 1000000},
                "warning_length": 100,
                "required_columns": {
                    "weather_comment": ["weather_comment", "count"],
                    "advice": ["advice", "count"]
                }
            },
            "data_quality": {
                "remove_duplicates": True,
                "remove_empty": True,
                "normalize_special_chars": True,
                "ng_words": ["エラー", "NULL", "undefined", "???"]
            }
        }
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """単一のCSVファイルを検証
        
        Args:
            file_path: CSVファイルのパス
            
        Returns:
            検証結果
        """
        errors = []
        warnings = []
        statistics = {
            "total_rows": 0,
            "valid_rows": 0,
            "empty_rows": 0,
            "duplicate_rows": 0,
            "avg_comment_length": 0,
            "max_count": 0,
            "min_count": float('inf')
        }
        
        if not file_path.exists():
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=None,
                column=None,
                error_type="file_not_found",
                message=f"ファイルが見つかりません: {file_path}",
                severity="error"
            ))
            return ValidationResult(False, errors, warnings, statistics)
        
        # ファイル名から期待されるカラムを判定
        expected_column = None
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
            required_columns = ["count"]
        
        seen_comments = set()
        comment_lengths = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # ヘッダー検証
                if not reader.fieldnames:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        line_number=1,
                        column=None,
                        error_type="no_header",
                        message="ヘッダー行がありません",
                        severity="error"
                    ))
                    return ValidationResult(False, errors, warnings, statistics)
                
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
                
                # データ行の検証
                for line_num, row in enumerate(reader, start=2):
                    statistics["total_rows"] += 1
                    row_errors = self._validate_row(
                        row, line_num, expected_column, seen_comments
                    )
                    
                    for error in row_errors:
                        error.file_path = str(file_path)
                        if error.severity == "error":
                            errors.append(error)
                        else:
                            warnings.append(error)
                    
                    # 統計情報の更新
                    if expected_column and row.get(expected_column):
                        comment = row[expected_column].strip()
                        if comment:
                            comment_lengths.append(len(comment))
                            statistics["valid_rows"] += 1
                        else:
                            statistics["empty_rows"] += 1
                    
                    # count値の統計
                    if "count" in row:
                        try:
                            count = int(row["count"])
                            statistics["max_count"] = max(statistics["max_count"], count)
                            statistics["min_count"] = min(statistics["min_count"], count)
                        except ValueError:
                            pass
        
        except Exception as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                line_number=None,
                column=None,
                error_type="read_error",
                message=f"ファイル読み込みエラー: {str(e)}",
                severity="error"
            ))
        
        # 統計情報の計算
        if comment_lengths:
            statistics["avg_comment_length"] = sum(comment_lengths) / len(comment_lengths)
        if statistics["min_count"] == float('inf'):
            statistics["min_count"] = 0
        statistics["duplicate_rows"] = len(seen_comments) - statistics["valid_rows"]
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, statistics)
    
    def _validate_row(self, row: dict[str, str], line_num: int, 
                     expected_column: str | None, 
                     seen_comments: set) -> list[ValidationError]:
        """行データを検証"""
        errors = []
        config = self.config["validation"]
        quality_config = self.config["data_quality"]
        
        # コメントテキストの検証
        if expected_column:
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
            
            # 長さチェック
            if comment:
                if len(comment) > config["max_comment_length"]:
                    errors.append(ValidationError(
                        file_path="",
                        line_number=line_num,
                        column=expected_column,
                        error_type="comment_too_long",
                        message=f"コメントが長すぎます ({len(comment)}文字)",
                        severity="error"
                    ))
                elif len(comment) > config["warning_length"]:
                    errors.append(ValidationError(
                        file_path="",
                        line_number=line_num,
                        column=expected_column,
                        error_type="comment_long",
                        message=f"コメントが長めです ({len(comment)}文字)",
                        severity="warning"
                    ))
                
                # NGワードチェック
                for ng_word in quality_config["ng_words"]:
                    if ng_word in comment:
                        errors.append(ValidationError(
                            file_path="",
                            line_number=line_num,
                            column=expected_column,
                            error_type="ng_word",
                            message=f"NGワード '{ng_word}' が含まれています",
                            severity="error"
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
        
        # count値の検証
        if "count" in row:
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
    
    def validate_directory(self, directory: Path) -> dict[str, ValidationResult]:
        """ディレクトリ内の全CSVファイルを検証
        
        Args:
            directory: 検証するディレクトリ
            
        Returns:
            ファイル名をキーとする検証結果の辞書
        """
        results = {}
        
        for csv_file in directory.glob("*.csv"):
            logger.info(f"検証中: {csv_file}")
            results[csv_file.name] = self.validate_file(csv_file)
        
        return results
    
    def generate_report(self, results: dict[str, ValidationResult]) -> str:
        """検証結果のレポートを生成
        
        Args:
            results: validate_directoryの結果
            
        Returns:
            レポート文字列
        """
        report = []
        report.append("=" * 80)
        report.append("CSV検証レポート")
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        total_files = len(results)
        valid_files = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        # サマリー
        report.append("## サマリー")
        report.append(f"- 検証ファイル数: {total_files}")
        report.append(f"- 正常ファイル数: {valid_files}")
        report.append(f"- エラー総数: {total_errors}")
        report.append(f"- 警告総数: {total_warnings}")
        report.append("")
        
        # ファイル別詳細
        for filename, result in sorted(results.items()):
            report.append(f"## {filename}")
            report.append(f"- ステータス: {'✓ 正常' if result.is_valid else '✗ エラー'}")
            report.append(f"- 総行数: {result.statistics['total_rows']}")
            report.append(f"- 有効行数: {result.statistics['valid_rows']}")
            report.append(f"- 平均コメント長: {result.statistics['avg_comment_length']:.1f}")
            report.append(f"- count値範囲: {result.statistics['min_count']} - {result.statistics['max_count']}")
            
            if result.errors:
                report.append("\n### エラー:")
                for error in result.errors[:10]:  # 最初の10件のみ表示
                    report.append(f"  - 行{error.line_number}: {error.message}")
                if len(result.errors) > 10:
                    report.append(f"  ... 他{len(result.errors) - 10}件のエラー")
            
            if result.warnings:
                report.append("\n### 警告:")
                for warning in result.warnings[:5]:  # 最初の5件のみ表示
                    report.append(f"  - 行{warning.line_number}: {warning.message}")
                if len(result.warnings) > 5:
                    report.append(f"  ... 他{len(result.warnings) - 5}件の警告")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """コマンドライン実行用"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSVファイル検証ツール")
    parser.add_argument("directory", help="検証するディレクトリ")
    parser.add_argument("--output", "-o", help="レポート出力ファイル")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログを表示")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    validator = CSVValidator()
    results = validator.validate_directory(Path(args.directory))
    report = validator.generate_report(results)
    
    print(report)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nレポートを {args.output} に保存しました")


if __name__ == "__main__":
    main()