"""セッション状態管理の実装"""

import logging
from typing import Any

import streamlit as st

from app_interfaces import ISessionManager

logger = logging.getLogger(__name__)


class SessionManager(ISessionManager):
    """Streamlitのセッション状態を管理するクラス
    
    セッション状態の初期化、取得、設定を一元管理し、
    アプリケーション全体で一貫したセッション管理を提供します。
    
    このクラスはISessionManagerインターフェースを実装し、
    Streamlitのst.session_stateへの依存を隔離します。
    これにより、テスト時のモック化や将来的な実装の変更が容易になります。
    
    主な機能:
    - セッション状態の初期化（デフォルト値の設定）
    - 値の取得、設定、更新、削除
    - セッション状態の一括クリア
    - 存在確認と全値の取得
    
    使用例:
        session = SessionManager()
        session.initialize({'user_name': 'guest', 'count': 0})
        session.set('count', session.get('count', 0) + 1)
        session.update({'user_name': 'John', 'logged_in': True})
    """

    def __init__(self):
        """セッションマネージャーの初期化"""
        self._initialized = False

    def initialize(self, defaults: dict[str, Any]) -> None:
        """セッション状態を初期化
        
        Args:
            defaults: デフォルト値の辞書
        """
        if self._initialized:
            logger.debug("Session already initialized, skipping...")
            return

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
                logger.debug(f"Initialized session key '{key}' with value: {value}")

        self._initialized = True
        logger.info(f"Session initialized with {len(defaults)} default values")

    def get(self, key: str, default: Any = None) -> Any:
        """セッション値を取得
        
        Args:
            key: 取得するキー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            セッション値またはデフォルト値
        """
        value = st.session_state.get(key, default)
        logger.debug(f"Retrieved session key '{key}': {value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """セッション値を設定
        
        Args:
            key: 設定するキー
            value: 設定する値
        """
        old_value = st.session_state.get(key)
        st.session_state[key] = value
        logger.debug(f"Set session key '{key}': {old_value} -> {value}")

    def update(self, updates: dict[str, Any]) -> None:
        """複数のセッション値を更新
        
        Args:
            updates: 更新する値の辞書
        """
        for key, value in updates.items():
            self.set(key, value)
        logger.info(f"Updated {len(updates)} session values")

    def has(self, key: str) -> bool:
        """キーの存在確認
        
        Args:
            key: 確認するキー
            
        Returns:
            キーが存在する場合True
        """
        exists = key in st.session_state
        logger.debug(f"Session key '{key}' exists: {exists}")
        return exists

    def remove(self, key: str) -> None:
        """セッション値を削除
        
        Args:
            key: 削除するキー
        """
        if key in st.session_state:
            del st.session_state[key]
            logger.debug(f"Removed session key '{key}'")
        else:
            logger.warning(f"Attempted to remove non-existent session key '{key}'")

    def clear(self) -> None:
        """全てのセッション値をクリア"""
        count = len(st.session_state)
        st.session_state.clear()
        self._initialized = False
        logger.info(f"Cleared all {count} session values")

    def get_all(self) -> dict[str, Any]:
        """全てのセッション値を取得
        
        Returns:
            セッション状態の辞書
        """
        return dict(st.session_state)
