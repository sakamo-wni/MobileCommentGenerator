"""天気コメント生成システム - インターフェース定義"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from src.config.app_config import AppConfig

from src.types import BatchGenerationResult, LocationResult


class ICommentGenerationController(ABC):
    """コメント生成コントローラーのインターフェース"""

    @property
    @abstractmethod
    def generation_history(self) -> list[dict[str, str | int | float | bool]]:
        """生成履歴を取得"""
        pass

    @property
    @abstractmethod
    def config(self) -> "AppConfig":
        """設定を取得"""
        pass

    @abstractmethod
    def get_default_locations(self) -> list[str]:
        """デフォルトの地点リストを取得"""
        pass

    @abstractmethod
    def get_default_llm_provider(self) -> str:
        """デフォルトのLLMプロバイダーを取得"""
        pass

    @abstractmethod
    def validate_configuration(self) -> dict[str, bool | str]:
        """設定の検証"""
        pass

    @abstractmethod
    def generate_comment_for_location(self, location: str, llm_provider: str) -> LocationResult:
        """単一地点のコメント生成

        Args:
            location: 地点名
            llm_provider: LLMプロバイダー

        Returns:
            LocationResult: 生成結果
        """
        pass

    @abstractmethod
    def generate_comments_batch(
        self,
        locations: list[str],
        llm_provider: str,
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> BatchGenerationResult:
        """複数地点のコメント生成

        Args:
            locations: 地点リスト
            llm_provider: LLMプロバイダー
            progress_callback: 進捗通知コールバック

        Returns:
            BatchGenerationResult: バッチ生成結果
        """
        pass

    @abstractmethod
    def extract_weather_metadata(self, result: LocationResult) -> dict[str, str | float | None]:
        """天気メタデータの抽出

        Args:
            result: 地点結果

        Returns:
            dict: メタデータ
        """
        pass

    @abstractmethod
    def format_forecast_time(self, forecast_time: str) -> str:
        """予報時刻のフォーマット

        Args:
            forecast_time: UTC時刻文字列

        Returns:
            str: フォーマット済み時刻
        """
        pass

    @abstractmethod
    def validate_location_count(self, locations: list[str]) -> tuple[bool, str | None]:
        """地点数の検証

        Args:
            locations: 地点リスト

        Returns:
            tuple: (検証結果, エラーメッセージ)
        """
        pass


class ICommentGenerationView(ABC):
    """コメント生成ビューのインターフェース"""

    @abstractmethod
    def create_progress_ui(self) -> tuple["DeltaGenerator", "DeltaGenerator"]:
        """プログレスUIの作成

        Returns:
            tuple: (progress_bar, status_text)
        """
        pass

    @abstractmethod
    def update_progress(self, progress_bar: "DeltaGenerator", status_text: "DeltaGenerator", idx: int, total: int, location: str) -> None:
        """プログレスの更新

        Args:
            progress_bar: プログレスバーオブジェクト
            status_text: ステータステキストオブジェクト
            idx: 現在のインデックス
            total: 全体数
            location: 現在の地点名
        """
        pass

    @abstractmethod
    def complete_progress(self, progress_bar: "DeltaGenerator", status_text: "DeltaGenerator", success_count: int, total: int) -> None:
        """プログレスの完了処理

        Args:
            progress_bar: プログレスバーオブジェクト
            status_text: ステータステキストオブジェクト
            success_count: 成功数
            total: 全体数
        """
        pass

    @abstractmethod
    def display_single_result(self, result: LocationResult, metadata: dict[str, str | float | None]) -> None:
        """単一結果の表示

        Args:
            result: 地点結果
            metadata: メタデータ
        """
        pass
