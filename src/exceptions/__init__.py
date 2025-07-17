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
import warnings

class APIError(AppException):
    """非推奨: AppException(ErrorType.API_ERROR)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "APIError is deprecated. Use AppException with ErrorType.API_ERROR. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.API_ERROR, message, details)

class APIKeyError(AppException):
    """非推奨: AppException(ErrorType.MISSING_CREDENTIAL)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "APIKeyError is deprecated. Use AppException with ErrorType.MISSING_CREDENTIAL. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.MISSING_CREDENTIAL, message, details)

class NetworkError(AppException):
    """非推奨: AppException(ErrorType.NETWORK_ERROR)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "NetworkError is deprecated. Use AppException with ErrorType.NETWORK_ERROR. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.NETWORK_ERROR, message, details)

class APITimeoutError(AppException):
    """非推奨: AppException(ErrorType.TIMEOUT_ERROR)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "APITimeoutError is deprecated. Use AppException with ErrorType.TIMEOUT_ERROR. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.TIMEOUT_ERROR, message, details)

# DataErrorはDataAccessErrorのエイリアス
DataError = DataAccessError

class DataParsingError(AppException):
    """非推奨: AppException(ErrorType.PARSING_ERROR)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "DataParsingError is deprecated. Use AppException with ErrorType.PARSING_ERROR. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.PARSING_ERROR, message, details)

# DataValidationErrorはValidationErrorのエイリアス
DataValidationError = ValidationError

class BusinessLogicError(AppException):
    """非推奨: AppException(ErrorType.SYSTEM_ERROR)を使用してください"""
    def __init__(self, message=None, details=None):
        warnings.warn(
            "BusinessLogicError is deprecated. Use AppException with ErrorType.SYSTEM_ERROR. "
            "Will be removed in version 2.0.0",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(ErrorType.SYSTEM_ERROR, message, details)

# WeatherDataUnavailableErrorはWeatherFetchErrorのエイリアス
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