"""ビジネスロジック関連のエラークラス

警告: このモジュールは非推奨です。
代わりに error_types.py の統一された例外システムを使用してください。
"""

import warnings

warnings.warn(
    "business_errors モジュールは非推奨です。error_types.py の統一された例外システムを使用してください。",
    DeprecationWarning,
    stacklevel=2
)


class BusinessLogicError(Exception):
    """ビジネスロジック関連のベース例外"""
    pass


class LocationNotFoundError(BusinessLogicError):
    """指定された場所が見つからない場合の例外"""
    pass


class WeatherDataUnavailableError(BusinessLogicError):
    """天気データが利用できない場合の例外"""
    pass


class CommentGenerationError(BusinessLogicError):
    """コメント生成に失敗した場合の例外"""
    pass