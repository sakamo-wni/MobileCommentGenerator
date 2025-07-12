"""起動時間とインポート時間の測定"""

import time

def measure_import_times():
    """各モジュールのインポート時間を測定"""
    print("=== インポート時間の測定 ===\n")
    
    # 基本的なインポート
    start = time.time()
    import os
    import sys
    base_time = time.time() - start
    print(f"基本モジュール: {base_time:.3f}秒")
    
    # Trie実装のインポート
    start = time.time()
    from src.data.location.trie import LocationTrie
    trie_time = time.time() - start
    print(f"Trie実装: {trie_time:.3f}秒")
    
    # 検索エンジンのインポート
    start = time.time()
    from src.data.location.search_engine import LocationSearchEngine
    engine_time = time.time() - start
    print(f"検索エンジン: {engine_time:.3f}秒")
    
    # LocationManagerのインポート
    start = time.time()
    from src.data.location.manager import LocationManagerRefactored
    manager_time = time.time() - start
    print(f"LocationManager: {manager_time:.3f}秒")
    
    # キャッシュユーティリティのインポート
    start = time.time()
    from src.utils.cache import TTLCache, cached_method
    cache_time = time.time() - start
    print(f"キャッシュユーティリティ: {cache_time:.3f}秒")
    
    # APIクライアントのインポート
    start = time.time()
    from src.apis.wxtech.client import WxTechAPIClient
    client_time = time.time() - start
    print(f"APIクライアント: {client_time:.3f}秒")
    
    print(f"\n合計インポート時間: {base_time + trie_time + engine_time + manager_time + cache_time + client_time:.3f}秒")
    
    # 実際のインスタンス作成時間
    print("\n=== インスタンス作成時間 ===\n")
    
    # LocationManagerの作成
    start = time.time()
    manager = LocationManagerRefactored()
    manager_create_time = time.time() - start
    print(f"LocationManager作成: {manager_create_time:.3f}秒")
    print(f"  ロードされた地点数: {len(manager.locations)}")
    
    # Trie構築の詳細測定
    from src.data.location.models import Location
    test_locations = [
        Location(name=f"テスト地点{i:04d}", normalized_name=f"テスト地点{i:04d}")
        for i in range(1000)
    ]
    
    start = time.time()
    trie = LocationTrie()
    for loc in test_locations:
        trie.insert(loc.name, loc)
    trie_build_time = time.time() - start
    print(f"\nTrie構築（1000件）: {trie_build_time:.3f}秒")
    print(f"  1件あたり: {trie_build_time/1000*1000:.3f}ms")

if __name__ == "__main__":
    overall_start = time.time()
    measure_import_times()
    overall_time = time.time() - overall_start
    print(f"\n全体の実行時間: {overall_time:.3f}秒")