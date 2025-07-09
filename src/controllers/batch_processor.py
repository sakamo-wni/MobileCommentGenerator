"""バッチ処理モジュール"""

import asyncio
import logging
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.types import LocationResult, BatchGenerationResult
from src.utils.error_handler import ErrorHandler
from src.controllers.progress_handler import ProgressHandler

logger = logging.getLogger(__name__)


class BatchProcessor:
    """バッチ処理を管理するクラス"""
    
    def __init__(self, progress_handler: ProgressHandler):
        self._progress_handler = progress_handler
    
    def _create_error_response(self, error: Exception) -> BatchGenerationResult:
        """エラーレスポンスを作成（共通エラーハンドリング）"""
        error_response = ErrorHandler.handle_error(error)
        return {
            'success': False,
            'error': error_response.error_message,
            'final_comment': None,
            'hint': error_response.hint,
            'total_locations': 0,
            'success_count': 0,
            'results': [],
            'errors': [error_response.error_message]
        }
    
    async def process_batch_async(
        self,
        locations: List[str],
        llm_provider: str,
        generate_func: Callable[[str, str], LocationResult],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        max_workers: int = 3
    ) -> BatchGenerationResult:
        """非同期バッチ処理（asyncio版）"""
        if not locations:
            return {'success': False, 'error': '地点が選択されていません'}
        
        all_results = []
        total_locations = len(locations)
        
        try:
            # セマフォで同時実行数を制限
            semaphore = asyncio.Semaphore(max_workers)
            
            # 非同期タスクを作成
            tasks = []
            for idx, location in enumerate(locations):
                task = asyncio.create_task(
                    self._process_single_location_with_callback(
                        generate_func, location, llm_provider, 
                        idx, total_locations, progress_callback, semaphore
                    )
                )
                tasks.append(task)
            
            # 全タスクの完了を待つ
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果を処理
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    location = locations[idx]
                    location_result = ErrorHandler.create_error_result(location, result)
                    all_results.append(location_result)
                else:
                    all_results.append(result)
            
            return self._progress_handler.aggregate_results(all_results, locations)
            
        except Exception as e:
            return self._create_error_response(e)
    
    async def _process_single_location_with_callback(
        self,
        generate_func: Callable[[str, str], LocationResult],
        location: str,
        llm_provider: str,
        idx: int,
        total: int,
        progress_callback: Optional[Callable[[int, int, str], None]],
        semaphore: asyncio.Semaphore
    ) -> LocationResult:
        """単一地点の処理（コールバック付き）"""
        result = await self._progress_handler.handle_single_location_async(
            generate_func, location, llm_provider, semaphore
        )
        
        # 進捗コールバック
        if progress_callback:
            progress_callback(idx, total, location)
        
        return result
    
    def process_batch_sync(
        self,
        locations: List[str],
        llm_provider: str,
        generate_func: Callable[[str, str], LocationResult],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        max_workers: int = 3
    ) -> BatchGenerationResult:
        """同期バッチ処理（ThreadPoolExecutor版）- 後方互換性のため"""
        if not locations:
            return {'success': False, 'error': '地点が選択されていません'}
        
        all_results = []
        total_locations = len(locations)
        completed_count = 0
        
        try:
            # 並列処理で複数地点を処理
            with ThreadPoolExecutor(max_workers=min(max_workers, total_locations)) as executor:
                # 各地点の処理をサブミット
                future_to_location = {}
                for location in locations:
                    future = executor.submit(
                        generate_func,
                        location,
                        llm_provider
                    )
                    future_to_location[future] = location
                
                # 完了した順に結果を処理
                for future in as_completed(future_to_location):
                    location = future_to_location[future]
                    completed_count += 1
                    
                    try:
                        # 結果を取得
                        location_result = future.result()
                        all_results.append(location_result)
                        
                        # 進捗コールバック
                        if progress_callback:
                            progress_callback(completed_count - 1, total_locations, location)
                            
                    except Exception as e:
                        # 個別地点のエラーをキャッチ
                        location_result = ErrorHandler.create_error_result(location, e)
                        all_results.append(location_result)
                        
                        # 進捗コールバック
                        if progress_callback:
                            progress_callback(completed_count - 1, total_locations, location)
            
            return self._progress_handler.aggregate_results(all_results, locations)
            
        except Exception as e:
            return self._create_error_response(e)