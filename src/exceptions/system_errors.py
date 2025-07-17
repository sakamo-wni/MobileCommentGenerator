"""システム関連のエラークラス

警告: このモジュールは非推奨です。
代わりに error_types.py の統一された例外システムを使用してください。
"""

import warnings

warnings.warn(
    "system_errors モジュールは非推奨です。error_types.py の統一された例外システムを使用してください。",
    DeprecationWarning,
    stacklevel=2
)


class FileIOError(Exception):
    """ファイル I/O 関連のベース例外"""
    pass


class ConfigurationError(Exception):
    """設定関連のエラー"""
    pass