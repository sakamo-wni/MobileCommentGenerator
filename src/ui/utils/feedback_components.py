"""
ユーザーフィードバックコンポーネント

より良いユーザー体験のためのフィードバック機能
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Callable, Literal
from datetime import datetime
import time
from .security_utils import sanitize_html, sanitize_id, generate_safe_id


def show_operation_status(
    operation_name: str,
    status: Literal["processing", "success", "error", "warning"] = "processing",
    message: Optional[str] = None,
    progress: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    操作の状態を視覚的に表示
    
    Args:
        operation_name: 操作名
        status: 状態（processing, success, error, warning）
        message: 追加メッセージ
        progress: 進行状況（0.0-1.0）
        details: 詳細情報
    """
    status_config = {
        "processing": {"icon": "⏳", "color": "#1f77b4"},
        "success": {"icon": "✅", "color": "#2ca02c"},
        "error": {"icon": "❌", "color": "#d62728"},
        "warning": {"icon": "⚠️", "color": "#ff7f0e"}
    }
    
    config = status_config.get(status, status_config["processing"])
    
    # ステータスコンテナ
    with st.container():
        col1, col2 = st.columns([1, 9])
        
        with col1:
            st.markdown(f"<h2 style='text-align: center;'>{sanitize_html(config['icon'])}</h2>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<h4 style='color: {config['color']};'>{sanitize_html(operation_name)}</h4>", unsafe_allow_html=True)
            
            if message:
                st.write(message)
            
            if progress is not None:
                st.progress(progress)
            
            if details:
                with st.expander("詳細情報"):
                    for key, value in details.items():
                        st.write(f"**{sanitize_html(str(key))}:** {sanitize_html(str(value))}")


