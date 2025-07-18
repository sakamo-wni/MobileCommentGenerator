"""CSVファイル検証ユーティリティ（リファクタリング版）"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

from .validators.csv import (
    ValidationResult,
    CSVFileValidator,
    CSVDirectoryValidator,
    CSVReportGenerator
)

logger = logging.getLogger(__name__)


class CSVValidator:
    """CSVファイルの検証クラス（リファクタリング版）
    
    モジュール化されたバリデータを使用して、CSVファイルの検証を行います。
    """
    
    def __init__(self, config: dict[str, Any | None] = None):
        """初期化
        
        Args:
            config: 検証設定（local_csv_config.yamlから読み込み）
        """
        self.config = config
        self.file_validator = CSVFileValidator(config)
        self.directory_validator = CSVDirectoryValidator(config)
        self.report_generator = CSVReportGenerator()
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """単一のCSVファイルを検証
        
        Args:
            file_path: CSVファイルのパス
            
        Returns:
            検証結果
        """
        return self.file_validator.validate_file(file_path)
    
    def validate_directory(self, directory: Path) -> dict[str, ValidationResult]:
        """ディレクトリ内の全CSVファイルを検証
        
        Args:
            directory: 検証するディレクトリ
            
        Returns:
            ファイル名をキーとする検証結果の辞書
        """
        return self.directory_validator.validate_directory(directory)
    
    def generate_report(self, results: dict[str, ValidationResult]) -> str:
        """検証結果のレポートを生成
        
        Args:
            results: validate_directoryの結果
            
        Returns:
            レポート文字列
        """
        return self.report_generator.generate_report(results)


def main():
    """コマンドライン実行用"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSVファイル検証ツール")
    parser.add_argument("directory", help="検証するディレクトリ")
    parser.add_argument("--output", "-o", help="レポート出力ファイル")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログを表示")
    
    args = parser.parse_args()
    
    # ロギング設定
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 検証実行
    validator = CSVValidator()
    directory = Path(args.directory)
    
    logger.info(f"検証開始: {directory}")
    results = validator.validate_directory(directory)
    
    # レポート生成
    report = validator.generate_report(results)
    logger.info(report)
    
    # レポート保存
    if args.output:
        output_path = Path(args.output)
        validator.report_generator.save_report(report, output_path)
        logger.info(f"\nレポートを {output_path} に保存しました")
    
    # 終了コード
    has_errors = any(not result.is_valid for result in results.values())
    return 1 if has_errors else 0


if __name__ == "__main__":
    exit(main())