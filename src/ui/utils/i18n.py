"""
国際化（i18n）サポートモジュール

多言語対応のための基本的なフレームワーク
"""

import json
import os
from typing import Any
from enum import Enum
from pathlib import Path
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """サポートする言語"""
    JA = "ja"  # 日本語
    EN = "en"  # 英語


# デフォルトの翻訳データ
DEFAULT_TRANSLATIONS: dict[str, dict[str, str]] = {
    # エラーメッセージ
    "error.api_key_missing.title": {
        "ja": "APIキーが設定されていません",
        "en": "API Key Not Set"
    },
    "error.api_key_missing.description": {
        "ja": "選択されたLLMプロバイダーのAPIキーが設定されていません。",
        "en": "The API key for the selected LLM provider is not configured."
    },
    "error.api_key_missing.solution": {
        "ja": "左側のサイドバーから「⚙️ 設定」を開き、APIキーを入力してください。",
        "en": "Open '⚙️ Settings' from the sidebar and enter your API key."
    },
    "error.api_error.title": {
        "ja": "API接続エラー",
        "en": "API Connection Error"
    },
    "error.api_error.description": {
        "ja": "LLMプロバイダーとの通信中にエラーが発生しました。",
        "en": "An error occurred while communicating with the LLM provider."
    },
    "error.api_error.solution": {
        "ja": "しばらく待ってから再度お試しください。問題が続く場合は、APIキーが正しいか確認してください。",
        "en": "Please wait a moment and try again. If the problem persists, verify your API key is correct."
    },
    "error.network_error.title": {
        "ja": "ネットワークエラー",
        "en": "Network Error"
    },
    "error.network_error.description": {
        "ja": "インターネット接続に問題がある可能性があります。",
        "en": "There may be an issue with your internet connection."
    },
    "error.network_error.solution": {
        "ja": "ネットワーク接続を確認してから再度お試しください。",
        "en": "Please check your network connection and try again."
    },
    "error.validation_error.title": {
        "ja": "入力エラー",
        "en": "Input Error"
    },
    "error.validation_error.description": {
        "ja": "入力された内容に問題があります。",
        "en": "There is an issue with the input provided."
    },
    "error.validation_error.solution": {
        "ja": "入力内容を確認して、正しい形式で入力してください。",
        "en": "Please check your input and ensure it is in the correct format."
    },
    "error.generation_failed.title": {
        "ja": "コメント生成に失敗しました",
        "en": "Comment Generation Failed"
    },
    "error.generation_failed.description": {
        "ja": "コメントの生成処理中にエラーが発生しました。",
        "en": "An error occurred during comment generation."
    },
    "error.generation_failed.solution": {
        "ja": "もう一度お試しください。問題が続く場合は、異なるLLMプロバイダーをお試しください。",
        "en": "Please try again. If the problem persists, try a different LLM provider."
    },
    
    # UI要素
    "ui.retry_button": {
        "ja": "🔄 再試行",
        "en": "🔄 Retry"
    },
    "ui.details": {
        "ja": "🔍 詳細情報",
        "en": "🔍 Details"
    },
    "ui.solution": {
        "ja": "💡 対処法:",
        "en": "💡 Solution:"
    },
    "ui.recommendation": {
        "ja": "💡 推奨:",
        "en": "💡 Recommendation:"
    },
    
    # 一般的なメッセージ
    "message.loading": {
        "ja": "読み込み中...",
        "en": "Loading..."
    },
    "message.processing": {
        "ja": "処理中...",
        "en": "Processing..."
    },
    "message.success": {
        "ja": "完了しました",
        "en": "Completed"
    },
    "message.failed": {
        "ja": "失敗しました",
        "en": "Failed"
    }
}


class I18n:
    """国際化サポートクラス"""
    
    def __init__(self, default_language: Language = Language.JA):
        """
        Args:
            default_language: デフォルトの言語
        """
        self.translations = DEFAULT_TRANSLATIONS.copy()
        self.default_language = default_language
        self._load_custom_translations()
    
    def _load_custom_translations(self):
        """カスタム翻訳ファイルを読み込む"""
        translations_dir = os.environ.get("I18N_TRANSLATIONS_DIR")
        translations_dir_path = Path(translations_dir) if translations_dir else None
        if translations_dir_path and translations_dir_path.exists():
            for lang in Language:
                lang_file = translations_dir_path / f"{lang.value}.json"
                if lang_file.exists():
                    try:
                        with open(lang_file, 'r', encoding='utf-8') as f:
                            custom_translations = json.load(f)
                        
                        # カスタム翻訳をマージ
                        for key, value in custom_translations.items():
                            if key not in self.translations:
                                self.translations[key] = {}
                            self.translations[key][lang.value] = value
                    except Exception as e:
                        logger.error(f"翻訳ファイルの読み込みエラー ({lang_file}): {e}")
    
    def get_current_language(self) -> Language:
        """現在の言語を取得"""
        # セッション状態から言語を取得
        if "language" in st.session_state:
            try:
                return Language(st.session_state.language)
            except ValueError:
                pass
        
        # 環境変数から言語を取得
        lang_env = os.environ.get("APP_LANGUAGE", "ja")
        try:
            return Language(lang_env)
        except ValueError:
            return self.default_language
    
    def set_language(self, language: Language):
        """言語を設定"""
        st.session_state.language = language.value
    
    def t(self, key: str, **kwargs) -> str:
        """
        翻訳を取得
        
        Args:
            key: 翻訳キー
            **kwargs: 翻訳内の変数置換用パラメータ
            
        Returns:
            翻訳されたテキスト
        """
        current_lang = self.get_current_language()
        
        # 翻訳を取得
        if key in self.translations:
            translations = self.translations[key]
            text = translations.get(current_lang.value)
            
            if text is None:
                # フォールバック: デフォルト言語
                text = translations.get(self.default_language.value)
            
            if text is None:
                # フォールバック: 最初に見つかった翻訳
                text = next(iter(translations.values()), key)
        else:
            # 翻訳が見つからない場合はキーを返す
            text = key
            logger.warning(f"翻訳キーが見つかりません: {key}")
        
        # 変数置換
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.error(f"翻訳の変数置換エラー ({key}): {e}")
        
        return text
    
    def add_translation(self, key: str, translations: dict[str, str]):
        """
        翻訳を追加
        
        Args:
            key: 翻訳キー
            translations: 言語コードと翻訳のマッピング
        """
        self.translations[key] = translations


# グローバルインスタンス
_i18n = I18n()


def t(key: str, **kwargs) -> str:
    """
    翻訳を取得する便利関数
    
    Args:
        key: 翻訳キー
        **kwargs: 翻訳内の変数置換用パラメータ
        
    Returns:
        翻訳されたテキスト
    """
    return _i18n.t(key, **kwargs)


def set_language(language: Language):
    """言語を設定"""
    _i18n.set_language(language)


def get_current_language() -> Language:
    """現在の言語を取得"""
    return _i18n.get_current_language()