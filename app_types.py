"""型定義とコールバックシグネチャ"""

from typing import Protocol

from src.types import LocationResult


class ProgressCallback(Protocol):
    """進捗更新コールバックのプロトコル
    
    Args:
        current: 現在の処理インデックス（0ベース）
        total: 総処理数
        location: 現在処理中の地点名
    """
    def __call__(self, current: int, total: int, location: str) -> None: ...


class ResultCallback(Protocol):
    """結果通知コールバックのプロトコル
    
    Args:
        location_result: 地点ごとのコメント生成結果
    """
    def __call__(self, location_result: LocationResult) -> None: ...


class CommentGeneratorFunc(Protocol):
    """コメント生成関数のプロトコル
    
    Args:
        location_name: 地点名
        target_datetime: 対象日時
        llm_provider: LLMプロバイダー名
        
    Returns:
        生成結果の辞書
    """
    def __call__(self, location_name: str, target_datetime: any, llm_provider: str) -> dict: ...


class HistoryLoaderFunc(Protocol):
    """履歴読み込み関数のプロトコル
    
    Returns:
        履歴データのリスト
    """
    def __call__(self) -> list[dict]: ...


class LocationLoaderFunc(Protocol):
    """地点読み込み関数のプロトコル
    
    Returns:
        地点名のリスト
    """
    def __call__(self) -> list[str]: ...


class HistorySaverFunc(Protocol):
    """履歴保存関数のプロトコル
    
    Args:
        result: 生成結果
        location: 地点名
        llm_provider: LLMプロバイダー名
    """
    def __call__(self, result: dict, location: str, llm_provider: str) -> None: ...
