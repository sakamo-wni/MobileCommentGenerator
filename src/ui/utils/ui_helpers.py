"""
UI関連のヘルパー関数

クリップボード操作、ダウンロード、エラーハンドリングなど
"""

import base64
from typing import Any, Callable
from datetime import datetime
import streamlit as st
from .feedback_components import show_notification


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
    
    # ユニークなIDを生成（複数のコピーボタンに対応）
    from .security_utils import generate_safe_id
    unique_id = generate_safe_id("clipboard")
    
    # StreamlitでのJavaScript実行（HTTPS環境でのみ動作）
    js_code = f"""
    <script>
    (function() {{
        const textToCopy = `{escaped_text}`;
        const uniqueId = '{unique_id}';
        
        // Clipboard APIが利用可能か確認
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(textToCopy).then(function() {{
                console.log('Copying to clipboard was successful!');
                // 成功通知を表示
                showNotification('success');
            }}, function(err) {{
                console.error('Could not copy text: ', err);
                // エラー通知を表示してフォールバック処理
                showNotification('error', err.message || 'クリップボードへのアクセスが拒否されました');
                showFallback();
            }});
        }} else {{
            // Clipboard APIが利用できない場合
            showNotification('warning', 'セキュアな接続（HTTPS）でないため、クリップボード機能が制限されています');
            showFallback();
        }}
        
        function showNotification(type, message) {{
            const notifElem = document.getElementById('clipboard-notification-' + uniqueId);
            if (notifElem) {{
                let icon = '';
                let color = '';
                let msg = '';
                
                switch(type) {{
                    case 'success':
                        icon = '✅';
                        color = '#4caf50';
                        msg = 'クリップボードにコピーしました';
                        break;
                    case 'error':
                        icon = '❌';
                        color = '#f44336';
                        msg = message || 'コピーに失敗しました';
                        break;
                    case 'warning':
                        icon = '⚠️';
                        color = '#ff9800';
                        msg = message || '警告';
                        break;
                }}
                
                notifElem.innerHTML = icon + ' ' + msg;
                notifElem.style.color = color;
                notifElem.style.display = 'block';
                
                // 3秒後に非表示
                if (type === 'success') {{
                    setTimeout(() => {{
                        notifElem.style.display = 'none';
                    }}, 3000);
                }}
            }}
        }}
        
        function showFallback() {{
            // フォールバック：選択可能なテキストエリアを表示
            const elem = document.getElementById('clipboard-fallback-' + uniqueId);
            if (elem) {{
                elem.style.display = 'block';
            }}
        }}
    }})();
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    
    # 通知表示エリア
    st.markdown(
        f'<div id="clipboard-notification-{unique_id}" style="display:none; margin-bottom:10px; font-weight:bold;"></div>',
        unsafe_allow_html=True
    )
    
    # フォールバック表示（HTTPSでない場合のため）
    if fallback_display:
        from .security_utils import sanitize_html
        st.markdown(
            f'<div id="clipboard-fallback-{unique_id}" style="display:none; margin-top:10px; padding:10px; background-color:#f5f5f5; border:1px solid #ddd; border-radius:4px;">' +
            f'<p style="color:#666; font-size:0.9em; margin-bottom:8px;">📋 以下のテキストを手動で選択してコピーしてください：</p>' +
            f'<textarea readonly style="width:100%; height:100px; padding:8px; border:1px solid #ccc; border-radius:4px; font-family:monospace; resize:vertical;">{sanitize_html(text)}</textarea>' +
            f'<p style="color:#888; font-size:0.8em; margin-top:8px; margin-bottom:0;">💡 ヒント: テキストエリア内をトリプルクリックすると全選択できます</p>' +
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


def handle_error(error: Exception, context: str | None = None, callback: Callable | None = None) -> None:
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