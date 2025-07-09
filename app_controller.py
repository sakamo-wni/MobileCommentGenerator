"""天気コメント生成システム - コントローラー（ビジネスロジック）

新しいモジュール構造にリダイレクトするファイル。
後方互換性のために残しています。
"""

# 新しいコントローラーをインポートして再エクスポート
from src.controllers.comment_generation_controller import CommentGenerationController

__all__ = ['CommentGenerationController']
