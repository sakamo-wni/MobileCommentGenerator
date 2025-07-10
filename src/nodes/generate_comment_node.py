"""天気コメント生成ノード

LLMを使用して天気情報と過去コメントを基にコメントを生成する。
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# langgraph nodeデコレータは新バージョンでは不要

from src.data.comment_generation_state import CommentGenerationState
from src.llm.llm_manager import LLMManager
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.config.weather_config import get_config
from .helpers import (
    get_ng_words,
    get_time_period,
    get_season,
    analyze_temperature_differences,
    check_and_fix_weather_comment_safety
)

logger = logging.getLogger(__name__)


def generate_comment_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    LLMを使用してコメントを生成するノード。

    Args:
        state: 現在のワークフロー状態

    Returns:
        更新された状態（generated_comment追加）
    """
    try:
        logger.info("Starting comment generation")

        # 必要なデータの確認
        weather_data = state.weather_data
        selected_pair = state.selected_pair
        llm_provider = state.llm_provider if state.llm_provider else "openai"

        if not weather_data:
            raise ValueError("Weather data is required for comment generation")

        if not selected_pair:
            raise ValueError("Selected comment pair is required for generation")

        # LLMマネージャーの初期化
        from src.config.config import Config
        config = Config()
        llm_manager = LLMManager(provider=llm_provider, config=config)

        # 制約条件の設定
        constraints = {
            "max_length": 15,
            "ng_words": get_ng_words(),
            "time_period": get_time_period(state.target_datetime),
            "season": get_season(state.target_datetime),
        }

        # 選択されたコメントペアから最終コメントを構成
        # S3から選択された天気コメントとアドバイスをそのまま組み合わせる
        weather_comment = (
            selected_pair.weather_comment.comment_text if selected_pair.weather_comment else ""
        )
        advice_comment = (
            selected_pair.advice_comment.comment_text if selected_pair.advice_comment else ""
        )

        # コメントの安全性チェックと修正
        weather_comment, advice_comment = check_and_fix_weather_comment_safety(
            weather_data, weather_comment, advice_comment, state
        )

        # 最終コメント構成
        if weather_comment and advice_comment:
            generated_comment = f"{weather_comment}　{advice_comment}"
        elif weather_comment:
            generated_comment = weather_comment
        elif advice_comment:
            generated_comment = advice_comment
        else:
            generated_comment = "コメントが選択できませんでした"

        logger.info(f"Final comment (from CSV): {generated_comment}")
        logger.info(f"  - Weather part: {weather_comment}")
        logger.info(f"  - Advice part: {advice_comment}")

        # 状態の更新
        state.generated_comment = generated_comment
        state.update_metadata("llm_provider", llm_provider)
        state.update_metadata("generation_timestamp", datetime.now().isoformat())
        state.update_metadata("constraints_applied", constraints)
        state.update_metadata(
            "selected_past_comments",
            [
                {"type": "weather", "text": weather_comment} if weather_comment else None,
                {"type": "advice", "text": advice_comment} if advice_comment else None,
            ],
        )
        state.update_metadata("comment_source", "S3_PAST_COMMENTS")

        # 気象データをメタデータに追加
        if weather_data:
            state.update_metadata("temperature", weather_data.temperature)
            state.update_metadata("weather_condition", weather_data.weather_description)
            state.update_metadata("humidity", weather_data.humidity)
            state.update_metadata("wind_speed", weather_data.wind_speed)
            
            # 気温差情報をメタデータに追加
            temperature_differences = state.generation_metadata.get("temperature_differences", {})
            if temperature_differences:
                state.update_metadata("previous_day_temperature_diff", temperature_differences.get("previous_day_diff"))
                state.update_metadata("twelve_hours_ago_temperature_diff", temperature_differences.get("twelve_hours_ago_diff"))
                state.update_metadata("daily_temperature_range", temperature_differences.get("daily_range"))
                
                # 気温差の特徴を分析
                temp_diff_analysis = analyze_temperature_differences(temperature_differences, weather_data.temperature)
                state.update_metadata("temperature_analysis", temp_diff_analysis)

        return state

    except Exception as e:
        logger.error(f"Error in generate_comment_node: {str(e)}")
        state.add_error(str(e), "generate_comment")

        # エラーを再発生させて適切に処理
        raise




# エクスポート
__all__ = [
    "generate_comment_node",
]
