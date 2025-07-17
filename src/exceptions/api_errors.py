"""API関連のエラークラス

警告: このモジュールは非推奨です。
代わりに error_types.py の統一された例外システムを使用してください。
"""

import warnings

warnings.warn(
    "api_errors モジュールは非推奨です。error_types.py の統一された例外システムを使用してください。",
    DeprecationWarning,
    stacklevel=2
)


class APIError(Exception):
    """API呼び出し関連のベース例外"""
    pass


class APIKeyError(APIError):
    """APIキーが無効または不足している場合の例外"""
    pass


class RateLimitError(APIError):
    """APIレート制限に達した場合の例外"""
    pass


class NetworkError(APIError):
    """ネットワーク接続に問題がある場合の例外"""
    pass


class APIResponseError(APIError):
    """API応答が無効または不正な場合の例外"""
    pass


class APITimeoutError(APIError):
    """APIリクエストがタイムアウトした場合の例外"""
    pass