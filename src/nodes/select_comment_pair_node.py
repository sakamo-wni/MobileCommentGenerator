"""コメントペア選択ノード - LLMを使用して適切なコメントペアを選択"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any
from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.config import get_comment_config, get_severe_weather_config
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.constants.content_constants import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES
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
        from src.config.config import get_config
        config = get_config()
        llm_manager = LLMManager(provider=llm_provider, config=config)
        validator = WeatherCommentValidator()
        selector = CommentSelector(llm_manager, validator)
        
        # 前回のコメントを除外するかどうかを確認
        exclude_previous = getattr(state, 'exclude_previous', False)
        logger.info(f"🔄 exclude_previous フラグ: {exclude_previous}")
        previous_weather_comment = None
        previous_advice_comment = None
        
        if exclude_previous:
            # 前回の生成履歴から除外すべきコメントを取得
            from src.ui.streamlit_utils import load_history
            try:
                history = load_history()
                logger.info(f"🔄 再生成モード - 履歴読み込み結果: {len(history) if history else 0}件")
                if history:
                    # 同じ地点の最新の履歴を取得
                    location_history = [h for h in history if h.get('location') == location_name]
                    logger.info(f"🔄 {location_name}の履歴: {len(location_history)}件")
                    if location_history:
                        latest = location_history[-1]
                        previous_weather_comment = latest.get('comment')
                        previous_advice_comment = latest.get('advice_comment')
                        logger.info(f"🔄 前回のコメントを除外対象として設定:")
                        logger.info(f"🔄   天気コメント: '{previous_weather_comment}'")
                        logger.info(f"🔄   アドバイス: '{previous_advice_comment}'")
                    else:
                        logger.info(f"🔄 {location_name}の履歴が見つかりません")
                else:
                    logger.info("🔄 履歴ファイルが空または存在しません")
            except Exception as e:
                logger.warning(f"🔄 履歴の読み込みに失敗しましたが、処理を続行します: {e}")
        
        # 最適なコメントペアを選択
        try:
            pair = selector.select_optimal_comment_pair(
                weather_comments, advice_comments, weather_data, 
                location_name, target_datetime, state,
                exclude_weather_comment=previous_weather_comment,
                exclude_advice_comment=previous_advice_comment
            )
        except Exception as selection_error:
            logger.error(f"コメントペア選択中に例外が発生: {selection_error}")
            logger.error(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")
            logger.error(f"天気データ: {weather_data.weather_description}, 気温: {weather_data.temperature}°C, 降水量: {weather_data.precipitation}mm")
            raise ValueError(f"LLMによるコメントペアの選択に失敗しました: {selection_error}")

        if not pair:
            logger.error("select_optimal_comment_pairがNoneを返しました")
            logger.error(f"フィルタリング前 - 天気: {len(weather_comments)}件, アドバイス: {len(advice_comments)}件")
            logger.error(f"天気データ: {weather_data.weather_description}, 気温: {weather_data.temperature}°C, 降水量: {weather_data.precipitation}mm")
            logger.error(f"除外対象 - 天気: '{previous_weather_comment}', アドバイス: '{previous_advice_comment}'")
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