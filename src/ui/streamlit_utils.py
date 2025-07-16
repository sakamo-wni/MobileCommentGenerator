"""
Streamlit UIユーティリティ関数

後方互換性のためのラッパーモジュール
新しいコードでは src.ui.utils パッケージから直接インポートすることを推奨
"""

# 後方互換性のために全ての関数を再エクスポート

from __future__ import annotations
from .utils import (
    # Location utilities
    get_location_order,
    sort_locations_by_order,
    load_locations,
    filter_locations,
    # History utilities
    save_to_history,
    load_history,
    export_history_csv,
    # UI helpers
    copy_to_clipboard,
    format_timestamp,
    create_download_link,
    reset_session_state,
    handle_error,
    # Config utilities
    validate_api_keys,
    get_theme_colors,
    # Statistics utilities
    get_statistics,
)

__all__ = [
    # Location utilities
    "get_location_order",
    "sort_locations_by_order",
    "load_locations",
    "filter_locations",
    # History utilities
    "save_to_history",
    "load_history",
    "export_history_csv",
    # UI helpers
    "copy_to_clipboard",
    "format_timestamp",
    "create_download_link",
    "reset_session_state",
    "handle_error",
    # Config utilities
    "validate_api_keys",
    "get_theme_colors",
    # Statistics utilities
    "get_statistics",
]