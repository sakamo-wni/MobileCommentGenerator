"""統一された例外システムのテスト"""

import pytest
from src.exceptions import (
    AppException,
    ErrorType,
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
)


class TestAppException:
    """AppException基底クラスのテスト"""
    
    def test_app_exception_basic(self):
        """基本的な例外生成のテスト"""
        error = AppException(ErrorType.SYSTEM_ERROR, "テストエラー")
        assert error.error_type == ErrorType.SYSTEM_ERROR
        assert str(error) == "テストエラー"
        assert error.details == {}  # デフォルトは空の辞書
    
    def test_app_exception_with_details(self):
        """詳細情報付き例外のテスト"""
        details = {"key": "value", "code": 123}
        error = AppException(ErrorType.API_ERROR, "APIエラー", details)
        assert error.error_type == ErrorType.API_ERROR
        assert str(error) == "APIエラー"
        assert error.details == details
    
    def test_app_exception_to_dict(self):
        """辞書変換のテスト"""
        error = AppException(ErrorType.VALIDATION_ERROR, "検証エラー", {"field": "email"})
        result = error.to_dict()
        
        assert result["error_type"] == "validation_error"
        assert result["message"] == "検証エラー"
        assert result["details"] == {"field": "email"}
    
    def test_app_exception_to_dict_english(self):
        """英語での辞書変換のテスト"""
        # langパラメータはコンストラクタで指定
        error = AppException(ErrorType.NETWORK_ERROR, None, None, lang="en")
        result = error.to_dict()
        
        assert result["error_type"] == "network_error"
        assert "Network" in result["message"]  # 英語メッセージが含まれることを確認


class TestSpecificExceptions:
    """個別の例外クラスのテスト"""
    
    def test_weather_fetch_error(self):
        """WeatherFetchErrorのテスト"""
        error = WeatherFetchError("天気データの取得に失敗")
        assert error.error_type == ErrorType.WEATHER_FETCH
        assert str(error) == "天気データの取得に失敗"
    
    def test_data_access_error(self):
        """DataAccessErrorのテスト"""
        error = DataAccessError("データアクセスエラー")
        assert error.error_type == ErrorType.DATA_ACCESS
        assert str(error) == "データアクセスエラー"
    
    def test_llm_error(self):
        """LLMErrorのテスト"""
        error = LLMError("LLM呼び出しエラー")
        assert error.error_type == ErrorType.LLM_ERROR
        assert str(error) == "LLM呼び出しエラー"
    
    def test_validation_error(self):
        """ValidationErrorのテスト"""
        error = ValidationError("検証エラー", {"field": "temperature", "value": -300})
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert str(error) == "検証エラー"
        assert error.details["field"] == "temperature"
    
    def test_config_error(self):
        """ConfigErrorのテスト"""
        error = ConfigError("設定エラー")
        assert error.error_type == ErrorType.CONFIG_ERROR
        assert str(error) == "設定エラー"
    
    def test_rate_limit_error(self):
        """RateLimitErrorのテスト"""
        error = RateLimitError("レート制限エラー", {"retry_after": 60})
        assert error.error_type == ErrorType.RATE_LIMIT_ERROR
        assert str(error) == "レート制限エラー"
        assert error.details["retry_after"] == 60
    
    def test_api_response_error(self):
        """APIResponseErrorのテスト"""
        error = APIResponseError("API応答エラー", {"status_code": 500})
        assert error.error_type == ErrorType.API_RESPONSE_ERROR
        assert str(error) == "API応答エラー"
        assert error.details["status_code"] == 500
    
    def test_file_io_error(self):
        """FileIOErrorのテスト"""
        error = FileIOError("ファイルI/Oエラー", {"path": "/tmp/test.txt"})
        assert error.error_type == ErrorType.FILE_IO_ERROR
        assert str(error) == "ファイルI/Oエラー"
        assert error.details["path"] == "/tmp/test.txt"
    
    def test_location_not_found_error(self):
        """LocationNotFoundErrorのテスト"""
        error = LocationNotFoundError("場所が見つかりません", {"location": "不明な場所"})
        assert error.error_type == ErrorType.LOCATION_NOT_FOUND
        assert str(error) == "場所が見つかりません"
        assert error.details["location"] == "不明な場所"
    
    def test_comment_generation_error(self):
        """CommentGenerationErrorのテスト"""
        error = CommentGenerationError("コメント生成エラー")
        assert error.error_type == ErrorType.COMMENT_GENERATION_ERROR
        assert str(error) == "コメント生成エラー"
    
    def test_missing_data_error(self):
        """MissingDataErrorのテスト"""
        error = MissingDataError("必要なデータがありません", {"fields": ["temperature", "humidity"]})
        assert error.error_type == ErrorType.MISSING_DATA_ERROR
        assert str(error) == "必要なデータがありません"
        assert error.details["fields"] == ["temperature", "humidity"]


class TestDeprecatedAliases:
    """非推奨エイリアスのテスト"""
    
    def test_deprecated_api_error(self):
        """非推奨のAPIErrorエイリアスのテスト"""
        from src.exceptions import APIError
        
        with pytest.warns(DeprecationWarning, match="APIError is deprecated"):
            error = APIError("テストエラー")
        
        assert error.error_type == ErrorType.API_ERROR
        assert str(error) == "テストエラー"
    
    def test_deprecated_data_parsing_error(self):
        """非推奨のDataParsingErrorエイリアスのテスト"""
        from src.exceptions import DataParsingError
        
        with pytest.warns(DeprecationWarning, match="DataParsingError is deprecated"):
            error = DataParsingError("解析エラー")
        
        assert error.error_type == ErrorType.PARSING_ERROR
        assert str(error) == "解析エラー"
    
    def test_deprecated_business_logic_error(self):
        """非推奨のBusinessLogicErrorエイリアスのテスト"""
        from src.exceptions import BusinessLogicError
        
        with pytest.warns(DeprecationWarning, match="BusinessLogicError is deprecated"):
            error = BusinessLogicError("ビジネスロジックエラー")
        
        assert error.error_type == ErrorType.SYSTEM_ERROR
        assert str(error) == "ビジネスロジックエラー"


class TestInternationalization:
    """国際化機能のテスト"""
    
    def test_japanese_error_messages(self):
        """日本語エラーメッセージのテスト"""
        error = AppException(ErrorType.WEATHER_FETCH, lang="ja")
        result = error.to_dict()
        
        assert "天気データ" in result["message"]
    
    def test_english_error_messages(self):
        """英語エラーメッセージのテスト"""
        error = AppException(ErrorType.WEATHER_FETCH, lang="en")
        result = error.to_dict()
        
        assert "weather data" in result["message"].lower()
    
    def test_custom_message_overrides_default(self):
        """カスタムメッセージがデフォルトを上書きすることのテスト"""
        error = AppException(ErrorType.VALIDATION_ERROR, "カスタムメッセージ")
        result = error.to_dict()
        
        assert result["message"] == "カスタムメッセージ"