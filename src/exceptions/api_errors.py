"""API関連のエラークラス"""


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