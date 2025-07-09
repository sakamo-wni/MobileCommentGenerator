"""コメント生成コントローラー"""

import asyncio
import logging
from typing import List, Dict, Optional, Callable
from concurrent.futures import as_completed, ThreadPoolExecutor

from src.config.app_config import AppConfig, get_config
from src.types import LocationResult, BatchGenerationResult
from src.ui.streamlit_utils import load_history, load_locations, save_to_history
from src.utils.error_handler import ErrorHandler
from src.workflows.comment_generation_workflow import run_comment_generation
from src.controllers.metadata_extractor import MetadataExtractor
from src.controllers.validators import ValidationManager
from src.controllers.batch_processor import BatchProcessor
from src.controllers.progress_handler import ProgressHandler
from app_interfaces import ICommentGenerationController

logger = logging.getLogger(__name__)


class CommentGenerationController(ICommentGenerationController):
    """コメント生成のビジネスロジックを管理するコントローラー"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self._config = config or get_config()
        self._generation_history: Optional[List[Dict[str, str]]] = None
        
        # 依存コンポーネントの初期化
        self._metadata_extractor = MetadataExtractor()
        self._validators = ValidationManager(self._config)
        self._progress_handler = ProgressHandler(self._metadata_extractor)
        self._batch_processor = BatchProcessor(self._progress_handler)
    
    @property
    def config(self) -> AppConfig:
        """設定を取得"""
        return self._config
    
    @property
    def generation_history(self) -> List[Dict[str, str]]:
        """生成履歴を取得（遅延読み込み）"""
        if self._generation_history is None:
            self._generation_history = load_history()
        return self._generation_history
    
    def get_default_locations(self) -> List[str]:
        """デフォルトの地点リストを取得"""
        return load_locations()
    
    def get_default_llm_provider(self) -> str:
        """デフォルトのLLMプロバイダーを取得"""
        return self.config.ui_settings.default_llm_provider
    
    def validate_configuration(self) -> Dict[str, bool | str]:
        """設定の検証"""
        return self._validators.validate_configuration()
    
    def get_config_dict(self) -> Dict[str, str | int | float | bool]:
        """設定を辞書形式で取得"""
        return self.config.to_dict()
    
    def generate_comment_for_location(self, location: str, llm_provider: str) -> LocationResult:
        """単一地点のコメント生成"""
        try:
            # 実際のコメント生成
            result = run_comment_generation(
                location_name=location,
                target_datetime=None,
                llm_provider=llm_provider
            )
            
            # 結果を収集
            location_result: LocationResult = {
                'location': location,
                'result': result,
                'success': result.get('success', False),
                'comment': result.get('final_comment', ''),
                'error': result.get('error', None),
                'source_files': None
            }
            
            # ソースファイル情報を抽出
            metadata = result.get('generation_metadata', {})
            if metadata.get('selected_past_comments'):
                sources = []
                for comment in metadata['selected_past_comments']:
                    if 'source_file' in comment:
                        sources.append(comment['source_file'])
                if sources:
                    location_result['source_files'] = sources
                    # 詳細ログ出力
                    logger.info(f"地点: {location}")
                    logger.info(f"  天気: {metadata.get('weather_condition', '不明')}")
                    logger.info(f"  気温: {metadata.get('temperature', '不明')}°C")
                    logger.info(f"  コメント生成元ファイル: {sources}")
                    logger.info(f"  生成コメント: {result.get('final_comment', '')}")
            
            # 履歴に保存
            if result.get('success'):
                save_to_history(result, location, llm_provider)
                # 履歴キャッシュをクリア
                self._generation_history = None
            
            return location_result
            
        except Exception as e:
            # エラーハンドリング
            return ErrorHandler.create_error_result(location, e)
    
    def generate_comments_batch(
        self, 
        locations: List[str], 
        llm_provider: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None, 
        max_workers: int = 3
    ) -> BatchGenerationResult:
        """複数地点のコメント生成（並列処理版）"""
        # asyncio版を試す（利用可能な場合）
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既存のイベントループ内では同期版を使用
                return self._batch_processor.process_batch_sync(
                    locations, llm_provider, 
                    self.generate_comment_for_location,
                    progress_callback, max_workers
                )
            else:
                # 新しいイベントループで非同期版を実行
                return asyncio.run(
                    self._batch_processor.process_batch_async(
                        locations, llm_provider,
                        self.generate_comment_for_location,
                        progress_callback, max_workers
                    )
                )
        except RuntimeError:
            # asyncioが利用できない場合は同期版にフォールバック
            return self._batch_processor.process_batch_sync(
                locations, llm_provider,
                self.generate_comment_for_location,
                progress_callback, max_workers
            )
    
    def format_forecast_time(self, forecast_time: str) -> str:
        """予報時刻をフォーマット"""
        return self._metadata_extractor.format_forecast_time(forecast_time)
    
    def extract_weather_metadata(self, result: LocationResult) -> Dict[str, str | float | None]:
        """結果から天気メタデータを抽出"""
        return self._metadata_extractor.extract_weather_metadata(result)
    
    def validate_location_count(self, locations: List[str]) -> tuple[bool, Optional[str]]:
        """地点数の検証"""
        return self._validators.validate_location_count(locations)
    
    def generate_with_progress(
        self, 
        locations: List[str], 
        llm_provider: str,
        view, 
        results_container
    ) -> BatchGenerationResult:
        """プログレスバー付きでコメントを生成（Streamlit UI連携）"""
        import streamlit as st
        from app_session_manager import SessionManager
        
        # ヘッダーを一度だけ表示
        with results_container.container():
            st.markdown("### 🌤️ 生成結果")
        
        # プログレスUI作成
        progress_bar, status_text = view.create_progress_ui()
        
        # 生成中フラグを立てる
        SessionManager.set_generating(True)
        
        # 結果を格納する変数を事前に初期化
        all_results = []
        
        try:
            # 進捗コールバック関数
            def progress_callback(idx: int, total: int, location: str) -> None:
                self._progress_handler.update_progress(
                    progress_bar, status_text, idx, total, location,
                    results_container, all_results, view
                )
            
            # 並列処理で複数地点を処理
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 各地点の処理をサブミット
                future_to_location = {}
                for location in locations:
                    future = executor.submit(
                        self.generate_comment_for_location,
                        location,
                        llm_provider
                    )
                    future_to_location[future] = location
                
                # 完了した順に結果を処理
                completed_count = 0
                for future in as_completed(future_to_location):
                    location = future_to_location[future]
                    completed_count += 1
                    
                    # 進捗更新
                    progress_callback(completed_count - 1, len(locations), location)
                    
                    # 結果処理
                    location_result = self._progress_handler.handle_completed_future(
                        future, location, all_results, results_container, view
                    )
            
            # 最終結果を集計
            result = self._progress_handler.aggregate_results(all_results, locations)
            
            # 完了処理
            view.complete_progress(progress_bar, status_text, result['success_count'], len(locations))
            
            return result
            
        finally:
            SessionManager.set_generating(False)