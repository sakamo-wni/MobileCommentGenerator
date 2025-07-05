"""コメント選択ロジックを分離したクラス - 後方互換性のためのラッパー"""

# 後方互換性のため、新しいモジュール構造から再エクスポート
from src.nodes.comment_selector.base_selector import CommentSelector

__all__ = ['CommentSelector']