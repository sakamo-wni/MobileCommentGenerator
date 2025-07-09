#!/usr/bin/env python3
"""
最適化実装の動作確認テスト

実際の実装で最適化版が正しく動作することを確認
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime
import logging
from dotenv import load_dotenv

from src.nodes.weather_forecast.data_fetcher import WeatherDataFetcher
from src.config.weather_settings import WeatherConfig

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()


async def test_weather_data_fetcher():
    """WeatherDataFetcherの最適化版をテスト"""
    logger.info("=" * 80)
    logger.info("🧪 WeatherDataFetcher最適化版テスト")
    logger.info("=" * 80)
    
    # API キーの確認
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        logger.error("❌ WXTECH_API_KEY が設定されていません")
        sys.exit(1)
    
    # WeatherConfigの確認
    weather_config = WeatherConfig()
    logger.info(f"📋 設定確認:")
    logger.info(f"  use_optimized_forecast: {weather_config.use_optimized_forecast}")
    logger.info(f"  enable_caching: {weather_config.enable_caching}")
    
    # データフェッチャーを初期化
    fetcher = WeatherDataFetcher(api_key)
    
    # テスト地点
    test_locations = [
        "東京",
        "大阪",
        "札幌"
    ]
    
    for location_name in test_locations:
        logger.info(f"\n📍 地点: {location_name}")
        
        try:
            # 非同期でデータ取得
            start_time = datetime.now()
            forecast_collection = await fetcher.fetch_weather_data(location_name)
            end_time = datetime.now()
            
            logger.info(f"✅ データ取得成功")
            logger.info(f"  実行時間: {(end_time - start_time).total_seconds():.2f}秒")
            logger.info(f"  取得データ数: {len(forecast_collection.forecasts)}件")
            
            # データの内容を確認
            if forecast_collection.forecasts:
                logger.info(f"  データ内容:")
                for i, forecast in enumerate(forecast_collection.forecasts):
                    logger.info(
                        f"    {i+1}. {forecast.datetime.strftime('%Y-%m-%d %H:%M')} - "
                        f"{forecast.weather_description} ({forecast.temperature}℃)"
                    )
                
                # 時刻の確認
                hours = [f.datetime.hour for f in forecast_collection.forecasts]
                logger.info(f"  取得時刻: {sorted(set(hours))}")
                
                # 最適化版の場合、4件のみであることを確認
                if weather_config.use_optimized_forecast:
                    if len(forecast_collection.forecasts) == 4:
                        logger.info("  ✅ 最適化版: 正確に4件のデータを取得")
                    else:
                        logger.warning(f"  ⚠️ 最適化版: 期待値4件に対して{len(forecast_collection.forecasts)}件")
            
        except Exception as e:
            logger.error(f"❌ エラー: {e}")


def test_sync_version():
    """同期版のテスト（ワークフロー用）"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 同期版（fetch_for_workflow）テスト")
    logger.info("=" * 80)
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        logger.error("❌ WXTECH_API_KEY が設定されていません")
        return
    
    fetcher = WeatherDataFetcher(api_key)
    
    try:
        # 東京のデータを取得
        forecast_collection, location = fetcher.fetch_for_workflow("東京")
        
        logger.info(f"✅ データ取得成功")
        logger.info(f"  地点: {location.name} ({location.latitude}, {location.longitude})")
        logger.info(f"  取得データ数: {len(forecast_collection.forecasts)}件")
        
        # データの詳細
        for i, forecast in enumerate(forecast_collection.forecasts):
            logger.info(
                f"  {i+1}. {forecast.datetime.strftime('%Y-%m-%d %H:%M')} - "
                f"{forecast.weather_description}"
            )
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")


def compare_optimized_vs_normal():
    """最適化版と通常版の比較"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 最適化版 vs 通常版の比較")
    logger.info("=" * 80)
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        return
    
    # 一時的に最適化を無効化してテスト
    os.environ["WEATHER_USE_OPTIMIZED_FORECAST"] = "false"
    fetcher_normal = WeatherDataFetcher(api_key)
    
    # 最適化を有効化
    os.environ["WEATHER_USE_OPTIMIZED_FORECAST"] = "true"
    fetcher_optimized = WeatherDataFetcher(api_key)
    
    try:
        # 通常版
        logger.info("\n📌 通常版:")
        start = datetime.now()
        normal_result, _ = fetcher_normal.fetch_for_workflow("東京")
        end = datetime.now()
        normal_time = (end - start).total_seconds()
        logger.info(f"  データ数: {len(normal_result.forecasts)}件")
        logger.info(f"  実行時間: {normal_time:.2f}秒")
        
        # 最適化版
        logger.info("\n📌 最適化版:")
        start = datetime.now()
        optimized_result, _ = fetcher_optimized.fetch_for_workflow("東京")
        end = datetime.now()
        optimized_time = (end - start).total_seconds()
        logger.info(f"  データ数: {len(optimized_result.forecasts)}件")
        logger.info(f"  実行時間: {optimized_time:.2f}秒")
        
        # 比較結果
        logger.info("\n📈 比較結果:")
        reduction = (1 - len(optimized_result.forecasts) / len(normal_result.forecasts)) * 100
        logger.info(f"  データ削減率: {reduction:.1f}%")
        logger.info(f"  実行時間差: {optimized_time - normal_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
    
    finally:
        # 環境変数を元に戻す
        del os.environ["WEATHER_USE_OPTIMIZED_FORECAST"]


async def main():
    """メイン処理"""
    logger.info("🚀 最適化実装テスト開始")
    
    # 非同期版のテスト
    await test_weather_data_fetcher()
    
    # 同期版のテスト
    test_sync_version()
    
    # 比較テスト
    compare_optimized_vs_normal()
    
    logger.info("\n✅ すべてのテスト完了")


if __name__ == "__main__":
    asyncio.run(main())