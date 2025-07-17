"""CSV検証の基底クラスとデータ構造"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


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


class BaseCSVValidator:
    """CSV検証の基底クラス"""
    
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