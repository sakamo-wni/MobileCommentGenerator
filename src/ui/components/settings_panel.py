"""設定パネルコンポーネント"""

from __future__ import annotations
import streamlit as st
import os
from typing import Any
from src.config.app_config import get_config, reset_config
try:
    from src.utils.secure_config import get_secure_config, mask_api_key
except ImportError:
    get_secure_config = None
    mask_api_key = lambda x: "*" * 20 if x else ""


def settings_panel() -> dict[str, Any]:
    """
    設定パネルコンポーネント
    
    Returns:
        更新された設定値の辞書
    """
    config = get_config()
    updated_settings = {}
    
    # APIキー設定
    st.subheader("🔐 APIキー設定")
    
    # 現在の検証状態
    validation = config.api_keys.validate()
    
    # OpenAI
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            openai_key = st.text_input(
                "OpenAI API Key",
                value="*" * 20 if validation["openai"] else "",
                type="password",
                help="OpenAI GPTを使用する場合に必要です"
            )
        with col2:
            if validation["openai"]:
                st.success("✅ 設定済み")
            else:
                st.error("❌ 未設定")
        
        if openai_key and openai_key != "*" * 20:
            os.environ["OPENAI_API_KEY"] = openai_key
            if get_secure_config:
                secure_config = get_secure_config()
                secure_config.save_api_key("openai", openai_key)
            updated_settings["openai_key"] = True
    
    # Gemini
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            gemini_key = st.text_input(
                "Gemini API Key",
                value="*" * 20 if validation["gemini"] else "",
                type="password",
                help="Google Geminiを使用する場合に必要です"
            )
        with col2:
            if validation["gemini"]:
                st.success("✅ 設定済み")
            else:
                st.error("❌ 未設定")
        
        if gemini_key and gemini_key != "*" * 20:
            os.environ["GEMINI_API_KEY"] = gemini_key
            if get_secure_config:
                secure_config = get_secure_config()
                secure_config.save_api_key("gemini", gemini_key)
            updated_settings["gemini_key"] = True
    
    # Anthropic
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            anthropic_key = st.text_input(
                "Anthropic API Key",
                value="*" * 20 if validation["anthropic"] else "",
                type="password",
                help="Claude APIを使用する場合に必要です"
            )
        with col2:
            if validation["anthropic"]:
                st.success("✅ 設定済み")
            else:
                st.error("❌ 未設定")
        
        if anthropic_key and anthropic_key != "*" * 20:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            if get_secure_config:
                secure_config = get_secure_config()
                secure_config.save_api_key("anthropic", anthropic_key)
            updated_settings["anthropic_key"] = True
    
    # 天気API
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            wxtech_key = st.text_input(
                "WXTECH API Key",
                value="*" * 20 if validation["wxtech"] else "",
                type="password",
                help="天気予報データの取得に必要です（必須）"
            )
        with col2:
            if validation["wxtech"]:
                st.success("✅ 設定済み")
            else:
                st.error("❌ 未設定")
        
        if wxtech_key and wxtech_key != "*" * 20:
            os.environ["WXTECH_API_KEY"] = wxtech_key
            if get_secure_config:
                secure_config = get_secure_config()
                secure_config.save_api_key("wxtech", wxtech_key)
            updated_settings["wxtech_key"] = True
    
    
    # 詳細設定
    if st.checkbox("詳細設定を表示"):
        st.subheader("⚙️ 詳細設定")
        
        # 生成設定
        st.write("**生成設定**")
        max_locations = st.number_input(
            "一度に生成可能な最大地点数",
            min_value=1,
            max_value=100,
            value=config.ui_settings.max_locations_per_generation,
            help="バッチ処理で一度に生成できる地点数の上限"
        )
        if max_locations != config.ui_settings.max_locations_per_generation:
            os.environ["MAX_LOCATIONS_PER_GENERATION"] = str(max_locations)
            updated_settings["max_locations"] = max_locations
        
        # タイムアウト設定
        timeout = st.number_input(
            "生成タイムアウト（秒）",
            min_value=30,
            max_value=600,
            value=config.generation_settings.generation_timeout,
            help="コメント生成のタイムアウト時間"
        )
        if timeout != config.generation_settings.generation_timeout:
            updated_settings["generation_timeout"] = timeout
        
        # デバッグモード
        debug_mode = st.checkbox(
            "デバッグモード",
            value=config.debug,
            help="詳細なログ情報を表示します"
        )
        if debug_mode != config.debug:
            os.environ["DEBUG"] = str(debug_mode).lower()
            updated_settings["debug"] = debug_mode
    
    # 設定の保存
    if st.button("💾 設定を保存", type="primary"):
        if updated_settings:
            # 設定をリセットして再読み込み
            reset_config()
            new_config = get_config()
            st.success("✅ 設定を保存しました")
            st.rerun()
        else:
            st.info("変更された設定はありません")
    
    return updated_settings