"""ローカルCSVファイルからコメントデータを読み込むリポジトリ

このモジュールは、S3ではなくローカルのCSVファイルから過去コメントを読み込みます。
CSVファイルは output/ ディレクトリに季節別・タイプ別に保存されています。

Note: このファイルは後方互換性のために維持されています。
実際の実装はlocal_comment_repository_refactored.pyに移行されました。
"""

# リファクタリング版をインポートして、後方互換性を維持
from src.repositories.local_comment_repository_refactored import LocalCommentRepository

__all__ = ['LocalCommentRepository']