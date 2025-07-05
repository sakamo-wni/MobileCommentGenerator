"""
JSON Output Formatter

最終結果をJSON形式で整形し、クリーンアップ処理を行う
"""

from typing import Dict, Any
import logging
import json
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.formatters.final_comment_formatter import FinalCommentFormatter
from src.formatters.metadata_formatter import MetadataFormatter
from src.formatters.debug_info_formatter import DebugInfoFormatter

logger = logging.getLogger(__name__)


class JsonOutputFormatter:
    """JSON出力のフォーマッター"""
    
    def __init__(self):
        self.final_comment_formatter = FinalCommentFormatter()
        self.metadata_formatter = MetadataFormatter()
        self.debug_info_formatter = DebugInfoFormatter()

    def format_output(self, state: CommentGenerationState) -> str:
        """
        最終結果をJSON形式で出力
        
        Args:
            state: ワークフローの状態
            
        Returns:
            JSON形式の出力文字列
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
            final_comment = self.final_comment_formatter.determine_final_comment(state)
            state.final_comment = final_comment

            # メタデータの生成
            generation_metadata = self.metadata_formatter.create_generation_metadata(state, execution_time_ms)
            state.generation_metadata = generation_metadata

            # 出力データの構築
            output_data = {"final_comment": final_comment, "generation_metadata": generation_metadata}

            # オプション情報の追加
            if state.generation_metadata.get("include_debug_info", False):
                output_data["debug_info"] = self.debug_info_formatter.create_debug_info(state)

            # JSON形式への変換
            output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
            state.update_metadata("output_json", output_json)

            # 成功ログ
            location_info = f"location={state.location_name}" if state.location_name else "location=unknown"
            logger.info(
                f"出力処理完了: {location_info}, "
                f"comment_length={len(final_comment)}, "
                f"execution_time={execution_time_ms}ms, "
                f"retry_count={state.retry_count}"
            )

            # クリーンアップ
            self.cleanup_state(state)

            state.update_metadata("output_processed", True)
            
            return output_json

        except Exception as e:
            logger.error(f"出力処理中にエラー: {str(e)}")
            state.errors = state.errors + [f"OutputNode: {str(e)}"]
            state.update_metadata("output_processed", False)

            # エラー時の出力
            error_output = self.format_error_output(state, str(e))
            state.update_metadata("output_json", error_output)
            
            return error_output

    def format_error_output(self, state: CommentGenerationState, error_message: str) -> str:
        """
        エラー時の出力を生成
        
        Args:
            state: ワークフローの状態
            error_message: エラーメッセージ
            
        Returns:
            エラー情報を含むJSON文字列
        """
        return json.dumps(
            {
                "error": error_message,
                "final_comment": None,
                "generation_metadata": {
                    "error": error_message,
                    "execution_time_ms": 0,
                    "errors": state.errors,
                },
            },
            ensure_ascii=False,
            indent=2
        )

    def cleanup_state(self, state: CommentGenerationState):
        """
        不要な中間データをクリーンアップ

        メモリ使用量を削減するため、大きな中間データを削除
        
        Args:
            state: ワークフローの状態
        """
        # 大きなデータの削除候補
        cleanup_keys = [
            "past_comments",  # 過去コメントの大量データ
            "all_weather_data",  # 詳細な天気データ
            "candidate_pairs",  # 評価前の候補ペア
            "evaluation_details",  # 詳細な評価情報
        ]

        for key in cleanup_keys:
            # メタデータ内の大きなデータをクリーンアップ
            if key in state.generation_metadata:
                value = state.generation_metadata[key]
                if isinstance(value, (list, dict)) and len(str(value)) > 10000:  # 10KB以上
                    logger.debug(f"クリーンアップ: {key} を削除")
                    del state.generation_metadata[key]


# エクスポート
__all__ = ["JsonOutputFormatter"]