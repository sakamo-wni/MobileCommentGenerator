"""
エラーメッセージングユーティリティ

ユーザーフレンドリーなエラーメッセージと対処法を提供
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
from enum import Enum
import logging
import json
from pathlib import Path
from .i18n import t

logger = logging.getLogger(__name__)

# エラーメッセージ設定ファイルのパス（将来的な拡張用）
import os
ERROR_MESSAGES_CONFIG_PATH = os.environ.get("ERROR_MESSAGES_CONFIG_PATH", None)


class ErrorType(Enum):
    """エラータイプの定義"""
    API_KEY_MISSING = "api_key_missing"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    GENERATION_FAILED = "generation_failed"
    PARTIAL_SUCCESS = "partial_success"
    UNKNOWN = "unknown"


class ErrorMessage:
    """エラーメッセージとその対処法"""
    def __init__(self, title: str, description: str, solution: Optional[str] = None,
                 title_key: Optional[str] = None, description_key: Optional[str] = None,
                 solution_key: Optional[str] = None):
        self.title = title
        self.description = description
        self.solution = solution
        # i18n対応用のキー（将来的な拡張のため）
        self.title_key = title_key
        self.description_key = description_key
        self.solution_key = solution_key


# エラータイプごとのメッセージ定義（i18n対応）
def _get_error_messages() -> Dict[ErrorType, ErrorMessage]:
    """i18n対応のエラーメッセージを取得"""
    return {
        ErrorType.API_KEY_MISSING: ErrorMessage(
            title=t("error.api_key_missing.title"),
            description=t("error.api_key_missing.description"),
            solution=t("error.api_key_missing.solution"),
            title_key="error.api_key_missing.title",
            description_key="error.api_key_missing.description",
            solution_key="error.api_key_missing.solution"
        ),
        ErrorType.API_ERROR: ErrorMessage(
            title=t("error.api_error.title"),
            description=t("error.api_error.description"),
            solution=t("error.api_error.solution"),
            title_key="error.api_error.title",
            description_key="error.api_error.description",
            solution_key="error.api_error.solution"
        ),
        ErrorType.NETWORK_ERROR: ErrorMessage(
            title=t("error.network_error.title"),
            description=t("error.network_error.description"),
            solution=t("error.network_error.solution"),
            title_key="error.network_error.title",
            description_key="error.network_error.description",
            solution_key="error.network_error.solution"
        ),
        ErrorType.VALIDATION_ERROR: ErrorMessage(
            title=t("error.validation_error.title"),
            description=t("error.validation_error.description"),
            solution=t("error.validation_error.solution"),
            title_key="error.validation_error.title",
            description_key="error.validation_error.description",
            solution_key="error.validation_error.solution"
        ),
        ErrorType.FILE_NOT_FOUND: ErrorMessage(
            title="ファイルが見つかりません",
            description="必要なファイルが見つかりませんでした。",
            solution="ファイルパスを確認するか、管理者にお問い合わせください。"
        ),
        ErrorType.PERMISSION_ERROR: ErrorMessage(
            title="アクセス権限エラー",
            description="ファイルやディレクトリへのアクセス権限がありません。",
            solution="ファイルの権限設定を確認するか、管理者にお問い合わせください。"
        ),
        ErrorType.GENERATION_FAILED: ErrorMessage(
            title=t("error.generation_failed.title"),
            description=t("error.generation_failed.description"),
            solution=t("error.generation_failed.solution"),
            title_key="error.generation_failed.title",
            description_key="error.generation_failed.description",
            solution_key="error.generation_failed.solution"
        ),
        ErrorType.PARTIAL_SUCCESS: ErrorMessage(
            title="一部の地点で生成に成功しました",
            description="すべての地点でコメントを生成できませんでした。",
            solution="失敗した地点を個別に再生成するか、異なるLLMプロバイダーをお試しください。"
        ),
        ErrorType.UNKNOWN: ErrorMessage(
            title="予期しないエラー",
            description="予期しないエラーが発生しました。",
            solution="アプリケーションを再読み込みしてから、もう一度お試しください。"
        )
    }

# グローバル変数として初期化
ERROR_MESSAGES = _get_error_messages()


def load_error_messages_from_config(config_path: Optional[str] = None) -> Optional[Dict[ErrorType, ErrorMessage]]:
    """
    設定ファイルからエラーメッセージを読み込む（将来的な拡張用）
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        エラーメッセージの辞書またはNone
    """
    if config_path is None:
        config_path = ERROR_MESSAGES_CONFIG_PATH
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            messages = {}
            for error_type_str, msg_data in config.items():
                try:
                    error_type = ErrorType(error_type_str)
                    messages[error_type] = ErrorMessage(
                        title=msg_data.get('title', ''),
                        description=msg_data.get('description', ''),
                        solution=msg_data.get('solution'),
                        title_key=msg_data.get('title_key'),
                        description_key=msg_data.get('description_key'),
                        solution_key=msg_data.get('solution_key')
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"エラーメッセージ設定の読み込みエラー: {e}")
            
            return messages
        except Exception as e:
            logger.error(f"エラーメッセージ設定ファイルの読み込みエラー: {e}")
    
    return None


# 設定ファイルからメッセージを読み込み、デフォルトを上書き
def update_error_messages():
    """エラーメッセージを更新（言語変更時に呼び出す）"""
    global ERROR_MESSAGES
    ERROR_MESSAGES = _get_error_messages()
    custom_messages = load_error_messages_from_config()
    if custom_messages:
        ERROR_MESSAGES.update(custom_messages)

# 初期化時に一度実行
update_error_messages()


def show_error(
    error_type: ErrorType,
    details: Optional[str] = None,
    show_details: bool = True,
    callback: Optional[Callable] = None
):
    """
    ユーザーフレンドリーなエラーメッセージを表示
    
    Args:
        error_type: エラーの種類
        details: 技術的な詳細情報（開発者向け）
        show_details: 詳細情報の表示有無
        callback: 「再試行」ボタンのコールバック関数
    """
    error_msg = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES[ErrorType.UNKNOWN])
    
    with st.container():
        # エラーアイコンとタイトル
        st.error(f"❌ **{error_msg.title}**")
        
        # 説明
        st.write(error_msg.description)
        
        # 対処法
        if error_msg.solution:
            st.info(f"{t('ui.solution')} {error_msg.solution}")
        
        # 詳細情報（開発者向け）
        if show_details and details:
            with st.expander(t("ui.details")):
                st.code(details, language="text")
        
        # 再試行ボタン
        if callback:
            if st.button(t("ui.retry_button"), key=f"retry_{error_type.value}"):
                callback()


def show_warning(
    title: str,
    description: str,
    suggestion: Optional[str] = None
):
    """
    警告メッセージを表示
    
    Args:
        title: 警告のタイトル
        description: 警告の説明
        suggestion: 推奨される対処法
    """
    with st.container():
        st.warning(f"⚠️ **{title}**")
        st.write(description)
        
        if suggestion:
            st.info(f"{t('ui.recommendation')} {suggestion}")


def show_success(
    title: str,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    成功メッセージを表示
    
    Args:
        title: 成功メッセージのタイトル
        description: 追加の説明
        details: 詳細情報の辞書
    """
    with st.container():
        st.success(f"✅ **{title}**")
        
        if description:
            st.write(description)
        
        if details:
            col1, col2 = st.columns(2)
            for i, (key, value) in enumerate(details.items()):
                with col1 if i % 2 == 0 else col2:
                    st.metric(key, value)


