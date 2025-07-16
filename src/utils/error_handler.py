"""統一されたエラーハンドリング"""

from __future__ import annotations
import logging
from typing import Any, TypeVar
from functools import wraps
from dataclasses import dataclass
import traceback

from ..exceptions.error_types import (
    ErrorType, ErrorMessages, AppException,
    WeatherFetchError, DataAccessError, LLMError, 
    ValidationError, ConfigError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ErrorResponse:
    """エラーレスポンスの統一フォーマット"""
    success: bool = False
    error_type: str = ""
    error_message: str = ""
    error_details: dict[str, Any | None] = None
    user_message: str = ""
    hint: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        result: dict[str, Any] = {
            "success": self.success,
            "error": self.error_message
        }
        if self.error_details:
            result["details"] = self.error_details
        if self.hint:
            result["hint"] = self.hint
        return result


# Legacy AppError for backward compatibility
class AppError(AppException):
    """アプリケーション共通エラー基底クラス (Legacy)"""
    def __init__(self, message: str, error_type: str = "AppError", hint: str | None = None):
        # Map legacy error type to new ErrorType
        error_type_enum = ErrorType.UNKNOWN_ERROR
        if error_type == "APIKeyError":
            error_type_enum = ErrorType.MISSING_CREDENTIAL
        elif error_type == "WeatherAPIError":
            error_type_enum = ErrorType.WEATHER_FETCH
        elif error_type == "LocationError":
            error_type_enum = ErrorType.VALIDATION_ERROR
        elif error_type == "DataStorageError":
            error_type_enum = ErrorType.DATA_ACCESS
        elif error_type == "GenerationError":
            error_type_enum = ErrorType.LLM_ERROR
            
        super().__init__(error_type_enum, message)
        self.hint = hint


# Legacy error classes removed - use AppException instead


class ErrorHandler:
    """統一されたエラーハンドラー"""
    
    @staticmethod
    def handle_error(error: Exception, lang: str = "ja") -> ErrorResponse:
        """エラーを処理してErrorResponseを返す"""
        logger.error(f"Error occurred: {type(error).__name__}: {str(error)}")
        logger.debug(traceback.format_exc())
        
        # AppException (新しいエラータイプ) の場合
        if isinstance(error, AppException):
            error_dict = error.to_dict()
            return ErrorResponse(
                error_type=error_dict["error_type"],
                error_message=error_dict["message"],
                user_message=error_dict["message"],
                error_details=error_dict.get("details"),
                hint=getattr(error, "hint", None)
            )
        
        # Legacy AppError の場合（AppExceptionを継承しているため、実際にはこのコードには到達しない）
        # if isinstance(error, AppError):
        #     return ErrorResponse(
        #         error_type=error.error_type,
        #         error_message=str(error),
        #         user_message=str(error),
        #         hint=error.hint
        #     )
        
        # 特定のエラータイプの処理
        error_message = str(error)
        
        # APIキーエラーの検出
        if any(key in error_message for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]):
            details = {"provider": "OpenAI" if "OPENAI" in error_message else "Gemini" if "GEMINI" in error_message else "Anthropic"}
            return ErrorHandler.handle_error(ConfigError(details=details), lang)
        
        # データストレージエラーの検出
        if "FileNotFoundError" in error_message or "CSV" in error_message or "output/" in error_message:
            return ErrorHandler.handle_error(DataAccessError(), lang)
        
        # 天気APIエラーの検出
        if "WXTECH" in error_message:
            return ErrorHandler.handle_error(WeatherFetchError(message=error_message), lang)
        
        # 天気関連エラーの詳細を保持
        if "weather" in error_message.lower() or "天気" in error_message or "気象" in error_message:
            weather_error = WeatherFetchError(message=error_message)
            return ErrorHandler.handle_error(weather_error, lang)
        
        # その他のエラー
        unknown_error = AppException(ErrorType.UNKNOWN_ERROR, message=error_message, lang=lang)
        return ErrorResponse(
            error_type=ErrorType.UNKNOWN_ERROR.value,
            error_message=error_message,
            user_message=unknown_error.message
        )
    
    @staticmethod
    def create_error_result(location: str, error: str | Exception) -> dict[str, Any]:
        """エラー結果の統一フォーマットを作成"""
        if isinstance(error, Exception):
            error_response = ErrorHandler.handle_error(error)
            error_message = error_response.error_message
        else:
            error_message = error
        
        return {
            'location': location,
            'result': None,
            'success': False,
            'comment': '',
            'error': error_message
        }