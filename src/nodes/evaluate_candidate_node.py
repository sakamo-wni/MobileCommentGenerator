"""
コメント候補評価ノード

選択されたコメントペアを評価し、品質を検証するLangGraphノード
"""

from typing import Dict, Any, Optional, Union
import logging
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast
from src.data.evaluation_criteria import EvaluationContext, EvaluationCriteria
from src.data.past_comment import PastComment
from src.algorithms.comment_evaluator import CommentEvaluator
from src.utils.exceptions import DataValidationError, NodeExecutionError

logger = logging.getLogger(__name__)


def evaluate_candidate_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    選択されたコメントペアを評価し、品質を検証

    Args:
        state: ワークフローの状態

    Returns:
        評価結果を含む更新された状態
    """
    logger.info("EvaluateCandidateNode: コメント候補評価を開始")

    try:
        # 必要なデータの取得
        selected_pair_data = state.selected_pair
        weather_data_dict = state.weather_data
        location_name = state.location_name or ""
        target_datetime = state.target_datetime or datetime.now()
        user_preferences = getattr(state, "user_preferences", {})

        if not selected_pair_data:
            raise DataValidationError("選択されたコメントペアが存在しません")

        if not weather_data_dict:
            raise DataValidationError("天気データが利用できません")

        # データの復元
        comment_pair = _restore_comment_pair(selected_pair_data)
        weather_data = _restore_weather_data(weather_data_dict)

        # 評価コンテキストの作成
        context = EvaluationContext(
            weather_condition=weather_data.weather_description,
            location=location_name,
            target_datetime=target_datetime,
            user_preferences=user_preferences,
            history=getattr(state, "evaluation_history", []),
        )

        # 評価器の初期化（カスタム重みがあれば使用）
        custom_weights = _get_custom_weights(user_preferences)
        evaluator = CommentEvaluator(weights=custom_weights)

        # 評価実行
        evaluation_result = evaluator.evaluate_comment_pair(comment_pair, context, weather_data)

        # 状態の更新
        state.validation_result = evaluation_result
        state.should_retry = not evaluation_result.is_valid

        # 評価結果の詳細をログ出力
        logger.info("=" * 60)
        logger.info("【評価結果詳細】")
        logger.info(
            f"総合スコア: {evaluation_result.total_score:.2f} {'✓ 合格' if evaluation_result.is_valid else '✗ 不合格'}"
        )
        logger.info("各評価基準のスコア:")
        for score in evaluation_result.criterion_scores:
            logger.info(f"  - {score.criterion.value}: {score.score:.2f} (重み: {score.weight})")
            if score.reason:
                logger.info(f"    理由: {score.reason}")
        logger.info("=" * 60)

        # リトライが必要な場合の処理
        if not evaluation_result.is_valid:
            state.increment_retry()

            # 改善提案をメタデータに記録
            state.update_metadata("improvement_suggestions", evaluation_result.suggestions)

            logger.warning("=" * 60)
            logger.warning(
                f"評価不合格: スコア={evaluation_result.total_score:.2f}, リトライ回数={state.retry_count}"
            )
            logger.warning("改善提案:")
            for suggestion in evaluation_result.suggestions:
                logger.warning(f"  - {suggestion}")
            logger.warning("=" * 60)

            # 評価履歴に追加
            _add_to_evaluation_history(state, evaluation_result)
        else:
            logger.info(f"評価合格: スコア={evaluation_result.total_score:.2f}")

        # デバッグ情報をメタデータに記録
        state.update_metadata(
            "evaluation_metadata",
            {
                "total_score": evaluation_result.total_score,
                "average_score": evaluation_result.average_score,
                "pass_rate": evaluation_result.pass_rate,
                "failed_criteria": [c for c in evaluation_result.failed_criteria],
                "suggestions_count": len(evaluation_result.suggestions),
            },
        )

    except DataValidationError as e:
        logger.error(f"データ検証エラー: {str(e)}")
        state.add_error(f"EvaluateCandidateNode: {str(e)}", "evaluate_candidate_node")
        raise NodeExecutionError(f"評価ノード実行エラー: {str(e)}") from e
    except (ValueError, TypeError) as e:
        logger.error(f"コメント評価中にエラー: {str(e)}")
        state.add_error(f"EvaluateCandidateNode: {str(e)}", "evaluate_candidate_node")

        # エラー時はデフォルトで合格とする（フローを継続）
        from src.data.evaluation_criteria import EvaluationResult, CriterionScore

        state.validation_result = EvaluationResult(
            total_score=0.5,
            is_valid=True,
            criterion_scores=[],
            failed_criteria=[],
            suggestions=["評価エラーのため、デフォルト設定で続行"],
        )
        state.should_retry = False

    return state


def _restore_comment_pair(pair_data: Any) -> CommentPair:
    """
    辞書データまたはCommentPairオブジェクトから適切な形式を返す
    """
    # すでにCommentPairオブジェクトの場合はそのまま返す
    if isinstance(pair_data, CommentPair):
        return pair_data

    # 辞書形式の場合は復元処理を行う
    if isinstance(pair_data, dict):
        # PastCommentオブジェクトの復元
        weather_comment = PastComment(
            comment_text=pair_data["weather_comment"]["comment_text"],
            comment_type=pair_data["weather_comment"]["comment_type"],
            location=pair_data["weather_comment"].get("location", ""),
            weather_condition=pair_data["weather_comment"].get("weather_condition"),
            temperature=pair_data["weather_comment"].get("temperature"),
            datetime=(
                datetime.fromisoformat(pair_data["weather_comment"]["datetime"])
                if isinstance(pair_data["weather_comment"].get("datetime"), str)
                else pair_data["weather_comment"].get("datetime", datetime.now())
            ),
        )

        advice_comment = PastComment(
            comment_text=pair_data["advice_comment"]["comment_text"],
            comment_type=pair_data["advice_comment"]["comment_type"],
            location=pair_data["advice_comment"].get("location", ""),
            weather_condition=pair_data["advice_comment"].get("weather_condition"),
            temperature=pair_data["advice_comment"].get("temperature"),
            datetime=(
                datetime.fromisoformat(pair_data["advice_comment"]["datetime"])
                if isinstance(pair_data["advice_comment"].get("datetime"), str)
                else pair_data["advice_comment"].get("datetime", datetime.now())
            ),
        )

        return CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=pair_data.get("similarity_score", 0.0),
            selection_reason=pair_data.get("selection_reason", ""),
            metadata=pair_data.get("metadata", {}),
        )

    raise TypeError(f"Expected CommentPair or dict, got {type(pair_data)}")


def _restore_weather_data(weather_data: Union[WeatherForecast, Dict[str, Any]]) -> WeatherForecast:
    """
    辞書データまたはWeatherForecastオブジェクトからWeatherForecastオブジェクトを復元
    """
    # すでにWeatherForecastオブジェクトの場合はそのまま返す
    if isinstance(weather_data, WeatherForecast):
        return weather_data

    # 辞書の場合は変換
    if isinstance(weather_data, dict):
        return WeatherForecast(
            location=weather_data.get("location", ""),
            datetime=(
                datetime.fromisoformat(weather_data["datetime"])
                if isinstance(weather_data.get("datetime"), str)
                else weather_data.get("datetime", datetime.now())
            ),
            temperature=weather_data.get("temperature", 20.0),
            weather_code=weather_data.get("weather_code", ""),
            weather_description=weather_data.get("weather_description", ""),
            precipitation=weather_data.get("precipitation", 0.0),
            humidity=weather_data.get("humidity", 50.0),
            wind_speed=weather_data.get("wind_speed", 0.0),
            wind_direction=weather_data.get("wind_direction", ""),
        )

    raise TypeError(f"Expected WeatherForecast or dict, got {type(weather_data)}")


def _get_custom_weights(
    user_preferences: Dict[str, Any],
) -> Optional[Dict[EvaluationCriteria, float]]:
    """
    ユーザー設定からカスタム評価重みを取得
    """
    weight_settings = user_preferences.get("evaluation_weights")
    if not weight_settings:
        return None

    # 文字列キーをEnumに変換
    custom_weights = {}
    for criterion_name, weight in weight_settings.items():
        try:
            criterion = EvaluationCriteria(criterion_name)
            custom_weights[criterion] = float(weight)
        except (ValueError, TypeError):
            logger.warning(f"無効な評価基準または重み: {criterion_name}={weight}")

    return custom_weights if custom_weights else None


def _add_to_evaluation_history(state: CommentGenerationState, evaluation_result):
    """
    評価履歴に結果を追加
    """
    history = getattr(state, "evaluation_history", [])

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "retry_count": state.retry_count,
        "total_score": evaluation_result.total_score,
        "is_valid": evaluation_result.is_valid,
        "failed_criteria": [c.value for c in evaluation_result.failed_criteria],
        "suggestions": evaluation_result.suggestions[:3],  # 上位3件のみ
    }

    history.append(history_entry)

    # 履歴は最新10件まで保持
    state.evaluation_history = history[-10:]


# エクスポート
__all__ = ["evaluate_candidate_node"]
