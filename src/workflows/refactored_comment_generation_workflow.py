"""リファクタリングされたコメント生成ワークフロー

巨大なrun_comment_generation関数をWorkflowExecutorに委譲。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from src.workflows.comment_generation_workflow import create_comment_generation_workflow
from src.workflows.workflow_executor import WorkflowExecutor


def run_comment_generation_refactored(
    location_name: str,
    target_datetime: Optional[datetime] = None,
    llm_provider: str = "openai",
    exclude_previous: bool = False,
    **kwargs,
) -> Dict[str, str | int | float | bool | List[str] | Dict[str, str | int | float] | None]:
    """
    コメント生成ワークフローを実行（リファクタリング版）
    
    元のrun_comment_generation関数と同じインターフェースを維持しながら、
    内部実装をWorkflowExecutorに委譲。
    
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
    
    # ワークフロー実行を管理するエグゼキューターを作成
    executor = WorkflowExecutor(workflow)
    
    # ワークフローを実行
    return executor.execute(
        location_name=location_name,
        target_datetime=target_datetime,
        llm_provider=llm_provider,
        exclude_previous=exclude_previous,
        **kwargs
    )