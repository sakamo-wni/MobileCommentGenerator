"""統一されたエラーハンドリング"""

import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from functools import wraps
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ErrorResponse:
    """エラーレスポンスの統一フォーマット"""
    success: bool = False
    error_type: str = ""
    error_message: str = ""
    error_details: Optional[Dict[str, Any]] = None
    user_message: str = ""
    hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "success": self.success,
            "error": self.error_message
        }
        if self.error_details:
            result["details"] = self.error_details
        if self.hint:
            result["hint"] = self.hint
        return result


class AppError(Exception):
    """アプリケーション共通エラー基底クラス"""
    def __init__(self, message: str, error_type: str = "AppError", hint: Optional[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.hint = hint


class APIKeyError(AppError):
    """APIキー関連のエラー"""
    def __init__(self, provider: str, message: Optional[str] = None):
        default_message = f"{provider}のAPIキーが設定されていません"
        hint = f"サイドバーの「APIキー設定」から{provider}のAPIキーを設定してください"
        super().__init__(message or default_message, "APIKeyError", hint)
        self.provider = provider


class WeatherAPIError(AppError):
    """天気API関連のエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        hint = "WXTECH_API_KEY環境変数を確認してください"
        super().__init__(message, "WeatherAPIError", hint)
        self.status_code = status_code


class LocationError(AppError):
    """地点関連のエラー"""
    def __init__(self, location: str, message: Optional[str] = None):
        default_message = f"地点 '{location}' が見つかりません"
        hint = "地点名を確認して、正しい地点を選択してください"
        super().__init__(message or default_message, "LocationError", hint)
        self.location = location


class DataStorageError(AppError):
    """データストレージ関連のエラー"""
    def __init__(self, message: str, operation: Optional[str] = None):
        hint = "output/ディレクトリに必要なCSVファイルが存在することを確認してください"
        super().__init__(message, "DataStorageError", hint)
        self.operation = operation


class GenerationError(AppError):
    """コメント生成関連のエラー"""
    def __init__(self, message: str, location: Optional[str] = None):
        super().__init__(message, "GenerationError")
        self.location = location


class ErrorHandler:
    """統一されたエラーハンドラー"""
    
    @staticmethod
    def handle_error(error: Exception) -> ErrorResponse:
        """エラーを処理してErrorResponseを返す"""
        logger.error(f"Error occurred: {type(error).__name__}: {str(error)}")
        logger.debug(traceback.format_exc())
        
        # AppErrorの場合
        if isinstance(error, AppError):
            return ErrorResponse(
                error_type=error.error_type,
                error_message=str(error),
                user_message=str(error),
                hint=error.hint
            )
        
        # 特定のエラータイプの処理
        error_message = str(error)
        
        # APIキーエラーの検出
        if any(key in error_message for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]):
            provider = "OpenAI" if "OPENAI" in error_message else "Gemini" if "GEMINI" in error_message else "Anthropic"
            return ErrorHandler.handle_error(APIKeyError(provider))
        
        # データストレージエラーの検出
        if "FileNotFoundError" in error_message or "CSV" in error_message or "output/" in error_message:
            return ErrorHandler.handle_error(DataStorageError("データファイルの読み込みに失敗しました"))
        
        # 天気APIエラーの検出
        if "WXTECH" in error_message:
            return ErrorHandler.handle_error(WeatherAPIError(error_message))
        
        # 天気関連エラーの詳細を保持
        if "weather" in error_message.lower() or "天気" in error_message or "気象" in error_message:
            return ErrorResponse(
                error_type="WeatherError",
                error_message=error_message,
                user_message=error_message,
                hint="WXTECH_API_KEY環境変数を確認してください"
            )
        
        # その他のエラー
        return ErrorResponse(
            error_type=type(error).__name__,
            error_message=error_message,
            user_message=f"エラーが発生しました: {error_message}"
        )
    
    @staticmethod
    def create_error_result(location: str, error: Union[str, Exception]) -> Dict[str, Any]:
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


def with_error_handling(default_return=None, reraise: bool = False):
    """エラーハンドリングデコレーター"""
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = ErrorHandler.handle_error(e)
                logger.error(f"Error in {func.__name__}: {error_response.error_message}")
                
                if reraise:
                    raise
                
                # デフォルト値が辞書の場合はエラー情報を含める
                if isinstance(default_return, dict):
                    return {**default_return, **error_response.to_dict()}
                
                return default_return
        
        return wrapper
    return decorator


def safe_api_call(api_func: Callable[..., T], *args, **kwargs) -> Union[T, ErrorResponse]:
    """API呼び出しの安全なラッパー"""
    try:
        return api_func(*args, **kwargs)
    except Exception as e:
        return ErrorHandler.handle_error(e)


# エラーメッセージのテンプレート
ERROR_MESSAGES = {
    "api_key_missing": "🔐 {provider}のAPIキーが設定されていません",
    "weather_api_error": "☁️ 天気予報データの取得に失敗しました",
    "data_storage_error": "🗄️ データ読み込みエラー: コメントデータファイルにアクセスできません",
    "location_not_found": "📍 地点エラー: {location}が見つかりません",
    "generation_failed": "⚠️ コメント生成に失敗しました: {reason}",
    "timeout_error": "⏱️ タイムアウト: 処理に時間がかかりすぎています",
    "validation_error": "❌ 入力エラー: {details}"
}


def get_error_message(error_key: str, **kwargs) -> str:
    """エラーメッセージテンプレートから整形されたメッセージを取得"""
    template = ERROR_MESSAGES.get(error_key, "⚠️ エラーが発生しました")
    try:
        return template.format(**kwargs)
    except KeyError:
        return template