"""データ処理関連のエラークラス"""


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