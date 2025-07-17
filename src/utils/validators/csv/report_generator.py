"""CSV検証レポート生成"""

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from .base_csv_validator import ValidationResult

logger = logging.getLogger(__name__)


class CSVReportGenerator:
    """CSV検証レポートを生成するクラス"""
    
    def __init__(self, max_errors_shown: int = 10, max_warnings_shown: int = 5):
        """初期化
        
        Args:
            max_errors_shown: レポートに表示する最大エラー数
            max_warnings_shown: レポートに表示する最大警告数
        """
        self.max_errors_shown = max_errors_shown
        self.max_warnings_shown = max_warnings_shown
    
    def generate_report(self, results: dict[str, ValidationResult],
                       directory_path: str = None) -> str:
        """検証結果のレポートを生成
        
        Args:
            results: validate_directoryの結果
            directory_path: 検証したディレクトリのパス（オプション）
            
        Returns:
            レポート文字列
        """
        report = []
        
        # ヘッダー
        report.extend(self._generate_header(directory_path))
        
        # サマリー
        report.extend(self._generate_summary(results))
        
        # ファイル別詳細
        report.extend(self._generate_file_details(results))
        
        # エラー・警告の統計
        report.extend(self._generate_error_statistics(results))
        
        return "\n".join(report)
    
    def _generate_header(self, directory_path: str = None) -> list[str]:
        """レポートヘッダーを生成"""
        header = []
        header.append("=" * 80)
        header.append("CSV検証レポート")
        if directory_path:
            header.append(f"対象ディレクトリ: {directory_path}")
        header.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        header.append("=" * 80)
        header.append("")
        return header
    
    def _generate_summary(self, results: dict[str, ValidationResult]) -> list[str]:
        """サマリーセクションを生成"""
        summary = []
        
        total_files = len(results)
        valid_files = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        total_rows = sum(r.statistics["total_rows"] for r in results.values())
        
        summary.append("## サマリー")
        summary.append(f"- 検証ファイル数: {total_files}")
        summary.append(f"- 正常ファイル数: {valid_files} ({valid_files/total_files*100:.1f}%)")
        summary.append(f"- 異常ファイル数: {total_files - valid_files}")
        summary.append(f"- エラー総数: {total_errors}")
        summary.append(f"- 警告総数: {total_warnings}")
        summary.append(f"- 総行数: {total_rows:,}")
        summary.append("")
        
        return summary
    
    def _generate_file_details(self, results: dict[str, ValidationResult]) -> list[str]:
        """ファイル別詳細セクションを生成"""
        details = []
        details.append("## ファイル別詳細")
        details.append("")
        
        # エラーのあるファイルを先に表示
        sorted_results = sorted(
            results.items(),
            key=lambda x: (x[1].is_valid, x[0])
        )
        
        for filename, result in sorted_results:
            details.extend(self._generate_single_file_detail(filename, result))
        
        return details
    
    def _generate_single_file_detail(self, filename: str,
                                   result: ValidationResult) -> list[str]:
        """単一ファイルの詳細を生成"""
        detail = []
        
        status_icon = "✓" if result.is_valid else "✗"
        status_text = "正常" if result.is_valid else "エラー"
        
        detail.append(f"### {filename}")
        detail.append(f"- ステータス: {status_icon} {status_text}")
        detail.append(f"- 総行数: {result.statistics['total_rows']:,}")
        detail.append(f"- 有効行数: {result.statistics['valid_rows']:,}")
        
        if result.statistics['avg_comment_length'] > 0:
            detail.append(f"- 平均コメント長: {result.statistics['avg_comment_length']:.1f}文字")
        
        if result.statistics['max_count'] > 0:
            detail.append(f"- count値範囲: {result.statistics['min_count']:,} - "
                         f"{result.statistics['max_count']:,}")
        
        # エラー表示
        if result.errors:
            detail.append("")
            detail.append("#### エラー:")
            for i, error in enumerate(result.errors[:self.max_errors_shown]):
                location = f"行{error.line_number}" if error.line_number else "ファイル全体"
                detail.append(f"  {i+1}. [{location}] {error.message}")
            
            if len(result.errors) > self.max_errors_shown:
                detail.append(f"  ... 他{len(result.errors) - self.max_errors_shown}件のエラー")
        
        # 警告表示
        if result.warnings:
            detail.append("")
            detail.append("#### 警告:")
            for i, warning in enumerate(result.warnings[:self.max_warnings_shown]):
                location = f"行{warning.line_number}" if warning.line_number else "ファイル全体"
                detail.append(f"  {i+1}. [{location}] {warning.message}")
            
            if len(result.warnings) > self.max_warnings_shown:
                detail.append(f"  ... 他{len(result.warnings) - self.max_warnings_shown}件の警告")
        
        detail.append("")
        return detail
    
    def _generate_error_statistics(self, results: dict[str, ValidationResult]) -> list[str]:
        """エラー・警告の統計セクションを生成"""
        stats = []
        
        # エラータイプ別集計
        error_types = {}
        warning_types = {}
        
        for result in results.values():
            for error in result.errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            for warning in result.warnings:
                warning_types[warning.error_type] = warning_types.get(warning.error_type, 0) + 1
        
        if error_types or warning_types:
            stats.append("## エラー・警告タイプ別統計")
            stats.append("")
        
        if error_types:
            stats.append("### エラータイプ")
            for error_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
                stats.append(f"- {error_type}: {count}件")
            stats.append("")
        
        if warning_types:
            stats.append("### 警告タイプ")
            for warning_type, count in sorted(warning_types.items(), key=lambda x: -x[1]):
                stats.append(f"- {warning_type}: {count}件")
            stats.append("")
        
        return stats
    
    def save_report(self, report: str, output_path: Path) -> None:
        """レポートをファイルに保存
        
        Args:
            report: レポート文字列
            output_path: 出力ファイルパス
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"レポートを保存しました: {output_path}")
        except Exception as e:
            logger.error(f"レポート保存エラー: {e}")
            raise