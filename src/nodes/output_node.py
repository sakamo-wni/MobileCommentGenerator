"""
出力ノード

最終結果を整形してJSON形式で出力するLangGraphノード
"""

from typing import Any
import logging
from datetime import datetime
import json

from src.data.comment_generation_state import CommentGenerationState
from src.formatters import (
    FinalCommentFormatter,
    MetadataFormatter,
    JsonOutputFormatter
)

logger = logging.getLogger(__name__)

# フォーマッターインスタンスの初期化
final_comment_formatter = FinalCommentFormatter()
metadata_formatter = MetadataFormatter()
json_output_formatter = JsonOutputFormatter()


def output_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    最終結果をJSON形式で出力

    Args:
        state: ワークフローの状態

    Returns:
        出力形式に整形された状態
    """
    logger.info("OutputNode: 出力処理を開始")

    try:
        # 実行時間の計算
        execution_start = state.generation_metadata.get("execution_start_time")
        execution_end = datetime.now()
        execution_time_ms = 0

        if execution_start:
            # execution_startが文字列の場合はdatetimeに変換
            if isinstance(execution_start, str):
                try:
                    execution_start = datetime.fromisoformat(execution_start.replace("Z", "+00:00"))
                except:
                    execution_start = None

            # datetime型の場合のみ計算
            if isinstance(execution_start, datetime):
                execution_time_delta = execution_end - execution_start
                execution_time_ms = int(execution_time_delta.total_seconds() * 1000)

        # 最終コメントの確定
        final_comment = final_comment_formatter.determine_final_comment(state)
        state.final_comment = final_comment

        # メタデータの生成
        generation_metadata = metadata_formatter.create_generation_metadata(state, execution_time_ms)
        state.generation_metadata = generation_metadata

        # JSON形式への変換
        output_json = json_output_formatter.format_output(state)
        state.update_metadata("output_json", output_json)

        # 成功ログ
        location_info = f"location={state.location_name}" if state.location_name else "location=unknown"
        logger.info(
            f"出力処理完了: {location_info}, "
            f"comment_length={len(final_comment)}, "
            f"execution_time={execution_time_ms}ms, "
            f"retry_count={state.retry_count}"
        )

    except Exception as e:
        logger.error(f"出力処理中にエラー: {str(e)}")
        state.errors = state.errors + [f"OutputNode: {str(e)}"]
        state.update_metadata("output_processed", False)

        # エラー時の出力
        error_json = json_output_formatter.format_error_output(state, str(e))
        state.update_metadata("output_json", error_json)

    return state


# エクスポート
__all__ = ["output_node"]