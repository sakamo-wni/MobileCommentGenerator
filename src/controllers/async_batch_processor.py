"""非同期バッチ処理モジュール

複数地点の天気予報を並列で非同期取得する最適化版
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any
from collections.abc import Callable
from datetime import datetime

from src.apis.wxtech.cached_client import CachedWxTechAPIClient
from src.nodes.weather_forecast.services import WeatherAPIService
from src.nodes.weather_forecast.service_factory import WeatherForecastServiceFactory
from src.config import get_config
from src.config.config import get_weather_config
from src.workflows.comment_generation_workflow import run_comment_generation
from src.types import LocationResult, BatchGenerationResult
from src.utils.error_handler import ErrorHandler
from src.data.forecast_cache import save_forecast_to_cache
from src.controllers.parallel_comment_generator import ParallelCommentGenerator

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """非同期バッチ処理を管理するクラス"""
    
    def __init__(self):
        self.config = get_config()
        self.weather_config = get_weather_config()
        self.parallel_generator = ParallelCommentGenerator(
            max_workers=4,  # 4並列でコメント生成
            timeout_per_location=30
        )
        
    async def fetch_all_weather_data_async(
        self, 
        locations: list[str]
    ) -> dict[str, Any]:
        """全地点の天気予報データを並列で非同期取得（真の非同期実装）
        
        Args:
            locations: 地点名のリスト
            
        Returns:
            地点名をキーとする天気予報データの辞書
        """
        api_key = self.config.api.wxtech_api_key
        service_factory = WeatherForecastServiceFactory(
            self.config, 
            self.weather_config, 
            api_key
        )
        
        # 地点情報サービスのみ取得
        location_service = service_factory.get_location_service()
        
        # 真の非同期クライアントを使用
        async with CachedWxTechAPIClient(api_key) as client:
            # 非同期タスクのリストを作成
            tasks = []
            location_map = {}
            
            for location_name in locations:
                # 地点情報の解析
                parsed_name, lat, lon = location_service.parse_location_input(location_name)
                try:
                    location = location_service.get_location_with_coordinates(parsed_name, lat, lon)
                    location_map[location_name] = location
                    
                    # 真の非同期タスクを作成
                    task = client.async_get_forecast_optimized(
                        location.latitude,
                        location.longitude
                    )
                    tasks.append((location_name, location, task))
                except Exception as e:
                    logger.error(f"地点情報の取得に失敗: {location_name} - {e}")
                    continue
            
            # 全タスクを並列実行
            logger.info(f"🚀 {len(tasks)}地点の天気予報を真の非同期で並列取得開始")
            weather_data = {}
            results = await asyncio.gather(
                *[task for _, _, task in tasks],
                return_exceptions=True
            )
            
            # 結果を辞書に格納
            for i, (location_name, location, _) in enumerate(tasks):
                if isinstance(results[i], Exception):
                    logger.error(f"天気予報取得エラー: {location_name} - {results[i]}")
                    weather_data[location_name] = None
                else:
                    # キャッシュに保存
                    try:
                        save_forecast_to_cache(results[i], location_name)
                    except Exception as e:
                        logger.warning(f"キャッシュ保存エラー: {location_name} - {e}")
                    
                    weather_data[location_name] = {
                        'forecast_collection': results[i],
                        'location': location
                    }
            
            logger.info(f"✅ 天気予報並列取得完了: {len([v for v in weather_data.values() if v])}地点成功")
                
        return weather_data
    
    async def generate_comments_batch_async(
        self,
        locations: list[str],
        llm_provider: str = "gemini",
        progress_callback: Callable[[int, int, str | None], None] | None = None
    ) -> BatchGenerationResult:
        """複数地点のコメントを非同期で生成
        
        Args:
            locations: 地点名のリスト
            llm_provider: LLMプロバイダー
            progress_callback: 進捗コールバック関数
            
        Returns:
            バッチ生成結果
        """
        start_time = datetime.now()
        
        # まず全地点の天気データを並列取得
        logger.info(f"🚀 {len(locations)}地点の天気予報を並列取得開始")
        weather_data = await self.fetch_all_weather_data_async(locations)
        logger.info(f"✅ 天気予報取得完了: {len(weather_data)}地点")
        
        # 次に各地点のコメント生成（並列処理）
        logger.info(f"🚀 {len(locations)}地点のコメントを並列生成開始")
        
        # ParallelCommentGeneratorを使用して並列生成
        batch_result = await self.parallel_generator.generate_parallel_async(
            weather_data,
            llm_provider=llm_provider,
            progress_callback=progress_callback
        )
        
        logger.info(f"✅ コメント並列生成完了: {batch_result['success_count']}地点成功")
        
        # 統計情報をログ
        generator_stats = self.parallel_generator.get_stats()
        logger.info(
            f"📊 生成統計: "
            f"並列={generator_stats['parallel_processed']}, "
            f"シリアル={generator_stats['serial_processed']}, "
            f"タイムアウト={generator_stats['timeout_count']}, "
            f"エラー={generator_stats['error_count']}"
        )
        
        all_results = batch_result["results"]
        
        return batch_result


# 既存のコントローラーから呼び出すためのラッパー関数
async def run_async_batch_generation(
    locations: list[str],
    llm_provider: str = "gemini"
) -> BatchGenerationResult:
    """非同期バッチ生成を実行するラッパー関数"""
    processor = AsyncBatchProcessor()
    return await processor.generate_comments_batch_async(locations, llm_provider)