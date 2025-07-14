"""天気コメント生成ワークフロー

天気予報取得とコメント取得を並列実行することで、
パフォーマンスを最適化したワークフローです。
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
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
from src.exceptions.error_types import (
    ErrorType, WeatherFetchError, DataAccessError, 
    LLMError, AppException
)
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# 定数
MAX_RETRY_COUNT = 5
THREAD_POOL_SIZE = 4
PARALLEL_TIMEOUT = 30  # 秒


def parallel_fetch_data_node(state: CommentGenerationState) -> CommentGenerationState:
    """天気予報とコメントデータを並列で取得"""
    logger.info("ParallelFetchDataNode: 並列データ取得を開始")
    
    start_time = time.time()
    
    try:
        with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
            # 天気予報取得タスク
            weather_future = executor.submit(_fetch_weather_wrapper, state)
            
            # コメント取得タスク
            comments_future = executor.submit(_fetch_comments_wrapper, state)
            
            # 両方の結果を待つ
            try:
                weather_result = weather_future.result(timeout=PARALLEL_TIMEOUT)
                comments_result = comments_future.result(timeout=PARALLEL_TIMEOUT)
            except TimeoutError:
                logger.error("並列データ取得がタイムアウトしました")
                raise ValueError("データ取得がタイムアウトしました")
            
            # 結果をマージ
            state.weather_data = weather_result.get("weather_data")
            state.past_comments = comments_result.get("past_comments")
            
            # エラーがあれば記録
            if weather_result.get("errors"):
                state.errors = state.errors or []
                state.errors.extend(weather_result["errors"])
            if comments_result.get("errors"):
                state.errors = state.errors or []
                state.errors.extend(comments_result["errors"])
                
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"並列データ取得完了: {execution_time:.2f}ms")
        
        # メタデータに実行時間を記録
        if "generation_metadata" not in state:
            state.generation_metadata = {}
        if "node_execution_times" not in state.generation_metadata:
            state.generation_metadata["node_execution_times"] = {}
        state.generation_metadata["node_execution_times"]["parallel_fetch_data"] = execution_time
        
    except Exception as e:
        logger.error(f"並列データ取得エラー: {str(e)}")
        state.errors = state.errors or []
        state.errors.append(f"ParallelFetchDataNode: {str(e)}")
        raise
        
    return state


def _fetch_weather_wrapper(state: CommentGenerationState) -> Dict[str, Any]:
    """天気予報取得のラッパー"""
    try:
        result = fetch_weather_forecast_node(state)
        return {"weather_data": result.weather_data, "errors": result.errors}
    except Exception as e:
        logger.error(f"天気予報取得エラー: {str(e)}")
        return {"weather_data": None, "errors": [str(e)]}


def _fetch_comments_wrapper(state: CommentGenerationState) -> Dict[str, Any]:
    """コメント取得のラッパー"""
    try:
        result = retrieve_past_comments_node(state)
        return {"past_comments": result.past_comments, "errors": result.errors}
    except Exception as e:
        logger.error(f"コメント取得エラー: {str(e)}")
        return {"past_comments": None, "errors": [str(e)]}




def should_evaluate(state: CommentGenerationState) -> str:
    """評価を実行するかどうかを判定（従来モード用）"""
    if state.get("llm_provider"):
        return "evaluate"
    return "generate"


def should_retry(state: CommentGenerationState) -> str:
    """リトライが必要かどうかを判定（従来モード用）"""
    if state.get("retry_count", 0) >= MAX_RETRY_COUNT:
        return "continue"
        
    raw_result = state.get("validation_result", None)
    validation_result = ensure_validation_result(raw_result)
    
    if validation_result and not validation_result.is_valid:
        return "retry"
        
    return "continue"


def create_comment_generation_workflow() -> StateGraph:
    """天気コメント生成ワークフローを構築"""
    workflow = StateGraph(CommentGenerationState)
    
    # ノードの追加
    workflow.add_node("input", input_node)
    workflow.add_node("parallel_fetch", parallel_fetch_data_node)
    
    
    # 従来モード用ノード
    workflow.add_node("select_pair", select_comment_pair_node)
    workflow.add_node("evaluate", evaluate_candidate_node)
    workflow.add_node("generate", generate_comment_node)
    
    workflow.add_node("output", output_node)
    
    # エッジの追加
    workflow.add_edge("input", "parallel_fetch")
    
    # 並列データ取得後は選択ノードへ
    workflow.add_edge("parallel_fetch", "select_pair")
    
    # メインフロー
    workflow.add_conditional_edges(
        "select_pair",
        should_evaluate,
        {
            "evaluate": "evaluate",
            "generate": "generate"
        }
    )
    
    workflow.add_conditional_edges(
        "evaluate",
        should_retry,
        {
            "retry": "select_pair",
            "continue": "generate"
        }
    )
    
    workflow.add_edge("generate", "output")
    workflow.add_edge("output", END)
    
    workflow.set_entry_point("input")
    
    return workflow.compile()


def run_comment_generation(
    location_name: str,
    target_datetime: Optional[datetime] = None,
    llm_provider: str = "openai",
    exclude_previous: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """並列処理対応のコメント生成ワークフローを実行
    
    Args:
        location_name: 地点名
        target_datetime: 対象日時
        llm_provider: LLMプロバイダー
        exclude_previous: 前回生成と同じコメントを除外するか
        **kwargs: その他のオプション
        
    Returns:
        生成結果を含む辞書
    """
    logger.info("並列処理ワークフローを実行")
    
    workflow = create_comment_generation_workflow()
    
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
                "error": "; ".join(result.get("errors", [])),
                "final_comment": None,
                "generation_metadata": generation_metadata,
                "execution_time_ms": total_execution_time,
                "retry_count": result.get("retry_count", 0),
                "node_execution_times": generation_metadata.get("node_execution_times", {}),
                "warnings": result.get("warnings", []),
            }
            
        return {
            "success": True,
            "final_comment": final_comment,
            "generation_metadata": generation_metadata,
            "execution_time_ms": total_execution_time,
            "retry_count": result.get("retry_count", 0),
            "node_execution_times": generation_metadata.get("node_execution_times", {}),
            "warnings": result.get("warnings", []),
        }
        
    except Exception as e:
        logger.error(f"並列ワークフロー実行エラー: {str(e)}", exc_info=True)
        
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
            "retry_count": 0,
        }