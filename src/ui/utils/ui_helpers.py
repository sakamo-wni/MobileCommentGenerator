"""
UI関連のヘルパー関数

クリップボード操作、ダウンロード、エラーハンドリングなど
"""

import base64
from typing import Dict, Any
from datetime import datetime
import streamlit as st


def copy_to_clipboard(text: str) -> bool:
    """
    テキストをクリップボードにコピー

    Args:
        text: コピーするテキスト

    Returns:
        成功した場合True
    """
    # StreamlitでのJavaScript実行
    js_code = f"""
    <script>
    navigator.clipboard.writeText(`{text}`).then(function() {{
        console.log('Copying to clipboard was successful!');
    }}, function(err) {{
        console.error('Could not copy text: ', err);
    }});
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    return True


def format_timestamp(dt: datetime) -> str:
    """
    タイムスタンプをフォーマット

    Args:
        dt: datetime オブジェクト

    Returns:
        フォーマットされた日時文字列
    """
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """
    ダウンロードリンクを作成

    Args:
        data: ダウンロードデータ
        filename: ファイル名
        mime_type: MIMEタイプ

    Returns:
        HTMLダウンロードリンク
    """
    # Base64エンコード
    b64 = base64.b64encode(data.encode()).decode()

    # ダウンロードリンクの作成
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 {filename}</a>'
    
    return href


def reset_session_state():
    """
    セッションステートをリセット
    """
    # 保持したいキーのリスト
    preserve_keys = ['api_keys', 'locations', 'theme']
    
    # 保持するデータを一時的に保存
    preserved_data = {key: st.session_state.get(key) for key in preserve_keys if key in st.session_state}
    
    # セッションステートをクリア
    st.session_state.clear()
    
    # 保持したいデータを復元
    for key, value in preserved_data.items():
        st.session_state[key] = value


def handle_error(error: Exception, context: str = ""):
    """
    エラーを適切に処理して表示

    Args:
        error: 発生した例外
        context: エラーコンテキスト（オプション）
    """
    error_message = str(error)
    
    # コンテキストがある場合は追加
    if context:
        error_message = f"{context}: {error_message}"
    
    # エラーの種類に応じて表示方法を変える
    if isinstance(error, ValueError):
        st.warning(f"⚠️ 入力エラー: {error_message}")
    elif isinstance(error, FileNotFoundError):
        st.error(f"📁 ファイルが見つかりません: {error_message}")
    elif isinstance(error, PermissionError):
        st.error(f"🔒 アクセス権限エラー: {error_message}")
    else:
        st.error(f"❌ エラー: {error_message}")
    
    # デバッグモードの場合は詳細情報を表示
    if st.session_state.get('debug_mode', False):
        st.exception(error)