def get_error_type_from_exception(exception: Exception) -> ErrorType:
    """
    例外からエラータイプを推定
    
    Args:
        exception: 発生した例外
        
    Returns:
        推定されたエラータイプ
    """
    error_message = str(exception).lower()
    
    # APIキー関連
    if "api" in error_message and "key" in error_message:
        return ErrorType.API_KEY_MISSING
    
    # ネットワーク関連
    if any(word in error_message for word in ["connection", "network", "timeout"]):
        return ErrorType.NETWORK_ERROR
    
    # ファイル関連
    if isinstance(exception, FileNotFoundError):
        return ErrorType.FILE_NOT_FOUND
    
    # 権限関連
    if isinstance(exception, PermissionError):
        return ErrorType.PERMISSION_ERROR
    
    # バリデーション関連
    if any(word in error_message for word in ["validation", "invalid", "必須"]):
        return ErrorType.VALIDATION_ERROR
    
    # API関連
    if any(word in error_message for word in ["api", "endpoint", "request"]):
        return ErrorType.API_ERROR
    
    return ErrorType.UNKNOWN


def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    callback: Optional[Callable] = None
):
    """
    例外を処理してユーザーフレンドリーなメッセージを表示
    
    Args:
        exception: 発生した例外
        context: エラーが発生したコンテキスト
        callback: 再試行用のコールバック関数
    """
    error_type = get_error_type_from_exception(exception)
    
    # ログに記録
    logger.error(f"Error in {context or 'unknown context'}: {exception}", exc_info=True)
    
    # 技術的な詳細
    details = f"エラータイプ: {type(exception).__name__}\n"
    details += f"エラーメッセージ: {str(exception)}\n"
    if context:
        details += f"コンテキスト: {context}"
    
    # エラー表示
    show_error(
        error_type=error_type,
        details=details,
        show_details=st.session_state.get("show_error_details", True),
        callback=callback
    )