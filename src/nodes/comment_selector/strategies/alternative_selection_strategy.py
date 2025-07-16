"""
Alternative selection strategy

代替選択戦略（重複回避）
"""

from __future__ import annotations

import logging
from datetime import datetime
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


class AlternativeSelectionStrategy:
    """代替選択戦略（重複回避）"""
    
    def __init__(self, utils, validator, comment_validator):
        self.utils = utils
        self.validator = validator
        self.comment_validator = comment_validator
    
    def select_alternative_non_duplicate_pair(
        self,
        weather_comments: list[PastComment],
        advice_comments: list[PastComment],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        state: CommentGenerationState | None = None
    ) -> CommentPair | None:
        """重複を回避する代替ペア選択"""
        logger.info("重複回避のための代替コメントペア選択を開始")
        
        # 複数の候補を生成して重複しないペアを探す
        weather_candidates = self.utils.prepare_weather_candidates(
            weather_comments, weather_data, self.validator, self.comment_validator, target_datetime, state
        )
        advice_candidates = self.utils.prepare_advice_candidates(
            advice_comments, weather_data, self.validator, self.comment_validator, target_datetime
        )
        
        # 上位候補から順に試行（最大10回）
        max_attempts = min(10, len(weather_candidates), len(advice_candidates))
        
        for attempt in range(max_attempts):
            try:
                # 天気コメント候補を選択（異なるものを順番に試す）
                weather_idx = attempt % len(weather_candidates)
                weather_candidate = weather_candidates[weather_idx]['comment_object']
                
                # アドバイス候補を選択
                advice_idx = attempt % len(advice_candidates)
                advice_candidate = advice_candidates[advice_idx]['comment_object']
                
                # 包括的バリデーションチェック（新しい一貫性チェック含む）
                if self.comment_validator.validate_comment_pair(weather_candidate, advice_candidate, weather_data, state):
                    logger.info(f"代替ペア選択成功 (試行{attempt+1}): 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                    return CommentPair(
                        weather_comment=weather_candidate,
                        advice_comment=advice_candidate,
                        similarity_score=0.8,  # 代替選択なので若干低めのスコア
                        selection_reason=f"重複回避代替選択（試行{attempt+1}回目）"
                    )
                
                logger.debug(f"試行{attempt+1}: 重複または無効 - 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                
            except Exception as e:
                logger.warning(f"代替選択試行{attempt+1}でエラー: {e}")
                continue
        
        logger.warning("重複しない代替ペアの選択に失敗")
        return None