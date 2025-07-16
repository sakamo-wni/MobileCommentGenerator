"""
設定モジュールのCLIエントリーポイント

使用方法:
    python -m src.config
"""

from __future__ import annotations
from .validate import main

if __name__ == "__main__":
    main()