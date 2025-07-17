"""カスタム例外クラス定義

統一された例外システムを使用します。
すべての例外はAppExceptionベースで、国際化サポートが含まれています。
"""

# 統一された例外システムからインポート
from .error_types import (
    # Base exceptions
    AppException,
    ErrorType,
    
    # Specific exceptions
    WeatherFetchError,
    DataAccessError,
    LLMError,
    ValidationError,
    ConfigError,
    RateLimitError,
    APIResponseError,
    FileIOError,
    LocationNotFoundError,
    CommentGenerationError,
    MissingDataError,
    
    # Backward compatibility aliases
    ConfigurationError,
)

# 旧システムからの移行用エイリアス（非推奨）
# これらは将来のバージョンで削除される予定です
APIError = AppException  # ErrorType.API_ERRORを使用
APIKeyError = AppException  # ErrorType.MISSING_CREDENTIALを使用
NetworkError = AppException  # ErrorType.NETWORK_ERRORを使用
APITimeoutError = AppException  # ErrorType.TIMEOUT_ERRORを使用
DataError = DataAccessError
DataParsingError = AppException  # ErrorType.PARSING_ERRORを使用
DataValidationError = ValidationError
BusinessLogicError = AppException  # ErrorType.SYSTEM_ERRORを使用
WeatherDataUnavailableError = WeatherFetchError

__all__ = [
    # Base classes
    'AppException',
    'ErrorType',
    
    # Main exceptions
    'WeatherFetchError',
    'DataAccessError',
    'LLMError',
    'ValidationError',
    'ConfigError',
    'ConfigurationError',
    'RateLimitError',
    'APIResponseError',
    'FileIOError',
    'LocationNotFoundError',
    'CommentGenerationError',
    'MissingDataError',
    
    # Deprecated (for backward compatibility)
    'APIError',
    'APIKeyError',
    'NetworkError',
    'APITimeoutError',
    'DataError',
    'DataParsingError',
    'DataValidationError',
    'BusinessLogicError',
    'WeatherDataUnavailableError',
]