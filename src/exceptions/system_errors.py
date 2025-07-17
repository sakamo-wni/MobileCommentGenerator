"""システム関連のエラークラス"""


class FileIOError(Exception):
    """ファイル I/O 関連のベース例外"""
    pass


class ConfigurationError(Exception):
    """設定関連のエラー"""
    pass