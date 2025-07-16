"""
コメント生成状態 - LangGraphワークフローの状態管理

このモジュールは、天気コメント生成ワークフローの
状態データを管理するデータクラスを定義します。
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

# Import new type definitions for Python 3.13+
from src.types.workflow_types import (
    GenerationMetadata,
    WorkflowError,
    SelectedCommentInfo,
    WeatherConditionInfo,
    CommentSource,
    ValidationStatus,
)


@dataclass
class CommentGenerationState:
    """
    コメント生成ワークフローの状態データ

    LangGraphワークフローで使用される状態情報を保持します。
    各ノードが必要な情報を参照・更新できます。
    """

    # ===== 入力パラメータ =====
    location_name: str
    target_datetime: datetime
    llm_provider: str = "openai"
    exclude_previous: bool = False

    # ===== 中間データ =====
    location: Any | None = None  # Location オブジェクト
    weather_data: Any | None = None  # WeatherForecast オブジェクト
    past_comments: list[Any] = field(default_factory=list)  # PastComment のリスト
    selected_pair: Any | None = None  # CommentPair オブジェクト
    generated_comment: str | None = None

    # ===== 制御フラグ =====
    retry_count: int = 0
    max_retry_count: int = field(default_factory=lambda: int(os.environ.get("MAX_EVALUATION_RETRIES", "3")))
    validation_result: Any | None = None  # ValidationResult オブジェクト
    should_retry: bool = False

    # ===== 出力データ =====
    final_comment: str | None = None
    generation_metadata: GenerationMetadata = field(default_factory=dict)

    # ===== エラー情報 =====
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """初期化後の処理"""
        if not self.generation_metadata:
            self.generation_metadata = GenerationMetadata(
                workflow_started_at=datetime.now().isoformat(),
                completed_at=None,
                execution_time_ms=None,
                retry_count=0,
                errors=[],
                warnings=[],
                has_errors=False,
                has_warnings=False,
                final_comment_source=None,
                selected_past_comments=[],
                weather_condition=None,
                validation_status=None,
            )

    def add_error(self, error_message: str, node_name: str | None = None):
        """エラーを追加"""
        error_info = WorkflowError(
            message=error_message,
            node=node_name,
            timestamp=datetime.now().isoformat(),
        )
        self.errors.append(error_message)
        self.generation_metadata["errors"].append(error_info)
        self.generation_metadata["has_errors"] = True

    def add_warning(self, warning_message: str, node_name: str | None = None):
        """警告を追加"""
        warning_info = WorkflowError(
            message=warning_message,
            node=node_name,
            timestamp=datetime.now().isoformat(),
        )
        self.warnings.append(warning_message)
        self.generation_metadata["warnings"].append(warning_info)
        self.generation_metadata["has_warnings"] = True

    def increment_retry(self) -> bool:
        """
        リトライ回数を増加

        Returns:
            bool: まだリトライ可能かどうか
        """
        self.retry_count += 1
        self.generation_metadata["retry_count"] = self.retry_count
        return self.retry_count <= self.max_retry_count

    def is_retry_available(self) -> bool:
        """リトライが可能かどうか"""
        return self.retry_count < self.max_retry_count

    def set_final_comment(self, comment: str, source: CommentSource = "generated"):
        """最終コメントを設定"""
        self.final_comment = comment
        self.generation_metadata["final_comment_source"] = source
        self.generation_metadata["completed_at"] = datetime.now().isoformat()
        
        # Calculate execution time
        start_time = datetime.fromisoformat(self.generation_metadata["workflow_started_at"])
        end_time = datetime.now()
        self.generation_metadata["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

    def update_metadata(self, key: str, value: Any):
        """メタデータを更新"""
        self.generation_metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """辞書風のアクセスメソッド - LangGraphの互換性のため"""
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def __getitem__(self, key: str) -> Any:
        """辞書風のアクセス - LangGraphの互換性のため"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' not found in CommentGenerationState")

    def __contains__(self, key: str) -> bool:
        """in演算子のサポート"""
        return hasattr(self, key)

    def __setitem__(self, key: str, value: Any):
        """辞書風の設定 - LangGraphの互換性のため"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            # 新しい属性は追加しない（予期しない動作を防ぐため）
            raise KeyError(f"Cannot set '{key}' - not a valid attribute of CommentGenerationState")

    def get_execution_summary(self) -> dict[str, Any]:
        """実行サマリーを取得"""
        return {
            "location_name": self.location_name,
            "target_datetime": (
                self.target_datetime.isoformat()
                if isinstance(self.target_datetime, datetime)
                else str(self.target_datetime)
            ),
            "llm_provider": self.llm_provider,
            "final_comment": self.final_comment,
            "retry_count": self.retry_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "success": bool(self.final_comment and not self.errors),
            "metadata": self.generation_metadata,
        }

    def to_output_format(self) -> dict[str, Any]:
        """外部出力用フォーマットに変換"""
        # Update weather condition info if available
        if self.weather_data:
            weather_condition_info = WeatherConditionInfo(
                temperature=getattr(self.weather_data, "temperature", 0.0),
                description=getattr(self.weather_data, "weather_description", ""),
                is_severe=getattr(self.weather_data, "is_severe_weather", False),
                is_heat_wave=getattr(self.weather_data, "temperature", 0) >= 35,
            )
            self.generation_metadata["weather_condition"] = weather_condition_info
        
        # Update selected comments
        self.generation_metadata["selected_past_comments"] = self._format_selected_comments()
        
        # Update validation status
        if self.validation_result:
            self.generation_metadata["validation_status"] = "passed" if getattr(self.validation_result, "is_valid", False) else "failed"
        
        # Update additional metadata
        self.generation_metadata["location_name"] = self.location_name
        self.generation_metadata["target_datetime"] = (
            self.target_datetime.isoformat()
            if isinstance(self.target_datetime, datetime)
            else str(self.target_datetime)
        )
        self.generation_metadata["llm_provider"] = self.llm_provider
        self.generation_metadata["retry_count"] = self.retry_count
        
        return {
            "final_comment": self.final_comment,
            "generation_metadata": dict(self.generation_metadata),  # Convert TypedDict to regular dict
        }


    def _format_selected_comments(self) -> list[SelectedCommentInfo]:
        """選択された過去コメントをフォーマット"""
        selected_comments: list[SelectedCommentInfo] = []

        if self.selected_pair:
            if (
                hasattr(self.selected_pair, "weather_comment")
                and self.selected_pair.weather_comment
            ):
                selected_comments.append(
                    SelectedCommentInfo(
                        text=getattr(self.selected_pair.weather_comment, "comment_text", ""),
                        type="weather_comment",
                        score=getattr(self.selected_pair.weather_comment, "score", None),
                        original_index=getattr(self.selected_pair.weather_comment, "original_index", 0),
                    )
                )
            if hasattr(self.selected_pair, "advice_comment") and self.selected_pair.advice_comment:
                selected_comments.append(
                    SelectedCommentInfo(
                        text=getattr(self.selected_pair.advice_comment, "comment_text", ""),
                        type="advice",
                        score=getattr(self.selected_pair.advice_comment, "score", None),
                        original_index=getattr(self.selected_pair.advice_comment, "original_index", 0),
                    )
                )

        return selected_comments

    def reset_for_retry(self):
        """リトライ用にステートをリセット"""
        self.generated_comment = None
        self.validation_result = None
        self.should_retry = False

        # 前回のエラーを警告に変換
        if self.errors:
            last_error = self.errors[-1]
            self.add_warning(f"Retry due to: {last_error}")

    def is_complete(self) -> bool:
        """ワークフローが完了したかどうか"""
        return bool(self.final_comment)

    def get_current_step(self) -> str:
        """現在のステップを推定"""
        if not self.location:
            return "input_validation"
        elif not self.weather_data:
            return "fetch_forecast"
        elif not self.past_comments:
            return "retrieve_comments"
        elif not self.selected_pair:
            return "select_pair"
        elif not self.generated_comment:
            return "generate_comment"
        elif not self.validation_result:
            return "evaluate_candidate"
        elif self.should_retry:
            return "retry_loop"
        else:
            return "output"


# ワークフロー制御用のヘルパー関数
def should_retry_generation(state: CommentGenerationState) -> bool:
    """
    コメント生成をリトライすべきかどうかを判定

    Args:
        state: コメント生成状態

    Returns:
        bool: リトライが必要かどうか
    """
    if not state.is_retry_available():
        return False

    if state.validation_result and not state.validation_result.is_valid:
        return True

    if state.errors and not state.final_comment:
        return True

    return state.should_retry


def create_initial_state(
    location_name: str, target_datetime: datetime | None = None, llm_provider: str = "openai"
) -> CommentGenerationState:
    """
    初期状態を作成

    Args:
        location_name: 地点名
        target_datetime: 対象日時
        llm_provider: LLMプロバイダー

    Returns:
        CommentGenerationState: 初期化された状態
    """
    if target_datetime is None:
        target_datetime = datetime.now()

    return CommentGenerationState(
        location_name=location_name, target_datetime=target_datetime, llm_provider=llm_provider
    )


