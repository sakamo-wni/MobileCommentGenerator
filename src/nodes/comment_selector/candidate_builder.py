"""コメント候補の構築機能"""

from __future__ import annotations
import logging
from typing import Any

from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class CandidateBuilder:
    """コメント候補を構築するクラス"""
    
    @staticmethod
    def create_candidate_dict(
        index: int, 
        comment: PastComment, 
        original_index: int
    ) -> dict[str, Any]:
        """候補辞書を作成
        
        Args:
            index: 候補リスト内のインデックス
            comment: 元のコメントオブジェクト
            original_index: 元のリスト内のインデックス
            
        Returns:
            候補情報を含む辞書
        """
        return {
            'index': index,
            'original_index': original_index,
            'comment': comment.comment_text,
            'comment_object': comment,
            'weather_condition': comment.weather_condition,
            'usage_count': comment.usage_count,
            'evaluation_mode': getattr(comment, 'evaluation_mode', 'standard'),
        }