"""
レスポンシブデザインユーティリティ

モバイルフレンドリーなUIを実現するためのスタイリングとレイアウトヘルパー
"""

import streamlit as st
from typing import Optional, List, Tuple


def apply_responsive_styles():
    """
    レスポンシブデザインのCSSスタイルを適用
    """
    st.markdown("""
    <style>
    /* モバイル対応の基本スタイル */
    @media (max-width: 768px) {
        /* サイドバーのスタイル調整 */
        .css-1d391kg {
            padding: 1rem 0.5rem;
        }
        
        /* メインコンテンツの余白調整 */
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        /* ボタンのスタイル調整 */
        .stButton > button {
            width: 100%;
            padding: 0.5rem 1rem;
            font-size: 1rem;
        }
        
        /* メトリクスの表示調整 */
        [data-testid="metric-container"] {
            padding: 0.5rem;
        }
        
        /* カラムの最小幅設定 */
        .css-1kyxreq {
            flex: 100%;
            max-width: 100%;
        }
        
        /* テキストエリアの高さ調整 */
        .stTextArea textarea {
            min-height: 100px;
        }
        
        /* エクスパンダーのパディング調整 */
        .streamlit-expanderHeader {
            padding: 0.5rem;
        }
        
        /* テーブルのスクロール対応 */
        .dataframe {
            overflow-x: auto;
        }
    }
    
    /* タブレット対応 */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            max-width: 95%;
        }
    }
    
    /* 共通のアクセシビリティ向上 */
    /* フォーカス状態の明確化 */
    button:focus, input:focus, select:focus, textarea:focus {
        outline: 2px solid #0066cc;
        outline-offset: 2px;
    }
    
    /* タッチターゲットの最小サイズ確保 */
    button, .stCheckbox, .stRadio > div {
        min-height: 44px;
        min-width: 44px;
    }
    
    /* 読みやすさの向上 */
    p, li {
        line-height: 1.6;
    }
    
    /* エラーメッセージの視認性向上 */
    .stAlert {
        border-left-width: 4px;
        padding: 1rem;
    }
    
    /* カード風のコンテナスタイル */
    .card-container {
        background-color: var(--background-color);
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* 成功・エラーのアニメーション */
    @keyframes slideIn {
        from {
            transform: translateY(-10px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .stSuccess, .stError, .stWarning, .stInfo {
        animation: slideIn 0.3s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)


def create_responsive_columns(
    ratios: List[float],
    gap: str = "medium"
) -> List:
    """
    レスポンシブ対応のカラムを作成
    
    Args:
        ratios: カラムの比率リスト
        gap: カラム間のギャップサイズ（small, medium, large）
    
    Returns:
        Streamlitのカラムオブジェクトのリスト
    """
    gap_size = {
        "small": "0.5rem",
        "medium": "1rem", 
        "large": "2rem"
    }.get(gap, "1rem")
    
    # カスタムCSSでギャップを設定
    st.markdown(f"""
    <style>
    .row-widget.stHorizontalBlock {{
        gap: {gap_size};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    return st.columns(ratios)


def create_card(
    title: str,
    content: str,
    icon: Optional[str] = None,
    color: Optional[str] = None
):
    """
    カード風のUIコンポーネントを作成
    
    Args:
        title: カードのタイトル
        content: カードの内容
        icon: アイコン（絵文字）
        color: 背景色
    """
    icon_html = f"{icon} " if icon else ""
    color_style = f"background-color: {color};" if color else ""
    
    st.markdown(f"""
    <div class="card-container" style="{color_style}">
        <h3>{icon_html}{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def create_progress_indicator(
    current: int,
    total: int,
    label: Optional[str] = None
):
    """
    視覚的に分かりやすいプログレスインジケーターを作成
    
    Args:
        current: 現在の値
        total: 合計値
        label: ラベルテキスト
    """
    progress = current / total if total > 0 else 0
    percentage = int(progress * 100)
    
    label_text = label or f"{current}/{total}"
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>{label_text}</span>
            <span>{percentage}%</span>
        </div>
        <div style="background-color: #e0e0e0; border-radius: 4px; height: 8px; overflow: hidden;">
            <div style="background-color: #0066cc; width: {percentage}%; height: 100%; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_loading_animation(message: str = "処理中..."):
    """
    カスタムローディングアニメーションを表示
    
    Args:
        message: 表示するメッセージ
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div class="loading-spinner"></div>
        <p style="margin-top: 1rem;">{message}</p>
    </div>
    <style>
    .loading-spinner {{
        display: inline-block;
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #0066cc;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def create_tooltip(
    text: str,
    tooltip: str,
    icon: str = "ℹ️"
):
    """
    ツールチップ付きのテキストを作成
    
    Args:
        text: 表示するテキスト
        tooltip: ツールチップの内容
        icon: ヘルプアイコン
    """
    st.markdown(f"""
    <div style="display: inline-flex; align-items: center; gap: 0.5rem;">
        <span>{text}</span>
        <span title="{tooltip}" style="cursor: help;">{icon}</span>
    </div>
    """, unsafe_allow_html=True)


def get_device_type() -> str:
    """
    デバイスタイプを推定（簡易版）
    
    Returns:
        "mobile", "tablet", "desktop" のいずれか
    """
    # StreamlitではJavaScriptを直接実行できないため、
    # セッションステートに保存された情報を使用
    return st.session_state.get("device_type", "desktop")


def optimize_for_device(device_type: Optional[str] = None):
    """
    デバイスタイプに応じた最適化を適用
    
    Args:
        device_type: デバイスタイプ（None の場合は自動検出）
    """
    if device_type is None:
        device_type = get_device_type()
    
    if device_type == "mobile":
        st.set_page_config(
            layout="centered",
            initial_sidebar_state="collapsed"
        )
    elif device_type == "tablet":
        st.set_page_config(
            layout="centered",
            initial_sidebar_state="auto"
        )
    else:  # desktop
        st.set_page_config(
            layout="wide",
            initial_sidebar_state="expanded"
        )