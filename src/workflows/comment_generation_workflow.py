"""
天気コメント生成ワークフロー

LangGraphを使用した天気コメント生成のメインワークフロー実装
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from langgraph.graph import StateGraph, END

from src.data.comment_generation_state import CommentGenerationState
from src.nodes.weather_forecast_node import fetch_weather_forecast_node
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node
from src.nodes.generate_comment_node import generate_comment_node
from src.nodes.select_comment_pair_node import select_comment_pair_node
from src.nodes.evaluate_candidate_node import evaluate_candidate_node
from src.nodes.input_node import input_node
from src.nodes.output_node import output_node
from src.config.weather_config import get_config
from src.types.validation import ensure_validation_result


# 定数
MAX_RETRY_COUNT = 5


def should_evaluate(state: CommentGenerationState) -> str:
    """
    評価を実行するかどうかを判定

    Args:
        state: 現在のワークフロー状態

    Returns:
        "evaluate" または "generate" の文字列
    """
    # LLMプロバイダーが設定されている場合は評価を実行
    if state.get("llm_provider"):
        return "evaluate"

    # LLMプロバイダーが設定されていない場合は評価をスキップ
    return "generate"


def should_retry(state: CommentGenerationState) -> str:
    """
    リトライが必要かどうかを判定

    Args:
        state: 現在のワークフロー状態

    Returns:
        "retry" または "continue" の文字列
    """
    # リトライ上限チェック
    if state.get("retry_count", 0) >= MAX_RETRY_COUNT:
        return "continue"

    # バリデーション結果をチェック（統一されたProtocolベースのアプローチ）
    raw_result = state.get("validation_result", None)
    validation_result = ensure_validation_result(raw_result)
    
    if validation_result and not validation_result.is_valid:
        return "retry"

    return "continue"


def timed_node(node_func):
    """ノード実行時間を計測するデコレーター"""

    def wrapper(state: CommentGenerationState) -> CommentGenerationState:
        node_name = getattr(node_func, '__name__', 'unknown_node')
        start_time = time.time()

        try:
            # ノード実行
            result = node_func(state)

            # 実行時間を記録
            execution_time = (time.time() - start_time) * 1000  # ミリ秒
            if "generation_metadata" not in result:
                result["generation_metadata"] = {}
            if "node_execution_times" not in result["generation_metadata"]:
                result["generation_metadata"]["node_execution_times"] = {}
            result["generation_metadata"]["node_execution_times"][node_name] = execution_time

            return result
        except Exception as e:
            # エラーでも実行時間を記録
            execution_time = (time.time() - start_time) * 1000
            if "generation_metadata" not in state:
                state["generation_metadata"] = {}
            if "node_execution_times" not in state["generation_metadata"]:
                state["generation_metadata"]["node_execution_times"] = {}
            state["generation_metadata"]["node_execution_times"][node_name] = execution_time

            # エラーをstateに記録して再発生
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({"error": f"{node_name}: {str(e)}", "node": node_name})
            raise e

    return wrapper


def create_comment_generation_workflow() -> StateGraph:
    """
    天気コメント生成ワークフローを構築

    Returns:
        構築されたLangGraphワークフロー
    """
    # ワークフローの初期化
    workflow = StateGraph(CommentGenerationState)

    # ノードの追加（実行時間計測付き）
    workflow.add_node("input", timed_node(input_node))
    workflow.add_node("fetch_forecast", timed_node(fetch_weather_forecast_node))
    workflow.add_node("retrieve_comments", timed_node(retrieve_past_comments_node))
    workflow.add_node("select_pair", timed_node(select_comment_pair_node))
    workflow.add_node("evaluate", timed_node(evaluate_candidate_node))
    workflow.add_node("generate", timed_node(generate_comment_node))
    workflow.add_node("output", timed_node(output_node))

    # エッジの追加（通常フロー）
    workflow.add_edge("input", "fetch_forecast")
    workflow.add_edge("fetch_forecast", "retrieve_comments")
    workflow.add_edge("retrieve_comments", "select_pair")

    # 条件付きエッジ（評価をスキップするか判定）
    workflow.add_conditional_edges(
        "select_pair", should_evaluate, {"evaluate": "evaluate", "generate": "generate"}
    )

    # 条件付きエッジ（リトライループ）
    workflow.add_conditional_edges(
        "evaluate", should_retry, {"retry": "select_pair", "continue": "generate"}
    )

    workflow.add_edge("generate", "output")
    workflow.add_edge("output", END)

    # エントリーポイントの設定
    workflow.set_entry_point("input")

    return workflow.compile()


def run_comment_generation(
    location_name: str,
    target_datetime: Optional[datetime] = None,
    llm_provider: str = "openai",
    exclude_previous: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    コメント生成ワークフローを実行

    Args:
        location_name: 地点名
        target_datetime: 対象日時（デフォルト: 現在時刻）
        llm_provider: LLMプロバイダー（openai/gemini/anthropic）
        exclude_previous: 前回生成と同じコメントを除外するかどうか
        **kwargs: その他のオプション

    Returns:
        生成結果を含む辞書
    """
    # ワークフローの構築
    workflow = create_comment_generation_workflow()

    # 初期状態の準備
    config = get_config()
    forecast_hours_ahead = config.weather.forecast_hours_ahead
    initial_state = {
        "location_name": location_name,
        "target_datetime": target_datetime or (datetime.now() + timedelta(hours=forecast_hours_ahead)),
        "llm_provider": llm_provider,
        "exclude_previous": exclude_previous,
        "retry_count": 0,
        "errors": [],
        "warnings": [],
        "workflow_start_time": datetime.now(),
        **kwargs,
    }

    # ワークフローの実行
    try:
        result = workflow.invoke(initial_state)

        # 実行時間の計算
        workflow_end_time = datetime.now()
        total_execution_time = (
            workflow_end_time - result.get("workflow_start_time", workflow_end_time)
        ).total_seconds() * 1000

        # エラーがある場合は失敗として扱う
        if result.get("errors"):
            return {
                "success": False,
                "error": "; ".join(result.get("errors", [])),
                "final_comment": None,
                "generation_metadata": result.get("generation_metadata", {}),
                "execution_time_ms": total_execution_time,
                "retry_count": result.get("retry_count", 0),
                "node_execution_times": result.get("generation_metadata", {}).get(
                    "node_execution_times", {}
                ),
                "warnings": result.get("warnings", []),
            }

        return {
            "success": True,
            "final_comment": result.get("final_comment"),
            "generation_metadata": result.get("generation_metadata", {}),
            "execution_time_ms": total_execution_time,
            "retry_count": result.get("retry_count", 0),
            "node_execution_times": result.get("generation_metadata", {}).get(
                "node_execution_times", {}
            ),
            "warnings": result.get("warnings", []),
        }
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"ワークフロー実行エラー: {str(e)}", exc_info=True)

        # エラーメッセージをより詳細に
        error_msg = str(e)
        if "天気予報の取得に失敗しました" in error_msg:
            error_msg = f"天気データの取得エラー: {error_msg}"
        elif "過去コメントが存在しません" in error_msg:
            error_msg = f"S3データアクセスエラー: {error_msg}"
        elif "コメントの生成に失敗しました" in error_msg:
            error_msg = f"LLMエラー: {error_msg}"

        return {
            "success": False,
            "error": error_msg,
            "final_comment": None,
            "generation_metadata": {},
            "execution_time_ms": 0,
            "retry_count": 0,
        }


# エクスポート
__all__ = [
    "create_comment_generation_workflow",
    "run_comment_generation",
    "should_retry",
    "MAX_RETRY_COUNT",
]
