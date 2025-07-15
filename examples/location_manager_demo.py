"""
地点データ管理システムのデモ

Issue #2: 地点データ管理システムの使用例
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.location import Location
from src.data.location.manager import LocationManagerRefactored


def demo_basic_usage():
    """基本的な使用方法のデモ"""
    print("=== 基本的な使用方法 ===")

    # LocationManagerの初期化
    manager = LocationManagerRefactored()

    # 統計情報の表示
    stats = manager.get_statistics()
    print(f"読み込み地点数: {stats['total_locations']}")
    print(f"CSV パス: {stats['csv_path']}")
    print()


def demo_search_functionality():
    """検索機能のデモ"""
    print("=== 検索機能デモ ===")

    manager = LocationManagerRefactored()

    # 完全一致検索
    print("1. 完全一致検索")
    results = manager.search_location("東京", fuzzy=False)
    for result in results[:3]:
        print(f"  - {result.name} ({result.prefecture}, {result.region})")
    print()

    # 部分一致検索
    print("2. 部分一致検索（「大」を含む地点）")
    results = manager.search_location("大", fuzzy=False)
    for result in results[:5]:
        print(f"  - {result.name} ({result.prefecture})")
    print()

    # あいまい検索
    print("3. あいまい検索（「おおさか」）")
    results = manager.search_location("おおさか", fuzzy=True)
    for result in results[:3]:
        print(f"  - {result.name} ({result.prefecture})")
    print()


def demo_location_details():
    """地点詳細情報のデモ"""
    print("=== 地点詳細情報 ===")

    manager = LocationManagerRefactored()

    # 特定の地点を取得
    tokyo = manager.get_location_by_name("東京")
    if tokyo:
        print("東京の詳細情報:")
        location_dict = tokyo.to_dict()
        for key, value in location_dict.items():
            print(f"  {key}: {value}")
        print()

    # 札幌の情報
    sapporo = manager.get_location_by_name("札幌")
    if sapporo:
        print("札幌の詳細情報:")
        print(f"  名前: {sapporo.name}")
        print(f"  正規化名: {sapporo.normalized_name}")
        print(f"  都道府県: {sapporo.prefecture}")
        print(f"  地方: {sapporo.region}")
        print()


def demo_regional_filtering():
    """地方・都道府県別フィルタリングのデモ"""
    print("=== 地方・都道府県別フィルタリング ===")

    manager = LocationManagerRefactored()

    # 関東地方の地点
    print("1. 関東地方の地点:")
    kanto_locations = manager.get_locations_by_region("関東")
    for location in kanto_locations[:5]:
        print(f"  - {location.name} ({location.prefecture})")
    print(f"  総数: {len(kanto_locations)}地点")
    print()

    # 北海道の地点
    print("2. 北海道の地点:")
    hokkaido_locations = manager.get_locations_by_prefecture("北海道")
    for location in hokkaido_locations[:5]:
        print(f"  - {location.name}")
    print(f"  総数: {len(hokkaido_locations)}地点")
    print()


def demo_distance_calculation():
    """距離計算のデモ"""
    print("=== 距離計算デモ ===")

    # 座標付きの地点を作成
    tokyo = Location(name="東京", normalized_name="東京", latitude=35.6762, longitude=139.6503)

    osaka = Location(name="大阪", normalized_name="大阪", latitude=34.6937, longitude=135.5023)

    nagoya = Location(name="名古屋", normalized_name="名古屋", latitude=35.1815, longitude=136.9066)

    # 距離計算
    distance_to_osaka = tokyo.distance_to(osaka)
    distance_to_nagoya = tokyo.distance_to(nagoya)

    print("東京からの距離:")
    if distance_to_osaka:
        print(f"  大阪まで: {distance_to_osaka:.1f} km")
    if distance_to_nagoya:
        print(f"  名古屋まで: {distance_to_nagoya:.1f} km")
    print()


def demo_statistics():
    """統計情報のデモ"""
    print("=== 統計情報 ===")

    manager = LocationManagerRefactored()
    stats = manager.get_statistics()

    print(f"総地点数: {stats['total_locations']}")
    print()

    print("地方別分布:")
    for region, count in list(stats["regions"].items())[:8]:
        print(f"  {region}: {count}地点")
    print()

    print("都道府県別分布（上位10）:")
    for prefecture, count in list(stats["prefectures"].items())[:10]:
        print(f"  {prefecture}: {count}地点")
    print()


def demo_advanced_search():
    """高度な検索のデモ"""
    print("=== 高度な検索機能 ===")

    manager = LocationManagerRefactored()

    # 複数の検索条件
    search_queries = ["京", "川", "山", "田"]

    for query in search_queries:
        print(f"「{query}」を含む地点（上位3件）:")
        results = manager.search_location(query, max_results=3)
        for result in results:
            print(f"  - {result.name} ({result.prefecture})")
        print()


def demo_location_matching():
    """地点マッチング機能のデモ"""
    print("=== 地点マッチング機能 ===")

    manager = LocationManagerRefactored()

    # 異なる表記での検索テスト
    test_queries = ["東京", "とうきょう", "Tokyo", "大阪", "おおさか", "Osaka", "札幌", "さっぽろ"]

    for query in test_queries:
        results = manager.search_location(query, max_results=1, fuzzy=True)
        if results:
            result = results[0]
            print(f"「{query}」 → {result.name} ({result.prefecture})")
        else:
            print(f"「{query}」 → マッチなし")
    print()


def demo_error_handling():
    """エラーハンドリングのデモ"""
    print("=== エラーハンドリング ===")

    manager = LocationManagerRefactored()

    # 存在しない地点の検索
    result = manager.get_location_by_name("存在しない地点")
    print(f"存在しない地点の検索: {result}")

    # 空文字列での検索
    results = manager.search_location("")
    print(f"空文字列での検索結果: {len(results)}件")

    # 非常に長い文字列での検索
    long_query = "あ" * 100
    results = manager.search_location(long_query)
    print(f"長い文字列での検索結果: {len(results)}件")
    print()


def demo_performance():
    """パフォーマンステスト"""
    print("=== パフォーマンステスト ===")

    import time

    manager = LocationManagerRefactored()

    # 検索性能テスト
    queries = ["東京", "大阪", "名古屋", "札幌", "福岡"]

    start_time = time.time()
    for _ in range(100):
        for query in queries:
            manager.search_location(query)
    end_time = time.time()

    total_searches = 100 * len(queries)
    avg_time = (end_time - start_time) / total_searches * 1000

    print(f"検索性能: {total_searches}回検索を {end_time - start_time:.3f}秒で実行")
    print(f"平均検索時間: {avg_time:.2f}ms")
    print()


def main():
    """メインデモ実行"""
    print("地点データ管理システム デモプログラム")
    print("=" * 50)
    print()

    try:
        demo_basic_usage()
        demo_search_functionality()
        demo_location_details()
        demo_regional_filtering()
        demo_distance_calculation()
        demo_statistics()
        demo_advanced_search()
        demo_location_matching()
        demo_error_handling()
        demo_performance()

        print("=" * 50)
        print("デモ完了！")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()