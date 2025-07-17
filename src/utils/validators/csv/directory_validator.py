"""CSVディレクトリの検証"""

from __future__ import annotations
import logging
from pathlib import Path
from .base_csv_validator import BaseCSVValidator, ValidationResult
from .file_validator import CSVFileValidator

logger = logging.getLogger(__name__)


class CSVDirectoryValidator(BaseCSVValidator):
    """ディレクトリ内の全CSVファイルを検証するクラス"""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.file_validator = CSVFileValidator(config)
    
    def validate_directory(self, directory: Path) -> dict[str, ValidationResult]:
        """ディレクトリ内の全CSVファイルを検証
        
        Args:
            directory: 検証するディレクトリ
            
        Returns:
            ファイル名をキーとする検証結果の辞書
        """
        results = {}
        
        # ディレクトリの存在確認
        if not directory.exists():
            logger.error(f"ディレクトリが存在しません: {directory}")
            return results
        
        if not directory.is_dir():
            logger.error(f"指定されたパスはディレクトリではありません: {directory}")
            return results
        
        # CSVファイルの検証
        csv_files = list(directory.glob("*.csv"))
        
        if not csv_files:
            logger.warning(f"CSVファイルが見つかりません: {directory}")
            return results
        
        logger.info(f"{len(csv_files)}個のCSVファイルを検証します")
        
        for csv_file in sorted(csv_files):
            logger.info(f"検証中: {csv_file}")
            results[csv_file.name] = self.file_validator.validate_file(csv_file)
            
            # 簡易進捗表示
            result = results[csv_file.name]
            status = "✓" if result.is_valid else "✗"
            logger.info(f"  {status} {csv_file.name}: "
                       f"エラー{len(result.errors)}件, 警告{len(result.warnings)}件")
        
        return results
    
    def get_summary_statistics(self, results: dict[str, ValidationResult]) -> dict:
        """検証結果の集計統計を取得
        
        Args:
            results: validate_directoryの結果
            
        Returns:
            集計統計情報
        """
        summary = {
            "total_files": len(results),
            "valid_files": sum(1 for r in results.values() if r.is_valid),
            "invalid_files": sum(1 for r in results.values() if not r.is_valid),
            "total_errors": sum(len(r.errors) for r in results.values()),
            "total_warnings": sum(len(r.warnings) for r in results.values()),
            "total_rows": sum(r.statistics["total_rows"] for r in results.values()),
            "total_valid_rows": sum(r.statistics["valid_rows"] for r in results.values()),
            "error_types": {},
            "warning_types": {}
        }
        
        # エラータイプ別集計
        for result in results.values():
            for error in result.errors:
                error_type = error.error_type
                summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
            
            for warning in result.warnings:
                warning_type = warning.error_type
                summary["warning_types"][warning_type] = summary["warning_types"].get(warning_type, 0) + 1
        
        return summary