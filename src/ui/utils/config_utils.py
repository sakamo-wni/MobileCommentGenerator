"""
設定関連のユーティリティ関数

APIキー検証、テーマ設定など
"""

from __future__ import annotations
import os
import streamlit as st


def validate_api_keys() -> dict[str, bool]:
    """
    APIキーの存在を検証

    Returns:
        各プロバイダーのAPIキー有効性
    """
    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY"))
    }


def get_theme_colors() -> dict[str, str]:
    """
    アプリケーションのテーマカラーを取得

    Returns:
        テーマカラーの辞書
    """
    return {
        "primary": "#1E88E5",       # ブルー
        "secondary": "#FFC107",     # アンバー
        "success": "#4CAF50",       # グリーン
        "error": "#F44336",         # レッド
        "warning": "#FF9800",       # オレンジ
        "info": "#2196F3",          # ライトブルー
        "background": "#FAFAFA",    # ライトグレー
        "surface": "#FFFFFF",       # ホワイト
        "text_primary": "#212121",  # ダークグレー
        "text_secondary": "#757575", # ミディアムグレー
    }