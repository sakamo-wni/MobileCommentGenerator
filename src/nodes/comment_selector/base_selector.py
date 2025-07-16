"""コメント選択の基本クラス"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any
from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.config.config import get_severe_weather_config

from .llm_selector import LLMCommentSelector
from .validation import CommentValidator
from .utils import CommentUtils
from .strategies import (
    RainCommentStrategy,
    MinimalValidationStrategy,
    AlternativeSelectionStrategy
)

logger = logging.getLogger(__name__)

# 連続雨判定の閾値（時間）
CONTINUOUS_RAIN_THRESHOLD_HOURS = 4


class CommentSelector:
    """コメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager, validator: WeatherCommentValidator):
        self.llm_manager = llm_manager
        self.validator = validator
        self.severe_config = get_severe_weather_config()
        self.llm_selector = LLMCommentSelector(llm_manager)
        self.comment_validator = CommentValidator(validator, self.severe_config)
        self.utils = CommentUtils()
        self.alternative_strategy = AlternativeSelectionStrategy(self.utils, self.validator, self.comment_validator)
    
    def select_optimal_comment_pair(
        self, 
        weather_comments: list[PastComment], 
        advice_comments: list[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: CommentGenerationState | None = None,
        exclude_weather_comment: str | None = None,
        exclude_advice_comment: str | None = None
    ) -> CommentPair | None:
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
            error_details = {
                "error_type": "comment_selection_failed",
                "weather_comment_selected": best_weather is not None,
                "advice_comment_selected": best_advice is not None,
                "filtered_weather_count": len(filtered_weather),
                "filtered_advice_count": len(filtered_advice),
                "original_weather_count": len(weather_comments),
                "original_advice_count": len(advice_comments),
                "weather_data": {
                    "temperature": weather_data.temperature,
                    "weather_description": weather_data.weather_description,
                    "precipitation": weather_data.precipitation,
                    "wind_speed": weather_data.wind_speed
                },
                "location": location_name,
                "target_datetime": target_datetime.isoformat() if target_datetime else None
            }
            
            if not best_weather:
                logger.error("天気コメントの選択が失敗しました")
                error_details["weather_comment_error"] = "No suitable weather comment found after filtering"
            if not best_advice:
                logger.error("アドバイスコメントの選択が失敗しました")
                error_details["advice_comment_error"] = "No suitable advice comment found after filtering"
            
            logger.error(f"詳細なエラー情報: {error_details}")
            raise ValueError(f"コメント選択に失敗しました: {error_details}")
            
        # ペア作成前の最終バリデーション
        if not self.comment_validator.validate_comment_pair(best_weather, best_advice, weather_data, state):
            # 重複回避のための代替選択を試行
            alternative_pair = self.alternative_strategy.select_alternative_non_duplicate_pair(
                filtered_weather, filtered_advice, weather_data, location_name, target_datetime, state
            )
            if alternative_pair:
                return alternative_pair
            
            # 代替選択も失敗した場合はエラー
            validation_error = {
                "error_type": "comment_pair_validation_failed",
                "weather_comment": best_weather.comment_text,
                "advice_comment": best_advice.comment_text,
                "validation_reason": "Comment pair failed consistency validation",
                "weather_data": {
                    "temperature": weather_data.temperature,
                    "weather_description": weather_data.weather_description,
                    "precipitation": weather_data.precipitation
                }
            }
            logger.error(f"コメントペアのバリデーションエラー: {validation_error}")
            raise ValueError(f"コメントペアの検証に失敗しました: {validation_error}")
        
        return CommentPair(
            weather_comment=best_weather,
            advice_comment=best_advice,
            similarity_score=1.0,
            selection_reason="LLMによる最適選択",
        )
    
    def _select_best_weather_comment(
        self, 
        comments: list[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """天気コメントの選択"""
        if not comments:
            return None
            
        # 天気コメント用の候補を準備
        candidates = self.utils.prepare_weather_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime, state
        )
        
        if not candidates:
            logger.warning("適切な天気コメント候補が見つかりません")
            # フィルタリングが厳しすぎる場合、最低限のチェックで選択
            return MinimalValidationStrategy.select_weather_with_minimal_validation(comments, weather_data)
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.WEATHER_COMMENT, state
        )
    
    def _select_best_advice_comment(
        self, 
        comments: list[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """アドバイスコメントの選択"""
        if not comments:
            return None
            
        # アドバイス用の候補を準備
        candidates = self.utils.prepare_advice_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime
        )
        
        if not candidates:
            logger.warning("適切なアドバイス候補が見つかりません")
            # フィルタリングが厳しすぎる場合、最低限のチェックで選択
            return MinimalValidationStrategy.select_advice_with_minimal_validation(comments, weather_data)
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.ADVICE, state
        )
    
    def _find_rain_appropriate_weather_comment(
        self, 
        comments: list[PastComment],
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """雨に適した天気コメントを探す"""
        return RainCommentStrategy.find_rain_appropriate_weather_comment(comments, weather_data, state)
    
    def _find_rain_appropriate_advice_comment(
        self, 
        comments: list[PastComment],
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """雨に適したアドバイスコメントを探す"""
        return RainCommentStrategy.find_rain_appropriate_advice_comment(comments, weather_data, state)
