"""天気コメント生成システム - コントローラー（ビジネスロジック）

新しいモジュール構造にリダイレクトするファイル。
後方互換性のために残しています。
"""

# 新しいコントローラーをインポートして再エクスポート
# from src.controllers.comment_generation_controller import CommentGenerationController

# リファクタ版を使用 (高速化のため)
from src.controllers.refactored_comment_generation_controller import RefactoredCommentGenerationController as CommentGenerationController

__all__ = ["CommentGenerationController"]
