"""
Parallel comment generation processor

並列コメント生成プロセッサー
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.workflows.comment_generation_workflow import run_comment_generation
from src.types import LocationResult, BatchGenerationResult
from src.utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class ParallelCommentGenerator:
    """並列コメント生成器
    
    複数地点のコメント生成を並列実行して
    レスポンスタイムを短縮
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 timeout_per_location: int = 30):
        """初期化
        
        Args:
            max_workers: 最大ワーカー数
            timeout_per_location: 地点ごとのタイムアウト（秒）
        """
        self.max_workers = max_workers
        self.timeout_per_location = timeout_per_location
        self._lock = threading.Lock()
        self._stats = {
            "parallel_processed": 0,
            "serial_processed": 0,
            "timeout_count": 0,
            "error_count": 0
        }
    
    def generate_parallel(self,
                         locations_with_weather: Dict[str, Any],
                         llm_provider: str = "gemini",
                         progress_callback: Optional[callable] = None) -> BatchGenerationResult:
        """複数地点のコメントを並列生成
        
        Args:
            locations_with_weather: 地点名と天気データの辞書
            llm_provider: LLMプロバイダー
            progress_callback: 進捗コールバック
            
        Returns:
            バッチ生成結果
        """
        start_time = datetime.now()
        all_results = []
        completed_count = 0
        
        # バッチサイズを決定（大量の地点の場合は制限）
        use_parallel = len(locations_with_weather) > 1 and len(locations_with_weather) <= 20
        
        if use_parallel:
            logger.info(f"🚀 {len(locations_with_weather)}地点のコメントを並列生成開始（最大{self.max_workers}並列）")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 各地点のタスクを送信
                future_to_location = {}
                
                for location, weather_data in locations_with_weather.items():
                    if weather_data:
                        future = executor.submit(
                            self._generate_single_comment,
                            location,
                            weather_data,
                            llm_provider
                        )
                        future_to_location[future] = location
                    else:
                        # 天気データがない場合はエラー結果を追加
                        result = ErrorHandler.create_error_result(
                            location,
                            ValueError("天気予報データがありません")
                        )
                        all_results.append(result)
                        completed_count += 1
                        
                        if progress_callback:
                            progress_callback(completed_count, len(locations_with_weather), location)
                
                # 完了したタスクから順に処理
                for future in as_completed(future_to_location, timeout=self.timeout_per_location * len(future_to_location)):
                    location = future_to_location[future]
                    
                    try:
                        result = future.result(timeout=self.timeout_per_location)
                        all_results.append(result)
                        
                        with self._lock:
                            self._stats["parallel_processed"] += 1
                            
                    except TimeoutError:
                        logger.error(f"タイムアウト: {location}")
                        result = ErrorHandler.create_error_result(
                            location,
                            TimeoutError(f"コメント生成がタイムアウトしました（{self.timeout_per_location}秒）")
                        )
                        all_results.append(result)
                        
                        with self._lock:
                            self._stats["timeout_count"] += 1
                            
                    except Exception as e:
                        logger.error(f"並列処理エラー: {location} - {e}")
                        result = ErrorHandler.create_error_result(location, e)
                        all_results.append(result)
                        
                        with self._lock:
                            self._stats["error_count"] += 1
                    
                    completed_count += 1
                    if progress_callback:
                        progress_callback(completed_count, len(locations_with_weather), location)
        
        else:
            # シリアル処理（少数または大量の場合）
            logger.info(f"📝 {len(locations_with_weather)}地点のコメントをシリアル生成")
            
            for location, weather_data in locations_with_weather.items():
                try:
                    if weather_data:
                        result = self._generate_single_comment(location, weather_data, llm_provider)
                    else:
                        result = ErrorHandler.create_error_result(
                            location,
                            ValueError("天気予報データがありません")
                        )
                    
                    all_results.append(result)
                    
                    with self._lock:
                        self._stats["serial_processed"] += 1
                        
                except Exception as e:
                    logger.error(f"コメント生成エラー: {location} - {e}")
                    result = ErrorHandler.create_error_result(location, e)
                    all_results.append(result)
                    
                    with self._lock:
                        self._stats["error_count"] += 1
                
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(locations_with_weather), location)
        
        # 結果を集計
        success_count = sum(1 for r in all_results if r["success"])
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"✅ コメント生成完了: "
            f"成功={success_count}/{len(locations_with_weather)}, "
            f"時間={processing_time:.1f}秒, "
            f"並列={self._stats['parallel_processed']}, "
            f"シリアル={self._stats['serial_processed']}"
        )
        
        return BatchGenerationResult(
            results=all_results,
            total_count=len(locations_with_weather),
            success_count=success_count,
            failed_count=len(locations_with_weather) - success_count,
            processing_time=processing_time
        )
    
    def _generate_single_comment(self,
                               location: str,
                               weather_data: Any,
                               llm_provider: str) -> LocationResult:
        """単一地点のコメントを生成
        
        Args:
            location: 地点名
            weather_data: 天気データ
            llm_provider: LLMプロバイダー
            
        Returns:
            地点結果
        """
        try:
            # コメント生成ワークフローを実行
            result = run_comment_generation(
                location_name=location,
                llm_provider=llm_provider,
                pre_fetched_weather=weather_data
            )
            
            return LocationResult(
                location=location,
                success=True,
                comment=result.get("final_comment", ""),
                advice=result.get("advice_comment", ""),
                weather_summary=result.get("weather_summary", ""),
                generation_metadata=result.get("generation_metadata", {})
            )
            
        except Exception as e:
            logger.error(f"コメント生成エラー: {location} - {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            total_processed = (
                self._stats["parallel_processed"] + 
                self._stats["serial_processed"]
            )
            
            return {
                "total_processed": total_processed,
                "parallel_processed": self._stats["parallel_processed"],
                "serial_processed": self._stats["serial_processed"],
                "timeout_count": self._stats["timeout_count"],
                "error_count": self._stats["error_count"],
                "max_workers": self.max_workers,
                "timeout_per_location": self.timeout_per_location
            }
    
    async def generate_parallel_async(self,
                                    locations_with_weather: Dict[str, Any],
                                    llm_provider: str = "gemini",
                                    progress_callback: Optional[callable] = None) -> BatchGenerationResult:
        """非同期インターフェース（内部では同期処理）
        
        asyncioイベントループ内から呼び出すためのラッパー
        """
        loop = asyncio.get_event_loop()
        
        # ThreadPoolExecutorで実行
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self.generate_parallel,
                locations_with_weather,
                llm_provider,
                progress_callback
            )
        
        return result