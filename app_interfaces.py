"""MVCパターンのインターフェース定義"""

from abc import ABC, abstractmethod
from typing import Any

from app_types import ProgressCallback, ResultCallback
from src.types import BatchGenerationResult, LocationResult


class ICommentGenerationController(ABC):
    """コメント生成コントローラーのインターフェース
    
    天気コメント生成のビジネスロジックを抽象化したインターフェースです。
    このインターフェースを実装することで、テスト時のモック化や
    異なる実装の切り替えが容易になります。
    
    主な機能:
    - 設定管理と検証
    - 単一/複数地点のコメント生成
    - 生成履歴の管理
    - 天気メタデータの抽出とフォーマット
    """

    @abstractmethod
    def get_generation_history(self) -> list[dict[str, Any]]:
        """生成履歴を取得"""
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
    def validate_configuration(self) -> dict[str, Any]:
        """設定の検証"""
        pass

    @abstractmethod
    def get_config_dict(self) -> dict[str, Any]:
        """設定を辞書形式で取得"""
        pass

    @abstractmethod
    def generate_comment_for_location(self, location: str, llm_provider: str) -> LocationResult:
        """単一地点のコメント生成"""
        pass

    @abstractmethod
    def generate_comments_batch(
        self,
        locations: list[str],
        llm_provider: str,
        progress_callback: ProgressCallback | None = None,
        result_callback: ResultCallback | None = None
    ) -> BatchGenerationResult:
        """複数地点のコメント生成
        
        Args:
            locations: 生成対象の地点名リスト
            llm_provider: 使用するLLMプロバイダー
            progress_callback: 進捗更新時に呼ばれるコールバック
            result_callback: 各地点の結果生成時に呼ばれるコールバック
            
        Returns:
            BatchGenerationResult: バッチ処理の結果
        """
        pass

    @abstractmethod
    def format_forecast_time(self, forecast_time: str) -> str:
        """予報時刻をフォーマット"""
        pass

    @abstractmethod
    def extract_weather_metadata(self, result: LocationResult) -> dict[str, Any]:
        """結果から天気メタデータを抽出"""
        pass

    @abstractmethod
    def validate_location_count(self, locations: list[str]) -> tuple[bool, str | None]:
        """地点数の検証"""
        pass


class ICommentGenerationView(ABC):
    """コメント生成ビューのインターフェース
    
    UIの表示とユーザーインタラクションを抽象化したインターフェースです。
    Streamlitや他のUIフレームワークへの依存を分離し、
    テストや異なるUI実装への切り替えを容易にします。
    
    主な機能:
    - ページ設定とレイアウト管理
    - ヘッダー、サイドバー、フッターの表示
    - コメント生成結果の表示
    - 進捗表示と更新
    - エラーや警告のハンドリング
    """

    @abstractmethod
    def setup_page_config(self, config: Any) -> None:
        """ページ設定"""
        pass

    @abstractmethod
    def display_header(self) -> None:
        """ヘッダー表示"""
        pass

    @abstractmethod
    def display_api_key_warning(self, validation_results: dict[str, Any]) -> None:
        """APIキーの警告表示"""
        pass

    @abstractmethod
    def display_single_result(self, result: LocationResult, metadata: dict[str, Any]) -> None:
        """個別の結果を表示"""
        pass

    @abstractmethod
    def create_progress_ui(self) -> tuple:
        """プログレスUIを作成"""
        pass

    @abstractmethod
    def update_progress(self, progress_bar: Any, status_text: Any, current: int, total: int, location: str) -> None:
        """進捗状況を更新"""
        pass


class ISessionManager(ABC):
    """セッション管理のインターフェース
    
    アプリケーションのセッション状態を管理するためのインターフェースです。
    Streamlitのセッション状態や他の状態管理システムへの
    依存を分離し、テストや異なる実装への切り替えを容易にします。
    
    主な機能:
    - セッション状態の初期化
    - 値の取得、設定、更新
    - 複数値の一括更新
    """

    @abstractmethod
    def initialize(self, defaults: dict[str, Any]) -> None:
        """セッション状態を初期化"""
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """セッション値を取得"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """セッション値を設定"""
        pass

    @abstractmethod
    def update(self, updates: dict[str, Any]) -> None:
        """複数のセッション値を更新"""
        pass
