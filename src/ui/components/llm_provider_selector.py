"""LLMプロバイダー選択コンポーネント"""

import streamlit as st
from typing import Any
from src.config.app_config import get_config


def llm_provider_selector() -> str:
    """
    LLMプロバイダー選択コンポーネント

    Returns:
        選択されたプロバイダー名
    """
    config = get_config()
    api_validation = config.api_keys.validate()
    
    # プロバイダー情報の定義
    providers = {
        "openai": {
            "name": "OpenAI GPT",
            "description": "高精度で創造的な表現",
            "icon": "🤖",
            "available": api_validation["openai"]
        },
        "gemini": {
            "name": "Gemini",
            "description": "バランスの取れた生成",
            "icon": "✨",
            "available": api_validation["gemini"]
        },
        "anthropic": {
            "name": "Claude",
            "description": "自然で読みやすい文章",
            "icon": "🎭",
            "available": api_validation["anthropic"]
        }
    }
    
    # 利用可能なプロバイダーのみフィルタリング
    available_providers = {k: v for k, v in providers.items() if v["available"]}
    
    if not available_providers:
        st.error("⚠️ 利用可能なLLMプロバイダーがありません。APIキーを設定してください。")
        return config.ui_settings.default_llm_provider
    
    # プロバイダー選択UI
    st.write("**🤖 LLMプロバイダー選択**")
    
    # タブ形式での表示
    tabs = st.tabs([f"{v['icon']} {v['name']}" for k, v in available_providers.items()])
    
    selected_provider = None
    for idx, (provider_key, provider_info) in enumerate(available_providers.items()):
        with tabs[idx]:
            st.write(f"**{provider_info['description']}**")
            
            # プロバイダー固有の設定
            if provider_key == "openai":
                model = st.selectbox(
                    "モデル",
                    ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    key=f"openai_model_{idx}"
                )
                st.info(f"選択中: {model}")
                
            elif provider_key == "gemini":
                model = st.selectbox(
                    "モデル",
                    ["gemini-pro", "gemini-1.5-pro"],
                    key=f"gemini_model_{idx}"
                )
                st.info(f"選択中: {model}")
                
            elif provider_key == "anthropic":
                model = st.selectbox(
                    "モデル",
                    ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    key=f"anthropic_model_{idx}"
                )
                st.info(f"選択中: {model}")
            
            if st.button(f"{provider_info['icon']} このプロバイダーを使用", key=f"use_{provider_key}_{idx}"):
                selected_provider = provider_key
    
    # デフォルトまたは選択されたプロバイダーを返す
    if selected_provider:
        st.session_state.selected_llm_provider = selected_provider
        return selected_provider
    elif "selected_llm_provider" in st.session_state:
        return st.session_state.selected_llm_provider
    else:
        # デフォルトプロバイダーを返す（利用可能なものから）
        return list(available_providers.keys())[0] if available_providers else config.ui_settings.default_llm_provider