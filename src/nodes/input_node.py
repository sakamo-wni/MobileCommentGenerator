"""
入力ノード

ユーザー入力を受け取り、初期状態を設定するLangGraphノード
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import pytz

from src.data.comment_generation_state import CommentGenerationState
from src.data.location.models import Location
from src.data.location.manager import LocationManagerRefactored
from src.config.weather_config import get_config

logger = logging.getLogger(__name__)


def input_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    ユーザー入力を受け取り、初期stateを設定

    Args:
        state: ワークフローの状態

    Returns:
        初期化された状態
    """
    logger.info("InputNode: 入力処理を開始")

    try:
        # 必須パラメータの検証
        location_name = state.location_name
        if not location_name:
            raise ValueError("location_name（地点名）は必須パラメータです")

        # デフォルト値の設定
        target_datetime = state.target_datetime
        logger.info(f"InputNode - 元のtarget_datetime: {target_datetime}")
        
        if not target_datetime:
            # 設定から何時間後の予報を使用するか取得
            config = get_config()
            forecast_hours_ahead = config.weather.forecast_hours_ahead
            jst = pytz.timezone("Asia/Tokyo")
            target_datetime = datetime.now(jst) + timedelta(hours=forecast_hours_ahead)
            state.target_datetime = target_datetime
            logger.info(f"target_datetimeが未指定のため、{forecast_hours_ahead}時間後を使用: {target_datetime}")
        else:
            logger.info(f"既存のtarget_datetimeを使用: {target_datetime}")
        
        logger.info(f"InputNode - 最終的なtarget_datetime: {state.target_datetime}")

        # Location オブジェクトの作成
        location = _create_location(location_name)
        state.location = location

        # LLMプロバイダーのデフォルト設定
        if not state.llm_provider:
            state.llm_provider = "openai"
            logger.info("llm_providerが未指定のため、デフォルト'openai'を使用")

        # 初期化
        state.retry_count = 0
        state.errors = []
        state.warnings = []

        # メタデータに実行開始時刻を記録
        state.update_metadata("execution_start_time", datetime.now().isoformat())

        # 入力パラメータのログ
        logger.info(
            f"入力パラメータ: location={location_name}, "
            f"datetime={target_datetime}, "
            f"llm_provider={state.llm_provider}"
        )

        # メタデータに入力処理完了を記録
        state.update_metadata("input_processed", True)

    except Exception as e:
        logger.error(f"入力処理中にエラー: {str(e)}")
        state.add_error(f"InputNode: {str(e)}", "input_node")
        state.update_metadata("input_processed", False)

    return state


def _create_location(location_name: str) -> Location:
    """
    地点名からLocationオブジェクトを作成

    LocationManagerを使用してCSVファイルから地点情報を取得
    """
    # デバッグ: 入力された地点名をログ出力
    logger.info(f"_create_location called with: {repr(location_name)}")

    # カンマが含まれている場合は地点名部分のみを抽出
    if "," in location_name:
        actual_location_name = location_name.split(",")[0].strip()
        logger.info(f"Comma found in location_name, extracted: {repr(actual_location_name)}")
    else:
        actual_location_name = location_name.strip()

    # LocationManagerインスタンスを作成
    location_manager = LocationManagerRefactored()

    # 地点を検索
    location = location_manager.get_location(actual_location_name)

    if location:
        logger.info(
            f"地点情報を取得: {actual_location_name} -> {location.prefecture} ({location.latitude}, {location.longitude})"
        )
        return location
    else:
        # 登録されていない地点の場合はデフォルト（東京）を使用
        logger.warning(
            f"未登録の地点名: {actual_location_name}({repr(location_name)})。東京の座標を使用します"
        )
        # 東京の地点を検索
        tokyo = location_manager.get_location("東京")
        if tokyo:
            # 東京の情報を使用するが、nameは元の名前を保持
            return Location(
                name=actual_location_name,
                normalized_name=actual_location_name,
                latitude=tokyo.latitude,
                longitude=tokyo.longitude,
                region=tokyo.region,
                prefecture=tokyo.prefecture,
            )
        else:
            # Fallback to hardcoded Tokyo coordinates
            return Location(
                name=actual_location_name,
                normalized_name=actual_location_name,
                latitude=35.6768601,
                longitude=139.7638947,
                region="関東",
                prefecture="東京都",
            )


