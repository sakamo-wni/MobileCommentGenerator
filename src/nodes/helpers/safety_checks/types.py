"""コメント安全性チェック用の型定義"""

from typing import NamedTuple


class CheckResult(NamedTuple):
    """安全性チェック結果を表すデータ型
    
    Attributes:
        is_inappropriate: 不適切な表現が見つかったかどうか
        pattern_found: 見つかった不適切なパターン
        inappropriate_patterns: チェック対象の不適切パターンリスト
    """
    is_inappropriate: bool
    pattern_found: str
    inappropriate_patterns: list[str]