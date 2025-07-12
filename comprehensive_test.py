"""包括的なパフォーマンステスト"""

import time
import os
from src.apis.wxtech.client import WxTechAPIClient
from src.data.location.manager import LocationManagerRefactored

def measure_api_performance():
    """API呼び出しのパフォーマンスを測定"""
    print("=== APIパフォーマンステスト ===\n")
    
    # 環境変数の設定
    api_key = os.environ.get("WXTECH_API_KEY")
    if not api_key:
        print("WXTECH_API_KEYが設定されていません")
        return
    
    # キャッシュ無効でテスト
    print("1. キャッシュ無効:")
    client_no_cache = WxTechAPIClient(api_key, enable_cache=False)
    
    start = time.time()
    try:
        # 東京の天気を取得
        result = client_no_cache.get_forecast(35.6762, 139.6503, forecast_hours=24)
        elapsed = time.time() - start
        print(f"  実行時間: {elapsed:.3f}秒")
    except Exception as e:
        print(f"  エラー: {str(e)}")
    
    # キャッシュ有効でテスト
    print("\n2. キャッシュ有効:")
    client_with_cache = WxTechAPIClient(api_key, enable_cache=True)
    
    # 初回（キャッシュミス）
    start = time.time()
    try:
        result = client_with_cache.get_forecast(35.6762, 139.6503, forecast_hours=24)
        elapsed = time.time() - start
        print(f"  初回実行時間: {elapsed:.3f}秒")
    except Exception as e:
        print(f"  エラー: {str(e)}")
    
    # 2回目（キャッシュヒット）
    start = time.time()
    try:
        result = client_with_cache.get_forecast(35.6762, 139.6503, forecast_hours=24)
        elapsed = time.time() - start
        print(f"  2回目実行時間: {elapsed:.3f}秒")
    except Exception as e:
        print(f"  エラー: {str(e)}")
    
    # キャッシュ統計
    stats = client_with_cache.get_cache_stats()
    if stats:
        print(f"  キャッシュヒット率: {stats['hit_rate']:.1%}")

def measure_location_search():
    """地点検索のパフォーマンスを測定"""
    print("\n\n=== 地点検索パフォーマンステスト ===\n")
    
    try:
        manager = LocationManagerRefactored()
        print(f"ロードされた地点数: {len(manager.locations)}")
        
        # 検索テスト
        test_queries = ["東京", "大阪", "札幌", "福岡", "那覇", "稚内", "仙台", "広島", "金沢", "高松"]
        
        # ウォームアップ
        for query in test_queries[:3]:
            manager.get_location(query)
        
        # 実測定
        start = time.time()
        for _ in range(100):  # 100回繰り返し
            for query in test_queries:
                manager.get_location(query)
        elapsed = time.time() - start
        
        total_searches = 100 * len(test_queries)
        print(f"合計検索数: {total_searches}")
        print(f"総実行時間: {elapsed:.3f}秒")
        print(f"1検索あたり: {elapsed/total_searches*1000:.3f}ms")
        
    except Exception as e:
        print(f"エラー: {str(e)}")

def measure_memory_usage():
    """メモリ使用量を測定"""
    print("\n\n=== メモリ使用量 ===\n")
    print("（psutilモジュールが未インストールのためスキップ）")

def main():
    """メイン処理"""
    print("包括的パフォーマンステスト")
    print("=" * 50)
    
    # 各テストを実行
    measure_api_performance()
    measure_location_search()
    measure_memory_usage()
    
    print("\n完了！")

if __name__ == "__main__":
    main()