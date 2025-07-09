"""コメント選択の基本クラス"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.config.severe_weather_config import get_severe_weather_config

from .llm_selector import LLMCommentSelector
from .validation import CommentValidator
from .utils import CommentUtils

logger = logging.getLogger(__name__)


class CommentSelector:
    """コメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager, validator: WeatherCommentValidator):
        self.llm_manager = llm_manager
        self.validator = validator
        self.severe_config = get_severe_weather_config()
        self.llm_selector = LLMCommentSelector(llm_manager)
        self.comment_validator = CommentValidator(validator, self.severe_config)
        self.utils = CommentUtils()
    
    def select_optimal_comment_pair(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None,
        exclude_weather_comment: Optional[str] = None,
        exclude_advice_comment: Optional[str] = None
    ) -> Optional[CommentPair]:
        """最適なコメントペアを選択"""
        
        # 事前フィルタリング
        filtered_weather = self.validator.get_weather_appropriate_comments(
            weather_comments, weather_data, CommentType.WEATHER_COMMENT, limit=500
        )
        filtered_advice = self.validator.get_weather_appropriate_comments(
            advice_comments, weather_data, CommentType.ADVICE, limit=500
        )
        
        # 除外対象のコメントを削除
        if exclude_weather_comment:
            original_count = len(filtered_weather)
            filtered_weather = [c for c in filtered_weather 
                             if c.comment_text.strip() != exclude_weather_comment.strip()]
            logger.info(f"天気コメントから前回の生成結果を除外: '{exclude_weather_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_weather)}件)")
            
        if exclude_advice_comment:
            original_count = len(filtered_advice)
            filtered_advice = [c for c in filtered_advice 
                             if c.comment_text.strip() != exclude_advice_comment.strip()]
            logger.info(f"アドバイスコメントから前回の生成結果を除外: '{exclude_advice_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_advice)}件)")
        
        logger.info(f"フィルタリング結果 - 天気: {len(weather_comments)} -> {len(filtered_weather)}")
        logger.info(f"フィルタリング結果 - アドバイス: {len(advice_comments)} -> {len(filtered_advice)}")
        
        # デバッグ: 元のコメント数と内容を確認
        logger.debug(f"元の天気コメント総数: {len(weather_comments)}")
        logger.debug(f"元のアドバイスコメント総数: {len(advice_comments)}")
        
        # 最適なコメントを選択
        best_weather = self._select_best_weather_comment(
            filtered_weather, weather_data, location_name, target_datetime, state
        )
        best_advice = self._select_best_advice_comment(
            filtered_advice, weather_data, location_name, target_datetime, state
        )
        
        if not best_weather or not best_advice:
            return None
            
        # ペア作成前の最終バリデーション
        if not self.comment_validator.validate_comment_pair(best_weather, best_advice, weather_data, state):
            # 重複回避のための代替選択を試行
            alternative_pair = self._select_alternative_non_duplicate_pair(
                filtered_weather, filtered_advice, weather_data, location_name, target_datetime, state
            )
            if alternative_pair:
                return alternative_pair
            
            # 代替選択も失敗した場合はフォールバック処理
            return self._fallback_comment_selection(
                weather_comments, advice_comments, weather_data
            )
        
        return CommentPair(
            weather_comment=best_weather,
            advice_comment=best_advice,
            similarity_score=1.0,
            selection_reason="LLMによる最適選択",
        )
    
    def _select_best_weather_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """天気コメントの選択"""
        if not comments:
            return None
            
        # 天気コメント用の候補を準備
        candidates = self.utils.prepare_weather_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime, state
        )
        
        if not candidates:
            logger.warning("適切な天気コメント候補が見つかりません")
            return None
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.WEATHER_COMMENT, state
        )
    
    def _select_best_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """アドバイスコメントの選択"""
        if not comments:
            return None
            
        # アドバイス用の候補を準備
        candidates = self.utils.prepare_advice_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime
        )
        
        if not candidates:
            logger.warning("適切なアドバイス候補が見つかりません")
            return None
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.ADVICE, state
        )
    
    def _fallback_comment_selection(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast
    ) -> Optional[CommentPair]:
        """フォールバック選択処理"""
        logger.warning("フォールバック選択を実行")
        
        # 雨の場合の特別処理
        if weather_data.precipitation > 0:
            weather_comment = self._find_rain_appropriate_weather_comment(weather_comments)
            advice_comment = self._find_rain_appropriate_advice_comment(advice_comments)
            
            if weather_comment and advice_comment:
                return CommentPair(
                    weather_comment=weather_comment,
                    advice_comment=advice_comment,
                    similarity_score=0.5,
                    selection_reason="雨天時フォールバック"
                )
        
        # 最後の手段：最初の適切なコメントを選択
        if weather_comments and advice_comments:
            return CommentPair(
                weather_comment=weather_comments[0],
                advice_comment=advice_comments[0],
                similarity_score=0.3,
                selection_reason="最終フォールバック"
            )
            
        return None
    
    def _find_rain_appropriate_weather_comment(
        self, 
        comments: List[PastComment]
    ) -> Optional[PastComment]:
        """雨に適した天気コメントを探す"""
        rain_keywords = ["雨", "降水", "にわか雨", "傘"]
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_keywords):
                return comment
        return comments[0] if comments else None
    
    def _find_rain_appropriate_advice_comment(
        self, 
        comments: List[PastComment]
    ) -> Optional[PastComment]:
        """雨に適したアドバイスコメントを探す"""
        rain_advice_keywords = ["傘", "雨具", "濡れ", "雨対策"]
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_advice_keywords):
                return comment
        return comments[0] if comments else None
    
    def _select_alternative_non_duplicate_pair(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
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