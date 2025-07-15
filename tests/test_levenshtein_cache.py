"""
レーベンシュタイン距離計算のキャッシュ最適化テスト
"""

import pytest
import time
from src.data.location import Location, get_levenshtein_cache_info, clear_levenshtein_cache


class TestLevenshteinCache:
    """レーベンシュタイン距離計算のキャッシュテスト"""
    
    def setup_method(self):
        """各テストメソッドの前にキャッシュをクリア"""
        clear_levenshtein_cache()
    
    def test_cache_hit_rate(self):
        """キャッシュヒット率のテスト"""
        location = Location(name="東京", normalized_name="東京")
        
        # 初回呼び出し（キャッシュミス）
        assert location._levenshtein_distance("東京", "東大") == 1
        
        # 同じ引数で再度呼び出し（キャッシュヒット）
        assert location._levenshtein_distance("東京", "東大") == 1
        
        # キャッシュ情報を確認
        cache_info = get_levenshtein_cache_info()
        assert cache_info["hits"] == 1
        assert cache_info["misses"] == 1
        assert cache_info["hit_rate"] == 0.5
    
    def test_cache_performance(self):
        """キャッシュによるパフォーマンス向上のテスト"""
        location = Location(name="東京", normalized_name="東京")
        
        # キャッシュなしの場合の時間を計測（最初の呼び出し）
        start_time = time.time()
        for _ in range(100):
            location._levenshtein_distance("東京都千代田区", "東京都中央区")
        no_cache_time = time.time() - start_time
        
        # キャッシュありの場合の時間を計測（同じ文字列を繰り返し）
        start_time = time.time()
        for _ in range(1000):  # 10倍の回数
            location._levenshtein_distance("東京都千代田区", "東京都中央区")
        cache_time = time.time() - start_time
        
        # キャッシュありの方が高速であることを確認
        # 10倍の回数でも時間が短いはず
        assert cache_time < no_cache_time * 5
        
        cache_info = get_levenshtein_cache_info()
        assert cache_info["hits"] >= 1000  # 少なくとも1000回はヒット
    
    def test_cache_with_fuzzy_search(self):
        """あいまい検索でのキャッシュ効果テスト"""
        locations = [
            Location(name="東京", normalized_name="東京"),
            Location(name="大阪", normalized_name="大阪"),
            Location(name="名古屋", normalized_name="名古屋"),
            Location(name="札幌", normalized_name="札幌"),
            Location(name="福岡", normalized_name="福岡"),
        ]
        
        # 複数回の検索でキャッシュが効いているか確認
        queries = ["東大", "大坂", "名古屋市", "札幌市", "福岡県"]
        
        # 初回検索
        for query in queries:
            for location in locations:
                location.matches_query(query, fuzzy=True)
        
        initial_cache_info = get_levenshtein_cache_info()
        initial_misses = initial_cache_info["misses"]
        
        # 2回目の検索（同じクエリ）
        for query in queries:
            for location in locations:
                location.matches_query(query, fuzzy=True)
        
        final_cache_info = get_levenshtein_cache_info()
        
        # 2回目はキャッシュヒットが増えているはず
        assert final_cache_info["hits"] > initial_cache_info["hits"]
        # ミス数は変わらないはず
        assert final_cache_info["misses"] == initial_misses
    
    def test_cache_size_limit(self):
        """キャッシュサイズ上限のテスト"""
        location = Location(name="test", normalized_name="test")
        
        # 多数の異なる文字列ペアで計算
        for i in range(5000):  # maxsize=4096を超える数
            s1 = f"string_{i}"
            s2 = f"text_{i}"
            location._levenshtein_distance(s1, s2)
        
        cache_info = get_levenshtein_cache_info()
        # キャッシュサイズが上限を超えないことを確認
        assert cache_info["currsize"] <= cache_info["maxsize"]
        assert cache_info["maxsize"] == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])