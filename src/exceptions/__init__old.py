"""カスタム例外クラス定義"""

# API関連のエラー
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

# データ処理関連のエラー
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

# ビジネスロジック関連のエラー
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

# ファイル I/O 関連のエラー
class FileIOError(Exception):
    """ファイル I/O 関連のベース例外"""
    pass

class ConfigurationError(Exception):
    """設定関連のエラー"""
    pass