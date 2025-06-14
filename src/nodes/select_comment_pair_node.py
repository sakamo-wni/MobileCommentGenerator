"""コメントペア選択ノード - LLMを使用して適切なコメントペアを選択"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.comment_config import get_comment_config
from src.config.severe_weather_config import get_severe_weather_config
from src.data.forecast_cache import ForecastCache
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.common_utils import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES
from src.nodes.comment_selector import CommentSelector

logger = logging.getLogger(__name__)


def select_comment_pair_node(state: CommentGenerationState) -> CommentGenerationState:
    """LLMを使用して適切なコメントペアを選択"""
    logger.info("SelectCommentPairNode: LLMによるコメントペア選択を開始")

    try:
        # 入力データの検証
        weather_data = state.weather_data
        past_comments = state.past_comments
        location_name = state.location_name
        target_datetime = state.target_datetime or datetime.now()
        llm_provider = state.llm_provider or "openai"

        if not weather_data:
            raise ValueError("天気データが利用できません")
        if not past_comments:
            raise ValueError("過去コメントが存在しません")

        # コメントをタイプ別に分離
        collection = PastCommentCollection(past_comments)
        weather_comments = collection.filter_by_type(CommentType.WEATHER_COMMENT).comments
        advice_comments = collection.filter_by_type(CommentType.ADVICE).comments

        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")

        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")

        # コメント選択器の初期化
        llm_manager = LLMManager(provider=llm_provider)
        validator = WeatherCommentValidator()
        selector = CommentSelector(llm_manager, validator)
        
        # 最適なコメントペアを選択
        pair = selector.select_optimal_comment_pair(
            weather_comments, advice_comments, weather_data, 
            location_name, target_datetime, state
        )

        if not pair:
            raise ValueError("LLMによるコメントペアの選択に失敗しました")
            
        state.selected_pair = pair
        
        logger.info(f"選択完了 - 天気: {pair.weather_comment.comment_text}, アドバイス: {pair.advice_comment.comment_text}")
        
        # メタデータの更新
        state.update_metadata("selection_metadata", {
            "weather_comments_count": len(weather_comments),
            "advice_comments_count": len(advice_comments),
            "selection_method": "LLM",
            "llm_provider": llm_provider,
            "selected_weather_comment": pair.weather_comment.comment_text,
            "selected_advice_comment": pair.advice_comment.comment_text,
        })

    except Exception as e:
        logger.error(f"コメントペア選択中にエラー: {e!s}")
        state.add_error(f"SelectCommentPairNode: {e!s}", "select_comment_pair_node")
        raise

    return state