"""UIフレームワークアダプター"""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.controllers.ui_interfaces import (
    ProgressBarProtocol, StatusTextProtocol, 
    ContainerProtocol, UIViewProtocol
)

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from app_interfaces import ICommentGenerationView


class StreamlitProgressBarAdapter:
    """Streamlitのプログレスバーアダプター"""
    
    def __init__(self, delta_generator: "DeltaGenerator"):
        self._delta_generator = delta_generator
    
    def progress(self, value: float) -> None:
        """進捗を更新（0.0 - 1.0）"""
        self._delta_generator.progress(value)


class StreamlitStatusTextAdapter:
    """Streamlitのステータステキストアダプター"""
    
    def __init__(self, delta_generator: "DeltaGenerator"):
        self._delta_generator = delta_generator
    
    def text(self, message: str) -> None:
        """テキストを更新"""
        self._delta_generator.text(message)


class StreamlitContainerAdapter:
    """Streamlitのコンテナアダプター"""
    
    def __init__(self, delta_generator: "DeltaGenerator"):
        self._delta_generator = delta_generator
    
    def container(self):
        """コンテキストマネージャーとして使用可能なコンテナを返す"""
        return self._delta_generator.container()


class StreamlitViewAdapter:
    """StreamlitのビューアダプタFor"""
    
    def __init__(self, view: "ICommentGenerationView"):
        self._view = view
    
    def update_progress(
        self,
        progress_bar: ProgressBarProtocol,
        status_text: StatusTextProtocol,
        idx: int,
        total: int,
        location: str
    ) -> None:
        """進捗を更新"""
        # Streamlit固有の実装をラップ
        if hasattr(self._view, 'update_progress'):
            # 元のStreamlit DeltaGeneratorを期待する場合
            if hasattr(progress_bar, '_delta_generator'):
                progress_bar = progress_bar._delta_generator
            if hasattr(status_text, '_delta_generator'):
                status_text = status_text._delta_generator
            self._view.update_progress(progress_bar, status_text, idx, total, location)
    
    def display_single_result(self, result: dict, metadata: dict) -> None:
        """単一の結果を表示"""
        self._view.display_single_result(result, metadata)