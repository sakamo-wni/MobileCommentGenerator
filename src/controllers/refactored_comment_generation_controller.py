"""リファクタリングされたコメント生成コントローラー

単一責任原則に従い、責務を適切に分離。
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.types import LocationResult, BatchGenerationResult
from src.utils.error_handler import ErrorHandler
from src.utils.cpu_optimizer import CPUOptimizer
from src.workflows.comment_generation_workflow import run_comment_generation
from src.controllers.metadata_extractor import MetadataExtractor
from src.controllers.validators import ValidationManager
from src.controllers.batch_processor import BatchProcessor
from src.controllers.progress_handler import ProgressHandler
from src.controllers.async_batch_processor import AsyncBatchProcessor
from src.controllers.history_manager import HistoryManager
from src.controllers.config_manager import ConfigManager
from app_interfaces import ICommentGenerationController

logger = logging.getLogger(__name__)


class RefactoredCommentGenerationController(ICommentGenerationController):
    """リファクタリングされたコメント生成コントローラー
    
    各責務を専門のマネージャーに委譲し、自身はコーディネーターとして動作。
    """
    
    def __init__(self, config=None):
        # 各マネージャーの初期化
        self._config_manager = ConfigManager(config)
        self._history_manager = HistoryManager()
        self._metadata_extractor = MetadataExtractor()
        self._validators = ValidationManager(self._config_manager.config)
        self._progress_handler = ProgressHandler(self._metadata_extractor)
        self._batch_processor = BatchProcessor(self._progress_handler)
        
    # === 設定関連のメソッド（ConfigManagerに委譲）===
    
    @property
    def config(self):
        return self._config_manager.config
    
    def get_default_locations(self) -> list[str]:
        return self._config_manager.get_default_locations()
    
    def get_default_llm_provider(self) -> str:
        return self._config_manager.get_default_llm_provider()
    
    def get_config_dict(self) -> dict[str, str | int | float | bool]:
        return self._config_manager.get_config_dict()
    
    # === 履歴関連のメソッド（HistoryManagerに委譲）===
    
    @property
    def generation_history(self) -> list[dict[str, str]]:
        return self._history_manager.generation_history
    
    # === 検証関連のメソッド（ValidationManagerに委譲）===
    
    def validate_configuration(self) -> dict[str, bool | str]:
        return self._validators.validate_configuration()
    
    def validate_location_count(self, locations: list[str]) -> tuple[bool, str | None]:
        return self._validators.validate_location_count(locations)
    
    # === メタデータ関連のメソッド（MetadataExtractorに委譲）===
    
    def format_forecast_time(self, forecast_time: str) -> str:
        return self._metadata_extractor.format_forecast_time(forecast_time)
    
    def extract_weather_metadata(self, result: LocationResult) -> dict[str, str | float | None]:
        return self._metadata_extractor.extract_weather_metadata(result)
    
    # === コメント生成のコアロジック ===
    
    def generate_comment_for_location(self, location: str, llm_provider: str) -> LocationResult:
        """単一地点のコメント生成"""
        try:
            # 実際のコメント生成
            result = run_comment_generation(
                location_name=location,
                target_datetime=None,
                llm_provider=llm_provider
            )
            
            # デバッグログ（必要に応じて別クラスに移動可能）
            self._log_weather_timeline(location, result)
            
            # 結果を構築
            location_result = self._build_location_result(location, result)
            
            # 履歴に保存
            self._history_manager.save_generation_result(result, location, llm_provider)
            
            return location_result
            
        except Exception as e:
            return ErrorHandler.create_error_result(location, e)
    
    def generate_comments_batch(
        self, 
        locations: list[str], 
        llm_provider: str,
        progress_callback: Callable[[int, int, str | None], None] | None = None, 
        max_workers: int | None = None
    ) -> BatchGenerationResult:
        """複数地点のコメント生成（並列処理版）"""
        # 最適な並列度を決定
        if max_workers is None:
            max_workers = CPUOptimizer.get_io_bound_workers(
                task_count=len(locations),
                max_workers=16
            )
            logger.info(f"Optimized max_workers: {max_workers} (locations: {len(locations)})")
        
        # 非同期版の使用判定
        if self._config_manager.is_async_weather_enabled():
            logger.info("🚀 非同期版APIクライアントを使用")
            async_processor = AsyncBatchProcessor()
            try:
                return asyncio.run(
                    async_processor.generate_comments_batch_async(
                        locations, llm_provider, progress_callback
                    )
                )
            except Exception as e:
                logger.error(f"非同期処理でエラー発生: {e}")
        
        # 同期版を使用
        logger.info("同期版APIクライアントを使用")
        return self._batch_processor.process_batch_sync(
            locations, llm_provider, 
            self.generate_comment_for_location,
            progress_callback, max_workers
        )
    
    def generate_with_progress(
        self, 
        locations: list[str], 
        llm_provider: str,
        view, 
        results_container
    ) -> BatchGenerationResult:
        """プログレスバー付きでコメントを生成（Streamlit UI連携）"""
        import streamlit as st
        from app_session_manager import SessionManager
        
        # UI初期化
        with results_container.container():
            st.markdown("### 🌤️ 生成結果")
        
        progress_bar, status_text = view.create_progress_ui()
        SessionManager.set_generating(True)
        
        all_results = []
        
        try:
            # 進捗コールバック関数
            def progress_callback(idx: int, total: int, location: str) -> None:
                self._progress_handler.update_progress(
                    progress_bar, status_text, idx, total, location,
                    results_container, all_results, view
                )
            
            # バッチ処理実行
            return self._execute_batch_with_progress(
                locations, llm_provider, progress_callback, 
                all_results, results_container, view
            )
            
        finally:
            SessionManager.set_generating(False)
            progress_bar.empty()
            status_text.empty()
    
    # === プライベートメソッド ===
    
    def _log_weather_timeline(self, location: str, result: dict[str, Any]) -> None:
        """weather_timelineのデバッグログ出力"""
        generation_metadata = result.get('generation_metadata', {})
        weather_timeline = generation_metadata.get('weather_timeline', {})
        if weather_timeline:
            future_forecasts = weather_timeline.get('future_forecasts', [])
            logger.info(f"Controller: location={location}, weather_timeline存在, future_forecasts数={len(future_forecasts)}")
            if future_forecasts:
                logger.debug(f"Controller: future_forecasts[0]={future_forecasts[0]}")
        else:
            logger.warning(f"Controller: location={location}, weather_timelineが存在しません")
    
    def _build_location_result(self, location: str, result: dict[str, Any]) -> LocationResult:
        """LocationResult型の結果を構築"""
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
        
        return location_result
    
    def _execute_batch_with_progress(
        self,
        locations: list[str],
        llm_provider: str,
        progress_callback: Callable,
        all_results: list[LocationResult],
        results_container,
        view
    ) -> BatchGenerationResult:
        """プログレス表示付きバッチ処理の実行"""
        total_locations = len(locations)
        
        # 最適な並列度を決定
        max_workers = CPUOptimizer.get_io_bound_workers(
            task_count=total_locations,
            max_workers=16
        )
        logger.info(f"Optimized max_workers for batch: {max_workers}")
        
        # 並列処理で複数地点を処理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                progress_callback(completed_count - 1, total_locations, location)
                
                # 結果を取得
                try:
                    location_result = future.result()
                    all_results.append(location_result)
                except Exception as e:
                    logger.error(f"Error processing {location}: {e}")
                    location_result = ErrorHandler.create_error_result(location, e)
                    all_results.append(location_result)
        
        # 結果を集約
        return self._progress_handler.aggregate_results(all_results, locations)