def _get_default_preferences() -> Dict[str, Any]:
    """
    デフォルトのユーザー設定を取得
    """
    return {
        "style": "casual",  # casual/formal/friendly
        "length": "medium",  # short/medium/long
        "emoji_usage": True,
        "weather_focus": "balanced",  # weather/advice/balanced
        "positivity": "positive",  # positive/neutral/realistic
        "personalization": True,
        "seasonal_awareness": True,
        "time_awareness": True,
        "evaluation_weights": None,  # Use default weights
    }


def _generate_request_id() -> str:
    """
    ユニークなリクエストIDを生成
    """
    import uuid

    return str(uuid.uuid4())


def _validate_input_parameters(state: CommentGenerationState):
    """
    入力パラメータの詳細検証
    """
    # 地点名の検証
    location_name = state.location_name if state.location_name else ""
    if len(location_name) > 50:
        raise ValueError("地点名は50文字以内で指定してください")

    if not location_name.replace(" ", "").replace("　", ""):
        raise ValueError("地点名が空白のみです")

    # 日時の検証
    target_datetime = state.target_datetime
    if target_datetime:
        # 未来すぎる日時のチェック（7日後まで）
        max_future = datetime.now() + timedelta(days=7)
        if target_datetime > max_future:
            state.add_warning("7日以上先の日時が指定されています", "input")

        # 過去すぎる日時のチェック（1年前まで）
        min_past = datetime.now() - timedelta(days=365)
        if target_datetime < min_past:
            state.add_warning("1年以上前の日時が指定されています", "input")

    # LLMプロバイダーの検証
    valid_providers = ["openai", "gemini", "anthropic"]
    llm_provider = state.llm_provider.lower() if state.llm_provider else ""
    if llm_provider not in valid_providers:
        raise ValueError(
            f"無効なLLMプロバイダー: {llm_provider}。" f"有効な値: {', '.join(valid_providers)}"
        )

    # ユーザー設定の検証
    preferences = getattr(state, "user_preferences", {})
    if preferences:
        _validate_user_preferences(preferences)


def _validate_user_preferences(preferences: Dict[str, Any]):
    """
    ユーザー設定の検証
    """
    # スタイルの検証
    valid_styles = ["casual", "formal", "friendly"]
    style = preferences.get("style", "casual")
    if style not in valid_styles:
        preferences["style"] = "casual"
        logger.warning(f"無効なstyle '{style}' が指定されました。デフォルト 'casual' を使用")

    # 長さの検証
    valid_lengths = ["short", "medium", "long"]
    length = preferences.get("length", "medium")
    if length not in valid_lengths:
        preferences["length"] = "medium"
        logger.warning(f"無効なlength '{length}' が指定されました。デフォルト 'medium' を使用")

    # ブール値の検証
    bool_keys = ["emoji_usage", "personalization", "seasonal_awareness", "time_awareness"]
    for key in bool_keys:
        if key in preferences and not isinstance(preferences[key], bool):
            preferences[key] = True
            logger.warning(f"{key} はブール値である必要があります。デフォルト True を使用")


def _initialize_minimal_state(state: CommentGenerationState):
    """
    エラー時の最小限の状態初期化
    """
    if not state.location_name:
        state.location_name = "東京"

    if not state.target_datetime:
        state.target_datetime = datetime.now()

    if not state.llm_provider:
        state.llm_provider = "openai"

    state.retry_count = 0
    state.update_metadata("input_processed", False)


# エクスポート
__all__ = ["input_node"]
