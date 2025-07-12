#!/usr/bin/env python3
"""APIクライアント統合のテスト"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from src.apis.wxtech import WxTechAPIClient
from src.apis.wxtech.errors import WxTechAPIError

# 環境変数をロード
load_dotenv()


def test_sync_client():
    """同期クライアントのテスト"""
    print("=== 同期クライアントのテスト ===")
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        print("エラー: WXTECH_API_KEYが設定されていません")
        return
    
    try:
        client = WxTechAPIClient(api_key, enable_cache=True)
        
        # 東京の天気予報を取得
        lat, lon = 35.6762, 139.6503
        forecast = client.get_forecast(lat, lon, forecast_hours=24)
        
        print(f"取得した予報数: {len(forecast.forecasts)}")
        if forecast.forecasts:
            first = forecast.forecasts[0]
            print(f"最初の予報: {first.datetime} - {first.weather_description}")
        
        # キャッシュ統計を表示
        cache_stats = client.get_cache_stats()
        if cache_stats:
            print(f"キャッシュ統計: {cache_stats}")
        
        print("✅ 同期クライアントのテスト成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")


async def test_async_client():
    """非同期クライアントのテスト"""
    print("\n=== 非同期クライアントのテスト ===")
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        print("エラー: WXTECH_API_KEYが設定されていません")
        return
    
    try:
        # 非同期コンテキストマネージャーを使用
        async with WxTechAPIClient(api_key, enable_cache=True) as client:
            # 大阪の天気予報を取得
            lat, lon = 34.6937, 135.5023
            forecast = await client.async_get_forecast_optimized(lat, lon)
            
            print(f"取得した予報数: {len(forecast.forecasts)}")
            if forecast.forecasts:
                first = forecast.forecasts[0]
                print(f"最初の予報: {first.datetime} - {first.weather_description}")
            
            print("✅ 非同期クライアントのテスト成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")


async def test_parallel_requests():
    """複数地点の並列リクエストのテスト"""
    print("\n=== 並列リクエストのテスト ===")
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        print("エラー: WXTECH_API_KEYが設定されていません")
        return
    
    locations = [
        ("東京", 35.6762, 139.6503),
        ("大阪", 34.6937, 135.5023),
        ("名古屋", 35.1815, 136.9066),
    ]
    
    try:
        async with WxTechAPIClient(api_key, enable_cache=False) as client:
            # 並列タスクを作成
            tasks = [
                client.async_get_forecast_optimized(lat, lon)
                for name, lat, lon in locations
            ]
            
            # 並列実行
            start_time = datetime.now()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now()
            
            # 結果を表示
            for (name, _, _), result in zip(locations, results):
                if isinstance(result, Exception):
                    print(f"{name}: エラー - {result}")
                else:
                    print(f"{name}: {len(result.forecasts)}件の予報を取得")
            
            elapsed = (end_time - start_time).total_seconds()
            print(f"\n実行時間: {elapsed:.2f}秒")
            print("✅ 並列リクエストのテスト成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")


def test_import_compatibility():
    """インポート互換性のテスト"""
    print("\n=== インポート互換性のテスト ===")
    
    try:
        # 新しいインポート方法
        from src.apis.wxtech import WxTechAPIClient as NewClient
        from src.apis.wxtech.errors import WxTechAPIError as NewError
        
        # 古いインポート方法（非推奨）
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from src.apis.wxtech_client import WxTechAPIClient as OldClient
            from src.apis.wxtech_client import WxTechAPIError as OldError
        
        # 同じクラスであることを確認
        assert NewClient is OldClient, "クライアントクラスが一致しません"
        assert NewError is OldError, "エラークラスが一致しません"
        
        print("✅ インポート互換性のテスト成功")
        
    except Exception as e:
        print(f"❌ エラー: {e}")


async def main():
    """メインテスト実行"""
    print("APIクライアント統合テスト")
    print("=" * 50)
    
    # 各テストを実行
    test_import_compatibility()
    test_sync_client()
    await test_async_client()
    await test_parallel_requests()
    
    print("\n" + "=" * 50)
    print("テスト完了")


if __name__ == "__main__":
    asyncio.run(main())