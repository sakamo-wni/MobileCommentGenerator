"""
Debug Info Formatter

デバッグ情報を作成する
"""

from typing import Dict, Any
import logging

from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


class DebugInfoFormatter:
    """デバッグ情報のフォーマッター"""

    def create_debug_info(self, state: CommentGenerationState) -> Dict[str, Any]:
        """
        デバッグ情報を作成
        
        Args:
            state: ワークフローの状態
            
        Returns:
            デバッグ情報
        """
        return {
            "state_keys": [attr for attr in dir(state) if not attr.startswith("_")],
            "retry_history": state.generation_metadata.get("evaluation_history", []),
            "node_execution_times": state.generation_metadata.get("node_execution_times", {}),
            "api_call_count": state.generation_metadata.get("api_call_count", 0),
            "cache_hits": state.generation_metadata.get("cache_hits", 0),
            "total_past_comments": len(state.past_comments) if state.past_comments else 0,
            "workflow_version": state.generation_metadata.get("execution_context", {}).get(
                "api_version", "unknown"
            ),
        }


# エクスポート
__all__ = ["DebugInfoFormatter"]