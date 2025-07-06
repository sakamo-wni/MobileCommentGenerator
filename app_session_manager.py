"""天気コメント生成システム - セッション管理"""

from typing import Any, TypeVar, overload

import streamlit as st

from app_interfaces import ICommentGenerationController

T = TypeVar('T')


class SessionManager:
    """Streamlitセッション状態の管理クラス

    セッション状態の初期化、取得、更新を一元管理します。
    """

    @staticmethod
    def initialize(controller: ICommentGenerationController) -> None:
        """セッション状態の初期化

        Args:
            controller: コメント生成コントローラー
        """
        defaults = {
            'generation_history': controller.generation_history,
            'selected_location': controller.get_default_locations(),
            'llm_provider': controller.get_default_llm_provider(),
            'current_result': None,
            'is_generating': False,
            'config': controller.config
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @overload
    @staticmethod
    def get(key: str) -> Any:
        """セッション状態から値を取得"""
        ...
    
    @overload
    @staticmethod
    def get(key: str, default: T) -> T:
        """セッション状態から値を取得（デフォルト値付き）"""
        ...
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """セッション状態から値を取得

        Args:
            key: 取得するキー
            default: デフォルト値

        Returns:
            セッション状態の値またはデフォルト値
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """セッション状態に値を設定

        Args:
            key: 設定するキー
            value: 設定する値
        """
        st.session_state[key] = value

    @staticmethod
    def update(updates: dict[str, Any]) -> None:
        """セッション状態を一括更新

        Args:
            updates: 更新する値の辞書
        """
        for key, value in updates.items():
            st.session_state[key] = value

    @staticmethod
    def is_generating() -> bool:
        """生成中かどうかを取得

        Returns:
            bool: 生成中の場合True
        """
        return st.session_state.get('is_generating', False)

    @staticmethod
    def set_generating(value: bool) -> None:
        """生成中フラグを設定

        Args:
            value: 生成中フラグ
        """
        st.session_state.is_generating = value

    @staticmethod
    def get_current_result() -> dict[str, Any] | None:
        """現在の生成結果を取得

        Returns:
            Optional[dict]: 生成結果
        """
        return st.session_state.get('current_result')

    @staticmethod
    def set_current_result(result: dict[str, Any] | None) -> None:
        """現在の生成結果を設定

        Args:
            result: 生成結果
        """
        st.session_state.current_result = result

    @staticmethod
    def get_selected_location() -> list[str]:
        """選択された地点を取得

        Returns:
            list[str]: 地点リスト
        """
        return st.session_state.get('selected_location', [])

    @staticmethod
    def set_selected_location(locations: list[str]) -> None:
        """選択された地点を設定

        Args:
            locations: 地点リスト
        """
        st.session_state.selected_location = locations

    @staticmethod
    def get_llm_provider() -> str:
        """LLMプロバイダーを取得

        Returns:
            str: LLMプロバイダー名
        """
        return st.session_state.get('llm_provider', '')

    @staticmethod
    def set_llm_provider(provider: str) -> None:
        """LLMプロバイダーを設定

        Args:
            provider: LLMプロバイダー名
        """
        st.session_state.llm_provider = provider
