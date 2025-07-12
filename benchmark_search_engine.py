"""検索エンジンのベンチマークスクリプト"""

import time
import statistics
from typing import List

from src.data.location.models import Location
from src.data.location.search_engine import LocationSearchEngine


def create_test_dataset(size: int) -> List[Location]:
    """テストデータセットを生成"""
    locations = []
    prefectures = ["東京", "大阪", "愛知", "北海道", "福岡", "神奈川", "埼玉", "千葉"]
    
    for i in range(size):
        prefecture = prefectures[i % len(prefectures)]
        location = Location(
            name=f"テスト地点{i:06d}",
            normalized_name=f"テスト地点{i:06d}",
            prefecture=prefecture,
            latitude=35.0 + (i % 100) * 0.01,
            longitude=135.0 + (i % 100) * 0.01,
            region="関東" if prefecture in ["東京", "神奈川", "埼玉", "千葉"] else "その他",
            location_type="市",
            population=10000 + i * 100
        )
        locations.append(location)
    
    return locations


def benchmark_index_build(dataset_sizes: List[int]):
    """インデックス構築のベンチマーク"""
    print("\n=== インデックス構築のベンチマーク ===")
    print(f"{'データ件数':>10} | {'構築時間(秒)':>15} | {'1件あたり(ms)':>15}")
    print("-" * 45)
    
    for size in dataset_sizes:
        dataset = create_test_dataset(size)
        
        # 5回計測して平均を取る
        times = []
        for _ in range(5):
            start_time = time.time()
            engine = LocationSearchEngine(dataset)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        per_item = (avg_time / size) * 1000
        
        print(f"{size:10d} | {avg_time:15.3f} | {per_item:15.3f}")


def benchmark_search_operations(dataset_size: int):
    """検索操作のベンチマーク"""
    print(f"\n=== 検索操作のベンチマーク (データ件数: {dataset_size}) ===")
    
    dataset = create_test_dataset(dataset_size)
    engine = LocationSearchEngine(dataset)
    
    # 完全一致検索
    print("\n完全一致検索:")
    search_times = []
    for i in range(100):
        target = f"テスト地点{i:06d}"
        start_time = time.time()
        result = engine.get_location(target)
        elapsed = time.time() - start_time
        search_times.append(elapsed * 1000)  # ms
    
    print(f"  平均時間: {statistics.mean(search_times):.3f} ms")
    print(f"  最小時間: {min(search_times):.3f} ms")
    print(f"  最大時間: {max(search_times):.3f} ms")
    
    # 前方一致検索
    print("\n前方一致検索:")
    prefix_times = []
    test_prefixes = ["テスト", "テスト地", "テスト地点00", "テスト地点0000"]
    
    for prefix in test_prefixes:
        start_time = time.time()
        results = engine.prefix_trie.search_prefix(prefix)
        elapsed = time.time() - start_time
        prefix_times.append(elapsed * 1000)
        print(f"  '{prefix}': {elapsed * 1000:.3f} ms ({len(results)}件)")
    
    # メモリ使用状況
    print("\n統計情報:")
    stats = engine.get_statistics()
    for key, value in stats.items():
        if isinstance(value, int):
            print(f"  {key}: {value}")


def main():
    """メイン処理"""
    print("検索エンジンのパフォーマンスベンチマーク")
    print("=" * 50)
    
    # インデックス構築のベンチマーク
    dataset_sizes = [100, 500, 1000, 5000, 10000]
    benchmark_index_build(dataset_sizes)
    
    # 検索操作のベンチマーク
    benchmark_search_operations(10000)
    
    print("\n完了！")


if __name__ == "__main__":
    main()