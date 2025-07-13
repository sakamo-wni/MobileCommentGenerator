"""
UI関連のヘルパー関数

クリップボード操作、ダウンロード、エラーハンドリングなど
"""

import base64
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import streamlit as st


def copy_to_clipboard(text: str, fallback_display: bool = True) -> bool:
    """
    テキストをクリップボードにコピー

    Args:
        text: コピーするテキスト
        fallback_display: フォールバック表示を行うか

    Returns:
        成功した場合True
    """
    # テキストをエスケープ
    from .security_utils import escape_json_string
    escaped_text = escape_json_string(text)
    
    # StreamlitでのJavaScript実行（HTTPS環境でのみ動作）
    js_code = f"""
    <script>
    (function() {{
        const textToCopy = `{escaped_text}`;
        
        // Clipboard APIが利用可能か確認
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(textToCopy).then(function() {{
                console.log('Copying to clipboard was successful!');
            }}, function(err) {{
                console.error('Could not copy text: ', err);
                // フォールバック処理
                showFallback();
            }});
        }} else {{
            // Clipboard APIが利用できない場合
            showFallback();
        }}
        
        function showFallback() {{
            // フォールバック：選択可能なテキストエリアを表示
            const elem = document.getElementById('clipboard-fallback');
            if (elem) {{
                elem.style.display = 'block';
            }}
        }}
    }})();
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    
    # フォールバック表示（HTTPSでない場合のため）
    if fallback_display:
        from .security_utils import sanitize_html
        st.markdown(
            f'<div id="clipboard-fallback" style="display:none; margin-top:10px;">' +
            f'<p style="color:#666; font-size:0.9em;">✋ クリップボードへのコピーが失敗しました。' +
            f'以下のテキストを手動で選択してコピーしてください：</p>' +
            f'<textarea readonly style="width:100%; height:100px; padding:8px; border:1px solid #ddd;">{sanitize_html(text)}</textarea>' +
            f'</div>',
            unsafe_allow_html=True
        )
    
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


def handle_error(error: Exception, context: Optional[str] = None, callback: Optional[Callable] = None) -> None:
    """
    エラーを適切に処理してユーザーフレンドリーなメッセージを表示

    Args:
        error: 発生した例外
        context: エラーが発生したコンテキスト
        callback: 再試行用のコールバック関数
    """
    # 新しいエラーメッセージングシステムを使用
    from .error_messaging import handle_exception
    handle_exception(error, context=context, callback=callback)