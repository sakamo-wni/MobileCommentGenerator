"""統合コメント生成ワークフロー

選択と生成を1回のLLM呼び出しで実行する最適化されたワークフロー。
既存のワークフローと完全な互換性を保ちます。
"""

from __future__ import annotations
from typing import Any
from datetime import datetime, timedelta
import time
import json
import logging
from langgraph.graph import StateGraph, END

from src.data.comment_generation_state import CommentGenerationState
from src.nodes.weather_forecast_node import fetch_weather_forecast_node
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node
from src.nodes.unified_comment_generation_node import unified_comment_generation_node
from src.nodes.input_node import input_node
from src.nodes.output_node import output_node
from src.config.weather_config import get_config
from src.exceptions.error_types import (
    ErrorType, WeatherFetchError, DataAccessError, 
    LLMError, AppException
)
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def timed_node(node_func):
    """ノード実行時間を計測するデコレーター"""
    def wrapper(state: CommentGenerationState) -> CommentGenerationState:
        node_name = getattr(node_func, '__name__', 'unknown_node')
        start_time = time.time()
        
        try:
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


def create_unified_comment_generation_workflow() -> StateGraph:
    """統合コメント生成ワークフローを構築"""
    workflow = StateGraph(CommentGenerationState)
    
    # ノードの追加（実行時間計測付き）
    workflow.add_node("input", timed_node(input_node))
    workflow.add_node("fetch_forecast", timed_node(fetch_weather_forecast_node))
    workflow.add_node("retrieve_comments", timed_node(retrieve_past_comments_node))
    workflow.add_node("unified_generation", timed_node(unified_comment_generation_node))
    workflow.add_node("output", timed_node(output_node))
    
    # エッジの追加（シンプルな直線フロー）
    workflow.add_edge("input", "fetch_forecast")
    workflow.add_edge("fetch_forecast", "retrieve_comments")
    workflow.add_edge("retrieve_comments", "unified_generation")
    workflow.add_edge("unified_generation", "output")
    workflow.add_edge("output", END)
    
    # エントリーポイントの設定
    workflow.set_entry_point("input")
    
    return workflow.compile()


def run_unified_comment_generation(
    location_name: str,
    target_datetime: datetime | None = None,
    llm_provider: str = "openai",
    exclude_previous: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """統合コメント生成ワークフローを実行
    
    Args:
        location_name: 地点名
        target_datetime: 対象日時
        llm_provider: LLMプロバイダー
        exclude_previous: 前回生成と同じコメントを除外するか
        **kwargs: その他のオプション
        
    Returns:
        生成結果を含む辞書
    """
    workflow = create_unified_comment_generation_workflow()
    
    config = get_config()
    forecast_hours_ahead = config.weather.forecast_hours_ahead
    initial_state = {
        "location_name": location_name,
        "target_datetime": target_datetime or (datetime.now() + timedelta(hours=forecast_hours_ahead)),
        "llm_provider": llm_provider,
        "exclude_previous": exclude_previous,
        "errors": [],
        "warnings": [],
        "workflow_start_time": datetime.now(),
        **kwargs,
    }
    
    try:
        result = workflow.invoke(initial_state)
        
        workflow_end_time = datetime.now()
        total_execution_time = (
            workflow_end_time - result.get("workflow_start_time", workflow_end_time)
        ).total_seconds() * 1000
        
        # 結果の取得
        output_json_str = result.get("generation_metadata", {}).get("output_json")
        if output_json_str:
            try:
                output_data = json.loads(output_json_str)
                final_comment = output_data.get("final_comment")
                generation_metadata = output_data.get("generation_metadata", {})
            except json.JSONDecodeError:
                logger.error(f"output_jsonのパースに失敗: {output_json_str}")
                final_comment = result.get("final_comment")
                generation_metadata = result.get("generation_metadata", {})
        else:
            final_comment = result.get("final_comment")
            generation_metadata = result.get("generation_metadata", {})
            
        # エラーチェック
        if result.get("errors"):
            return {
                "success": False,
                "error": "; ".join([str(e) for e in result.get("errors", [])]),
                "final_comment": None,
                "generation_metadata": generation_metadata,
                "execution_time_ms": total_execution_time,
                "node_execution_times": generation_metadata.get("node_execution_times", {}),
                "warnings": result.get("warnings", []),
            }
            
        return {
            "success": True,
            "final_comment": final_comment,
            "generation_metadata": generation_metadata,
            "execution_time_ms": total_execution_time,
            "node_execution_times": generation_metadata.get("node_execution_times", {}),
            "warnings": result.get("warnings", []),
        }
        
    except Exception as e:
        logger.error(f"統合ワークフロー実行エラー: {str(e)}", exc_info=True)
        
        # エラー分類
        error_msg = str(e)
        app_error = None
        
        if "天気予報の取得に失敗しました" in error_msg or "weather" in error_msg.lower():
            app_error = WeatherFetchError(message=error_msg)
        elif "過去コメントが存在しません" in error_msg or "CSV" in error_msg:
            app_error = DataAccessError(message=error_msg)
        elif "コメントの生成に失敗しました" in error_msg or "LLM" in error_msg:
            app_error = LLMError(message=error_msg)
        else:
            app_error = AppException(ErrorType.UNKNOWN_ERROR, message=error_msg)
            
        error_response = ErrorHandler.handle_error(app_error)
        
        return {
            "success": False,
            "error": error_response.user_message,
            "error_type": error_response.error_type,
            "error_details": error_response.error_details,
            "final_comment": None,
            "generation_metadata": {},
            "execution_time_ms": 0,
        }