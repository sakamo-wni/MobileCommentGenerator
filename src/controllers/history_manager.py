"""履歴管理を専門に扱うマネージャー

CommentGenerationControllerから履歴管理の責務を分離。
"""

import logging
from typing import from src.ui.streamlit_utils import load_history, save_to_history

logger = logging.getLogger(__name__)


class HistoryManager:
    """コメント生成履歴を管理するクラス"""
    
    def __init__(self):
        self._generation_history: list[dict[str, str | None]] = None
        
    @property
    def generation_history(self) -> list[dict[str, str]]:
        """生成履歴を取得（遅延読み込み）"""
        if self._generation_history is None:
            self._generation_history = load_history()
        return self._generation_history
    
    def save_generation_result(self, result: Dict, location: str, llm_provider: str) -> None:
        """生成結果を履歴に保存"""
        if result.get('success'):
            save_to_history(result, location, llm_provider)
            # 履歴キャッシュをクリア
            self._generation_history = None
            logger.info(f"Saved to history: location={location}, provider={llm_provider}")
    
    def clear_cache(self) -> None:
        """履歴キャッシュをクリア"""
        self._generation_history = None
        
    def get_recent_history(self, limit: int = 10) -> list[dict[str, str]]:
        """最近の履歴を取得"""
        history = self.generation_history
        return history[-limit:] if len(history) > limit else history
    
    def get_history_by_location(self, location: str) -> list[dict[str, str]]:
        """特定の地点の履歴を取得"""
        return [
            h for h in self.generation_history 
            if h.get('location') == location
        ]