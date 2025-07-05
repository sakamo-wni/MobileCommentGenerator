"""
バリデーション関連の型定義

Protocolを使用して、型の一貫性を保証
"""

from typing import Protocol, List, Optional, runtime_checkable


@runtime_checkable
class ValidationResult(Protocol):
    """
    バリデーション結果のプロトコル定義
    
    EvaluationResultオブジェクトと辞書の両方に対応する
    共通インターフェースを定義
    """
    @property
    def is_valid(self) -> bool:
        """バリデーションが成功したかどうか"""
        ...


class DictValidationResult:
    """
    辞書形式のバリデーション結果をProtocolに適合させるラッパー
    
    後方互換性のために、辞書形式のデータをValidationResultプロトコルに
    適合させる
    """
    def __init__(self, data: dict):
        self._data = data
    
    @property
    def is_valid(self) -> bool:
        return self._data.get("is_valid", True)


def ensure_validation_result(result: any) -> Optional[ValidationResult]:
    """
    様々な形式のバリデーション結果をValidationResultプロトコルに変換
    
    Args:
        result: バリデーション結果（オブジェクトまたは辞書）
    
    Returns:
        ValidationResultプロトコルに適合するオブジェクト、またはNone
    """
    if result is None:
        return None
    
    # すでにValidationResultプロトコルに適合している場合
    if isinstance(result, ValidationResult):
        return result
    
    # 辞書の場合はラッパーで包む
    if isinstance(result, dict):
        return DictValidationResult(result)
    
    # その他の場合はそのまま返す（属性アクセスが可能な場合）
    if hasattr(result, "is_valid"):
        return result
    
    return None