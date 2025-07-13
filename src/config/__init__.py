"""設定モジュールのパブリックAPI

このモジュールは、アプリケーション全体で使用される設定関連のクラスと関数を提供します。
"""

# メイン設定クラスと関数（存在確認済み）
from .config import Config, get_config

__all__ = [
    'Config',
    'get_config',
]