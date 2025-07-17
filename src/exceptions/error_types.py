"""Standardized error types and error handling for the application"""

from __future__ import annotations
from enum import Enum
from typing import Any

class ErrorType(Enum):
    """Standardized error types for consistent error handling"""
    
    # Data access errors
    WEATHER_FETCH = "weather_fetch"
    DATA_ACCESS = "data_access"
    CACHE_ERROR = "cache_error"
    
    # Processing errors
    LLM_ERROR = "llm_error"
    VALIDATION_ERROR = "validation_error"
    PARSING_ERROR = "parsing_error"
    
    # Configuration errors
    CONFIG_ERROR = "config_error"
    MISSING_CREDENTIAL = "missing_credential"
    
    # Network errors
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    API_ERROR = "api_error"
    
    # System errors
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"
    
    # Additional error types for migration
    RATE_LIMIT_ERROR = "rate_limit_error"
    API_RESPONSE_ERROR = "api_response_error"
    FILE_IO_ERROR = "file_io_error"
    LOCATION_NOT_FOUND = "location_not_found"
    COMMENT_GENERATION_ERROR = "comment_generation_error"
    MISSING_DATA_ERROR = "missing_data_error"

class ErrorMessages:
    """Internationalized error messages"""
    
    _messages: dict[ErrorType, dict[str, str]] = {
        ErrorType.WEATHER_FETCH: {
            "ja": "天気データの取得エラー",
            "en": "Weather data fetch error"
        },
        ErrorType.DATA_ACCESS: {
            "ja": "データアクセスエラー",
            "en": "Data access error"
        },
        ErrorType.CACHE_ERROR: {
            "ja": "キャッシュエラー",
            "en": "Cache error"
        },
        ErrorType.LLM_ERROR: {
            "ja": "AI処理エラー",
            "en": "AI processing error"
        },
        ErrorType.VALIDATION_ERROR: {
            "ja": "検証エラー",
            "en": "Validation error"
        },
        ErrorType.PARSING_ERROR: {
            "ja": "データ解析エラー",
            "en": "Data parsing error"
        },
        ErrorType.CONFIG_ERROR: {
            "ja": "設定エラー",
            "en": "Configuration error"
        },
        ErrorType.MISSING_CREDENTIAL: {
            "ja": "認証情報が見つかりません",
            "en": "Missing credentials"
        },
        ErrorType.NETWORK_ERROR: {
            "ja": "ネットワークエラー",
            "en": "Network error"
        },
        ErrorType.TIMEOUT_ERROR: {
            "ja": "タイムアウトエラー",
            "en": "Timeout error"
        },
        ErrorType.API_ERROR: {
            "ja": "APIエラー",
            "en": "API error"
        },
        ErrorType.SYSTEM_ERROR: {
            "ja": "システムエラー",
            "en": "System error"
        },
        ErrorType.UNKNOWN_ERROR: {
            "ja": "不明なエラー",
            "en": "Unknown error"
        },
        ErrorType.RATE_LIMIT_ERROR: {
            "ja": "レート制限エラー",
            "en": "Rate limit error"
        },
        ErrorType.API_RESPONSE_ERROR: {
            "ja": "API応答エラー",
            "en": "API response error"
        },
        ErrorType.FILE_IO_ERROR: {
            "ja": "ファイル入出力エラー",
            "en": "File I/O error"
        },
        ErrorType.LOCATION_NOT_FOUND: {
            "ja": "場所が見つかりません",
            "en": "Location not found"
        },
        ErrorType.COMMENT_GENERATION_ERROR: {
            "ja": "コメント生成エラー",
            "en": "Comment generation error"
        },
        ErrorType.MISSING_DATA_ERROR: {
            "ja": "データが見つかりません",
            "en": "Missing data error"
        }
    }
    
    @classmethod
    def get_message(cls, error_type: ErrorType, lang: str = "ja") -> str:
        """Get error message in specified language
        
        Args:
            error_type: Type of error
            lang: Language code ("ja" or "en")
            
        Returns:
            Localized error message
        """
        if error_type not in cls._messages:
            return cls._messages[ErrorType.UNKNOWN_ERROR].get(lang, "Unknown error")
        
        return cls._messages[error_type].get(lang, cls._messages[error_type]["en"])

class AppException(Exception):
    """Base application exception with error type and details"""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str | None = None,
        details: dict[str, Any | None] = None,
        lang: str = "ja"
    ):
        self.error_type = error_type
        self.details = details or {}
        self.lang = lang
        
        # Use custom message or default localized message
        if message:
            self.message = message
        else:
            self.message = ErrorMessages.get_message(error_type, lang)
        
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details
        }

# Specific exception classes
class WeatherFetchError(AppException):
    """Error fetching weather data"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.WEATHER_FETCH, message, details)

class DataAccessError(AppException):
    """Error accessing data (S3, local files, etc.)"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.DATA_ACCESS, message, details)

class LLMError(AppException):
    """Error in LLM processing"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.LLM_ERROR, message, details)

class ValidationError(AppException):
    """Data validation error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.VALIDATION_ERROR, message, details)

class ConfigError(AppException):
    """Configuration error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.CONFIG_ERROR, message, details)

# Additional exception classes for migration compatibility
class RateLimitError(AppException):
    """Rate limit error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.RATE_LIMIT_ERROR, message, details)

class APIResponseError(AppException):
    """API response error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.API_RESPONSE_ERROR, message, details)

class FileIOError(AppException):
    """File I/O error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.FILE_IO_ERROR, message, details)

class LocationNotFoundError(AppException):
    """Location not found error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.LOCATION_NOT_FOUND, message, details)

class CommentGenerationError(AppException):
    """Comment generation error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.COMMENT_GENERATION_ERROR, message, details)

class MissingDataError(AppException):
    """Missing data error"""
    def __init__(self, message: str | None = None, details: dict[str, Any | None] = None):
        super().__init__(ErrorType.MISSING_DATA_ERROR, message, details)

# Aliases for backward compatibility
ConfigurationError = ConfigError
NetworkError = AppException  # Will use base with NETWORK_ERROR type