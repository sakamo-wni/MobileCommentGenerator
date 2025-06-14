"""カスタム例外クラス定義

このモジュールはプロジェクト全体で使用する具体的な例外クラスを定義します。
より明確なエラーハンドリングと適切なデバッグ情報の提供を目的としています。
"""


class MobileCommentGeneratorError(Exception):
    """ベース例外クラス"""
    pass


# 設定関連の例外
class ConfigurationError(MobileCommentGeneratorError):
    """設定ファイルやパラメータの問題"""
    pass


class MissingConfigError(ConfigurationError):
    """必須設定が見つからない"""
    pass


class InvalidConfigError(ConfigurationError):
    """設定値が無効"""
    pass


# API関連の例外
class APIError(MobileCommentGeneratorError):
    """外部API関連のエラー"""
    pass


class WeatherAPIError(APIError):
    """天気API関連のエラー"""
    pass


class LLMAPIError(APIError):
    """LLM API関連のエラー"""
    pass


class RateLimitError(APIError):
    """APIレート制限エラー"""
    pass


class AuthenticationError(APIError):
    """認証エラー"""
    pass


# データ関連の例外
class DataError(MobileCommentGeneratorError):
    """データ処理関連のエラー"""
    pass


class DataNotFoundError(DataError):
    """必要なデータが見つからない"""
    pass


class DataValidationError(DataError):
    """データ検証エラー"""
    pass


class CommentValidationError(DataValidationError):
    """コメント検証エラー"""
    pass


# S3関連の例外
class S3Error(MobileCommentGeneratorError):
    """S3操作関連のエラー"""
    pass


class S3ConnectionError(S3Error):
    """S3接続エラー"""
    pass


class S3PermissionError(S3Error):
    """S3権限エラー"""
    pass


# ファイル操作関連の例外
class FileOperationError(MobileCommentGeneratorError):
    """ファイル操作エラー"""
    pass


class CacheError(FileOperationError):
    """キャッシュ操作エラー"""
    pass


# ワークフロー関連の例外
class WorkflowError(MobileCommentGeneratorError):
    """ワークフロー実行エラー"""
    pass


class NodeExecutionError(WorkflowError):
    """ノード実行エラー"""
    pass


# バリデーション関連の例外
class ValidationError(MobileCommentGeneratorError):
    """入力検証エラー"""
    pass


class WeatherValidationError(ValidationError):
    """天気データ検証エラー"""
    pass


class LocationValidationError(ValidationError):
    """地点情報検証エラー"""
    pass


# タイムアウト例外
class TimeoutError(MobileCommentGeneratorError):
    """処理タイムアウト"""
    pass


# リトライ可能なエラーを示すミックスイン
class RetryableError:
    """リトライ可能なエラーを示すマーカー"""
    pass


class RetryableAPIError(APIError, RetryableError):
    """リトライ可能なAPIエラー"""
    pass


class RetryableS3Error(S3Error, RetryableError):
    """リトライ可能なS3エラー"""
    pass