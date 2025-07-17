"""カスタム例外クラス定義

例外クラスはカテゴリーごとに別々のモジュールに整理されています：
- api_errors: API関連のエラー
- data_errors: データ処理関連のエラー
- business_errors: ビジネスロジック関連のエラー
- system_errors: システム関連のエラー
"""

# API関連のエラー
from .api_errors import (
    APIError,
    APIKeyError,
    RateLimitError,
    NetworkError,
    APIResponseError,
    APITimeoutError
)

# データ処理関連のエラー
from .data_errors import (
    DataError,
    DataParsingError,
    DataValidationError,
    MissingDataError
)

# ビジネスロジック関連のエラー
from .business_errors import (
    BusinessLogicError,
    LocationNotFoundError,
    WeatherDataUnavailableError,
    CommentGenerationError
)

# システム関連のエラー
from .system_errors import (
    FileIOError,
    ConfigurationError
)

__all__ = [
    # API関連
    'APIError',
    'APIKeyError',
    'RateLimitError',
    'NetworkError',
    'APIResponseError',
    'APITimeoutError',
    # データ処理関連
    'DataError',
    'DataParsingError',
    'DataValidationError',
    'MissingDataError',
    # ビジネスロジック関連
    'BusinessLogicError',
    'LocationNotFoundError',
    'WeatherDataUnavailableError',
    'CommentGenerationError',
    # システム関連
    'FileIOError',
    'ConfigurationError'
]