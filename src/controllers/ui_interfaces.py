"""UIフレームワーク非依存のインターフェース定義"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProgressBarProtocol(Protocol):
    """プログレスバーのプロトコル"""
    
    def progress(self, value: float) -> None:
        """進捗を更新（0.0 - 1.0）"""
        ...


@runtime_checkable
class StatusTextProtocol(Protocol):
    """ステータステキストのプロトコル"""
    
    def text(self, message: str) -> None:
        """テキストを更新"""
        ...


@runtime_checkable
class ContainerProtocol(Protocol):
    """コンテナのプロトコル"""
    
    def container(self):
        """コンテキストマネージャーとして使用可能なコンテナを返す"""
        ...


class UIViewProtocol(Protocol):
    """UIビューのプロトコル"""
    
    def update_progress(
        self, 
        progress_bar: ProgressBarProtocol,
        status_text: StatusTextProtocol,
        idx: int,
        total: int,
        location: str
    ) -> None:
        """進捗を更新"""
        ...
    
    def display_single_result(
        self,
        result: dict,
        metadata: dict
    ) -> None:
        """単一の結果を表示"""
        ...