"""
プロンプトビルダー（後方互換性のためのラッパー）

このファイルは後方互換性のために保持されています。
新しいコードでは src.llm.prompt_builder パッケージを直接インポートしてください。
"""

# 後方互換性のため、すべてのエクスポートを再エクスポート
from src.llm.prompt_builder import (
    PromptTemplate,
    TemplateLoader,
    CommentPromptBuilder,
    create_simple_prompt
)

__all__ = [
    'PromptTemplate',
    'TemplateLoader',
    'CommentPromptBuilder',
    'create_simple_prompt'
]