"""ワークフロー実行を管理するモジュール

巨大なrun_comment_generation関数を分割し、責務を明確化。
"""

from __future__ import annotations
import json
import logging
from typing import Any
from datetime import datetime, timedelta

from src.data.comment_generation_state import CommentGenerationState
from src.config.weather_config import get_config
from src.exceptions.error_types import (
    ErrorType, WeatherFetchError, DataAccessError, 
    LLMError, AppException
)
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class WorkflowStateBuilder:
    """ワークフローの初期状態を構築するクラス"""
    
    @staticmethod
    def build_initial_state(
        location_name: str,
        target_datetime: datetime | None = None,
        llm_provider: str = "openai",
        exclude_previous: bool = False,
        **kwargs
    ) -> CommentGenerationState:
        """初期状態を構築"""
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
        
        # 事前取得した天気データがある場合は状態に追加
        if "pre_fetched_weather" in kwargs:
            initial_state["pre_fetched_weather"] = kwargs["pre_fetched_weather"]
            
        return initial_state


class WorkflowResultParser:
    """ワークフロー実行結果を解析するクラス"""
    
    @staticmethod
    def parse_output_json(result: CommentGenerationState) -> tuple[str | None, dict[str, Any]]:
        """output_jsonから結果を解析"""
        output_json_str = result.get("generation_metadata", {}).get("output_json")
        
        if output_json_str:
            try:
                output_data = json.loads(output_json_str)
                final_comment = output_data.get("final_comment")
                generation_metadata = output_data.get("generation_metadata", {})
                return final_comment, generation_metadata
            except json.JSONDecodeError:
                logger.error(f"output_jsonのパースに失敗: {output_json_str}")
        
        # フォールバック: 直接stateから取得
        final_comment = result.get("final_comment")
        generation_metadata = result.get("generation_metadata", {})
        return final_comment, generation_metadata
    
    @staticmethod
    def calculate_execution_time(
        workflow_start_time: datetime,
        workflow_end_time: datetime | None = None
    ) -> float:
        """実行時間を計算（ミリ秒）"""
        end_time = workflow_end_time or datetime.now()
        return (end_time - workflow_start_time).total_seconds() * 1000


class WorkflowResponseBuilder:
    """ワークフロー実行結果のレスポンスを構築するクラス"""
    
    @staticmethod
    def build_success_response(
        final_comment: str,
        generation_metadata: dict[str, Any],
        execution_time_ms: float,
        retry_count: int,
        warnings: list[str]
    ) -> dict[str, Any]:
        """成功レスポンスを構築"""
        return {
            "success": True,
            "final_comment": final_comment,
            "generation_metadata": generation_metadata,
            "execution_time_ms": execution_time_ms,
            "retry_count": retry_count,
            "node_execution_times": generation_metadata.get("node_execution_times", {}),
            "warnings": warnings,
        }
    
    @staticmethod
    def build_error_response(
        errors: list[str],
        generation_metadata: dict[str, Any],
        execution_time_ms: float,
        retry_count: int,
        warnings: list[str]
    ) -> dict[str, Any]:
        """エラーレスポンスを構築"""
        return {
            "success": False,
            "error": "; ".join(errors),
            "final_comment": None,
            "generation_metadata": generation_metadata,
            "execution_time_ms": execution_time_ms,
            "retry_count": retry_count,
            "node_execution_times": generation_metadata.get("node_execution_times", {}),
            "warnings": warnings,
        }
    
    @staticmethod
    def build_exception_response(exception: Exception) -> dict[str, Any]:
        """例外レスポンスを構築"""
        error_msg = str(exception)
        app_error = WorkflowResponseBuilder._classify_error(error_msg)
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
    
    @staticmethod
    def _classify_error(error_msg: str) -> AppException:
        """エラーメッセージを分類"""
        if "天気予報の取得に失敗しました" in error_msg or "weather" in error_msg.lower():
            return WeatherFetchError(message=error_msg)
        elif "過去コメントが存在しません" in error_msg or "CSV" in error_msg:
            return DataAccessError(message=error_msg)
        elif "コメントの生成に失敗しました" in error_msg or "LLM" in error_msg:
            return LLMError(message=error_msg)
        else:
            return AppException(ErrorType.UNKNOWN_ERROR, message=error_msg)


class WorkflowExecutor:
    """ワークフロー実行を管理するクラス"""
    
    def __init__(self, workflow):
        self.workflow = workflow
        self.state_builder = WorkflowStateBuilder()
        self.result_parser = WorkflowResultParser()
        self.response_builder = WorkflowResponseBuilder()
    
    def execute(
        self,
        location_name: str,
        target_datetime: datetime | None = None,
        llm_provider: str = "openai",
        exclude_previous: bool = False,
        **kwargs
    ) -> dict[str, Any]:
        """ワークフローを実行"""
        # 初期状態の構築
        initial_state = self.state_builder.build_initial_state(
            location_name=location_name,
            target_datetime=target_datetime,
            llm_provider=llm_provider,
            exclude_previous=exclude_previous,
            **kwargs
        )
        
        # ワークフローの実行
        try:
            result = self.workflow.invoke(initial_state)
            return self._process_result(result)
        except Exception as e:
            logger.error(f"ワークフロー実行エラー: {str(e)}", exc_info=True)
            return self.response_builder.build_exception_response(e)
    
    def _process_result(self, result: CommentGenerationState) -> dict[str, Any]:
        """実行結果を処理"""
        # 実行時間の計算
        workflow_start_time = result.get("workflow_start_time", datetime.now())
        execution_time_ms = self.result_parser.calculate_execution_time(workflow_start_time)
        
        # 結果の解析
        final_comment, generation_metadata = self.result_parser.parse_output_json(result)
        
        # 共通パラメータ
        retry_count = result.get("retry_count", 0)
        warnings = result.get("warnings", [])
        
        # エラーがある場合は失敗として扱う
        if result.get("errors"):
            return self.response_builder.build_error_response(
                errors=result.get("errors", []),
                generation_metadata=generation_metadata,
                execution_time_ms=execution_time_ms,
                retry_count=retry_count,
                warnings=warnings
            )
        
        # 成功レスポンスを返す
        return self.response_builder.build_success_response(
            final_comment=final_comment,
            generation_metadata=generation_metadata,
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
            warnings=warnings
        )