"""シンプルなパフォーマンステスト"""

import time
from src.data.location.manager import LocationManagerRefactored
from src.data.location.search_engine import LocationSearchEngine

def test_location_search():
    """地点検索のパフォーマンステスト"""
    print("=== 地点検索パフォーマンステスト ===\n")
    
    # LocationManagerのテスト
    print("1. LocationManagerRefactored:")
    manager = LocationManagerRefactored()
    
    test_queries = ["東京", "大阪", "札幌", "福岡", "那覇"]
    
    # 5回測定
    times = []
    for i in range(5):
        start = time.time()
        for query in test_queries:
            manager.get_location(query)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"  平均実行時間: {avg_time:.3f}秒")
    print(f"  1クエリあたり: {avg_time/len(test_queries)*1000:.3f}ms")
    
    # SearchEngineのダイレクトテスト
    print("\n2. LocationSearchEngine:")
    engine = LocationSearchEngine(manager.locations)
    
    # 5回測定
    times = []
    for i in range(5):
        start = time.time()
        for query in test_queries:
            engine.get_location(query)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"  平均実行時間: {avg_time:.3f}秒")
    print(f"  1クエリあたり: {avg_time/len(test_queries)*1000:.3f}ms")

if __name__ == "__main__":
    test_location_search()