def show_step_progress(
    steps: List[Dict[str, Any]],
    current_step: int
):
    """
    ステップごとの進行状況を表示
    
    Args:
        steps: ステップのリスト [{"name": "ステップ名", "status": "complete|current|pending"}]
        current_step: 現在のステップ番号
    """
    st.markdown("""
    <style>
    .step-container {
        display: flex;
        align-items: center;
        margin: 1rem 0;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
    }
    .step-complete {
        background-color: #2ca02c;
        color: white;
    }
    .step-current {
        background-color: #1f77b4;
        color: white;
        animation: pulse 2s infinite;
    }
    .step-pending {
        background-color: #e0e0e0;
        color: #666;
    }
    .step-line {
        flex: 1;
        height: 2px;
        background-color: #e0e0e0;
        margin: 0 1rem;
    }
    .step-line-complete {
        background-color: #2ca02c;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    for i, step in enumerate(steps):
        status = step.get("status", "pending")
        status_class = f"step-{status}"
        icon = "✓" if status == "complete" else str(i + 1)
        
        st.markdown(f"""
        <div class="step-container">
            <div class="step-circle {status_class}">{icon}</div>
            <div style="flex: 1;">
                <strong>{sanitize_html(step['name'])}</strong>
                {f"<br><small>{sanitize_html(step.get('description', ''))}</small>" if step.get('description') else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ステップ間の線
        if i < len(steps) - 1:
            line_class = "step-line-complete" if status == "complete" else ""
            st.markdown(f'<div class="step-line {line_class}"></div>', unsafe_allow_html=True)


def show_confirmation_dialog(
    title: str,
    message: str,
    confirm_label: str = "確認",
    cancel_label: str = "キャンセル",
    danger: bool = False
) -> Optional[bool]:
    """
    確認ダイアログを表示
    
    Args:
        title: ダイアログのタイトル
        message: 確認メッセージ
        confirm_label: 確認ボタンのラベル
        cancel_label: キャンセルボタンのラベル
        danger: 危険な操作かどうか（確認ボタンを赤色にする）
    
    Returns:
        確認された場合True、キャンセルされた場合False、未選択の場合None
    """
    with st.container():
        st.markdown(f"### {sanitize_html(title)}")
        st.write(sanitize_html(message))
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button(confirm_label, type="primary" if not danger else "secondary", 
                        help="この操作を実行します"):
                return True
        
        with col2:
            if st.button(cancel_label, help="この操作をキャンセルします"):
                return False
    
    return None


def show_notification(
    message: str,
    type: Literal["info", "success", "warning", "error"] = "info",
    duration: int = 3,
    position: Literal["top-right", "top-left", "bottom-right", "bottom-left"] = "top-right"
):
    """
    一時的な通知を表示（トースト風）
    
    Args:
        message: 通知メッセージ
        type: 通知タイプ（info, success, warning, error）
        duration: 表示時間（秒）
        position: 表示位置
    """
    notification_id = generate_safe_id("notification")
    
    type_styles = {
        "info": {"bg": "#e3f2fd", "color": "#1976d2", "icon": "ℹ️"},
        "success": {"bg": "#e8f5e9", "color": "#388e3c", "icon": "✅"},
        "warning": {"bg": "#fff3e0", "color": "#f57c00", "icon": "⚠️"},
        "error": {"bg": "#ffebee", "color": "#d32f2f", "icon": "❌"}
    }
    
    style = type_styles.get(type, type_styles["info"])
    
    position_styles = {
        "top-right": "top: 20px; right: 20px;",
        "top-left": "top: 20px; left: 20px;",
        "bottom-right": "bottom: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;"
    }
    
    pos_style = position_styles.get(position, position_styles["top-right"])
    
    st.markdown(f"""
    <div id="{notification_id}" class="notification" style="
        position: fixed;
        {pos_style}
        background-color: {style['bg']};
        color: {style['color']};
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        max-width: 300px;
    ">
        <span style="font-size: 1.2em;">{sanitize_html(style['icon'])}</span>
        <span>{sanitize_html(message)}</span>
    </div>
    <script>
        setTimeout(function() {{
            var elem = document.getElementById("{notification_id}");
            if (elem) {{
                elem.style.animation = "slideOut 0.3s ease-in";
                setTimeout(function() {{
                    elem.remove();
                }}, 300);
            }}
        }}, {duration * 1000});
    </script>
    <style>
    @keyframes slideIn {{
        from {{ transform: translateX(100%); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}
    @keyframes slideOut {{
        from {{ transform: translateX(0); opacity: 1; }}
        to {{ transform: translateX(100%); opacity: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def create_feedback_form(
    form_id: str = "feedback_form",
    include_rating: bool = True,
    include_comment: bool = True,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Optional[Dict[str, Any]]:
    """
    フィードバックフォームを作成
    
    Args:
        form_id: フォームID
        include_rating: 評価を含むか
        include_comment: コメントを含むか
        callback: 送信時のコールバック関数
    
    Returns:
        フィードバックデータまたはNone
    """
    with st.form(form_id):
        st.markdown("### 📝 フィードバック")
        
        feedback_data = {}
        
        if include_rating:
            rating = st.select_slider(
                "この機能はどの程度役立ちましたか？",
                options=["とても不満", "不満", "普通", "満足", "とても満足"],
                value="普通"
            )
            feedback_data["rating"] = rating
            
            # 絵文字での視覚的フィードバック
            emoji_map = {
                "とても不満": "😞",
                "不満": "😐", 
                "普通": "😊",
                "満足": "😃",
                "とても満足": "🤩"
            }
            st.markdown(f"<h1 style='text-align: center;'>{emoji_map[rating]}</h1>", unsafe_allow_html=True)
        
        if include_comment:
            comment = st.text_area(
                "ご意見・ご要望をお聞かせください（任意）",
                placeholder="改善点や追加してほしい機能などがあれば教えてください",
                height=100
            )
            feedback_data["comment"] = comment
        
        # タイムスタンプ
        feedback_data["timestamp"] = datetime.now().isoformat()
        
        submitted = st.form_submit_button("送信", type="primary")
        
        if submitted:
            if callback:
                callback(feedback_data)
            else:
                st.success("フィードバックありがとうございました！")
            return feedback_data
    
    return None


def show_help_tooltip(
    text: str,
    help_text: str,
    icon: str = "❓"
):
    """
    ヘルプツールチップを表示
    
    Args:
        text: メインテキスト
        help_text: ヘルプテキスト
        icon: ヘルプアイコン
    """
    with st.container():
        col1, col2 = st.columns([20, 1])
        with col1:
            st.write(text)
        with col2:
            st.markdown(
                f'<span title="{sanitize_html(help_text)}" style="cursor: help; font-size: 1.2em;">{sanitize_html(icon)}</span>',
                unsafe_allow_html=True
            )


def create_onboarding_tour(
    steps: List[Dict[str, str]],
    tour_id: str = "onboarding_tour"
):
    """
    新規ユーザー向けのオンボーディングツアーを作成
    
    Args:
        steps: ツアーステップのリスト [{"title": "", "content": "", "target": ""}]
        tour_id: ツアーID
    """
    if f"{tour_id}_completed" not in st.session_state:
        st.session_state[f"{tour_id}_completed"] = False
    
    if not st.session_state[f"{tour_id}_completed"]:
        current_step = st.session_state.get(f"{tour_id}_step", 0)
        
        if current_step < len(steps):
            step = steps[current_step]
            
            with st.container():
                st.info(f"""
                **👋 {sanitize_html(step['title'])}** ({current_step + 1}/{len(steps)})
                
                {sanitize_html(step['content'])}
                """)
                
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if current_step > 0:
                        if st.button("← 前へ"):
                            st.session_state[f"{tour_id}_step"] = current_step - 1
                            st.rerun()
                
                with col2:
                    if current_step < len(steps) - 1:
                        if st.button("次へ →"):
                            st.session_state[f"{tour_id}_step"] = current_step + 1
                            st.rerun()
                    else:
                        if st.button("完了 ✓"):
                            st.session_state[f"{tour_id}_completed"] = True
                            st.rerun()
                
                with col3:
                    if st.button("スキップ"):
                        st.session_state[f"{tour_id}_completed"] = True
                        st.rerun()