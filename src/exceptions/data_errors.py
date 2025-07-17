"""データ処理関連のエラークラス

警告: このモジュールは非推奨です。
代わりに error_types.py の統一された例外システムを使用してください。
"""

import warnings

warnings.warn(
    "data_errors モジュールは非推奨です。error_types.py の統一された例外システムを使用してください。",
    DeprecationWarning,
    stacklevel=2
)


class DataError(Exception):
    """データ処理関連のベース例外"""
    pass


class DataParsingError(DataError):
    """JSON/CSV解析に失敗した場合の例外"""
    pass


class DataValidationError(DataError):
    """データ検証に失敗した場合の例外"""
    pass


class MissingDataError(DataError):
    """必要なデータが見つからない場合の例外"""
    pass