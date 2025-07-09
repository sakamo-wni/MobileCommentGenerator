"""進捗管理モジュール"""

import asyncio
from typing import List, Callable, Optional, Any
from concurrent.futures import Future

import streamlit as st
from src.types import LocationResult, BatchGenerationResult
from src.utils.error_handler import ErrorHandler
from src.controllers.metadata_extractor import MetadataExtractor


class ProgressHandler:
    """進捗管理を行うクラス"""
    
    def __init__(self, metadata_extractor: MetadataExtractor):
        self._metadata_extractor = metadata_extractor
    
    async def handle_single_location_async(
        self, 
        generate_func: Callable[[str, str], LocationResult],
        location: str,
        llm_provider: str,
        semaphore: asyncio.Semaphore
    ) -> LocationResult:
        """単一地点の非同期処理"""
        async with semaphore:
            # 同期関数を非同期で実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                generate_func, 
                location, 
                llm_provider
            )
            return result
    
    def update_progress(
        self,
        progress_bar: Any,
        status_text: Any,
        idx: int,
        total: int,
        location: str,
        results_container: Any,
        all_results: List[LocationResult],
        view: Any
    ) -> None:
        """進捗を更新"""
        view.update_progress(progress_bar, status_text, idx, total, location)
        
        # 中間結果の表示
        if idx > 0 and all_results:
            with results_container.container():
                for i in range(min(idx, len(all_results))):
                    result = all_results[i]
                    metadata = self._metadata_extractor.extract_weather_metadata(result)
                    if 'forecast_time' in metadata and metadata['forecast_time']:
                        metadata['forecast_time'] = self._metadata_extractor.format_forecast_time(
                            str(metadata['forecast_time'])
                        )
                    view.display_single_result(result, metadata)
    
    def handle_completed_future(
        self,
        future: Future,
        location: str,
        all_results: List[LocationResult],
        results_container: Any,
        view: Any
    ) -> LocationResult:
        """完了したFutureの処理"""
        try:
            location_result = future.result()
        except Exception as e:
            location_result = ErrorHandler.create_error_result(location, e)
        
        all_results.append(location_result)
        
        # 結果を即座に表示
        with results_container.container():
            metadata = self._metadata_extractor.extract_weather_metadata(location_result)
            if 'forecast_time' in metadata and metadata['forecast_time']:
                metadata['forecast_time'] = self._metadata_extractor.format_forecast_time(
                    str(metadata['forecast_time'])
                )
            view.display_single_result(location_result, metadata)
        
        return location_result
    
    @staticmethod
    def aggregate_results(all_results: List[LocationResult], locations: List[str]) -> BatchGenerationResult:
        """結果を集計"""
        success_count = sum(1 for r in all_results if r['success'])
        errors = [r for r in all_results if not r['success']]
        error_messages = []
        
        for err in errors:
            location = err['location']
            error_msg = err.get('error', '不明なエラー')
            error_messages.append(f"{location}: {error_msg}")
        
        return {
            'success': success_count > 0,
            'total_locations': len(locations),
            'success_count': success_count,
            'results': all_results,
            'final_comment': '\n'.join([f"{r['location']}: {r['comment']}" for r in all_results if r['success']]),
            'errors': error_messages
        }