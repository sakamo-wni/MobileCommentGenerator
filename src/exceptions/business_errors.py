"""ビジネスロジック関連のエラークラス"""


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