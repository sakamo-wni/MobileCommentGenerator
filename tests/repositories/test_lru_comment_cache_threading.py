"""LRUCommentCacheのスレッドセーフティテスト"""

import pytest
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.repositories.lru_comment_cache import LRUCommentCache
from src.data.past_comment import PastComment, CommentType


class TestLRUCommentCacheThreadSafety:
    """LRUCommentCacheのスレッドセーフティテストクラス"""
    
    @pytest.fixture
    def cache(self):
        """テスト用のキャッシュインスタンス"""
        return LRUCommentCache(max_size=100, cache_ttl_minutes=60, max_memory_mb=10)
    
    @pytest.fixture
    def sample_comment(self):
        """テスト用のサンプルコメント"""
        return PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="テストコメント",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"test": True}
        )
    
    def test_concurrent_get_set(self, cache, sample_comment):
        """並行なget/set操作のテスト"""
        num_threads = 10
        num_operations = 100
        
        def worker(thread_id):
            results = []
            for i in range(num_operations):
                key = f"key_{thread_id}_{i % 5}"  # 5つのキーを使い回す
                
                # set操作
                cache.set(key, [sample_comment])
                
                # get操作
                result = cache.get(key)
                results.append(result is not None)
                
            return results
        
        # 複数スレッドで実行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            # 全スレッドの完了を待つ
            for future in as_completed(futures):
                results = future.result()
                # 各スレッドが正常に動作したことを確認
                assert any(results), "At least some operations should succeed"
        
        # 統計情報が正しく更新されていることを確認
        stats = cache.get_stats()
        assert stats['total_requests'] > 0
        assert stats['hits'] > 0
    
    def test_concurrent_eviction(self, cache, sample_comment):
        """並行なエビクション処理のテスト"""
        # キャッシュサイズを小さく設定
        small_cache = LRUCommentCache(max_size=10, cache_ttl_minutes=60)
        
        def add_entries(start_idx):
            for i in range(20):  # max_sizeより多く追加
                key = f"key_{start_idx}_{i}"
                small_cache.set(key, [sample_comment])
                time.sleep(0.001)  # 少し待機してタイミングをずらす
        
        # 複数スレッドで同時にエントリを追加
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_entries, args=(i * 100,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待つ
        for thread in threads:
            thread.join()
        
        # キャッシュサイズが制限内に収まっていることを確認
        stats = small_cache.get_stats()
        assert stats['size'] <= 10
    
    def test_concurrent_stats_access(self, cache, sample_comment):
        """統計情報への並行アクセステスト"""
        # 初期データを追加
        for i in range(10):
            cache.set(f"key_{i}", [sample_comment])
        
        def read_stats():
            stats_list = []
            for _ in range(50):
                stats = cache.get_stats()
                stats_list.append(stats)
                # 統計情報の整合性を確認
                assert stats['hits'] >= 0
                assert stats['misses'] >= 0
                assert stats['total_requests'] == stats['hits'] + stats['misses']
            return stats_list
        
        def modify_cache():
            for i in range(50):
                if i % 2 == 0:
                    cache.set(f"new_key_{i}", [sample_comment])
                else:
                    cache.get(f"key_{i % 10}")
        
        # 読み取りと書き込みを並行実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            # 2つの読み取りスレッドと2つの書き込みスレッド
            futures = []
            futures.extend([executor.submit(read_stats) for _ in range(2)])
            futures.extend([executor.submit(modify_cache) for _ in range(2)])
            
            # 全タスクの完了を確認
            for future in as_completed(futures):
                future.result()
    
    def test_concurrent_cleanup(self, cache, sample_comment):
        """クリーンアップ処理の並行実行テスト"""
        # 期限切れになるエントリを追加
        for i in range(20):
            cache.set(f"key_{i}", [sample_comment])
        
        # 期限を手動で過去に設定（テスト用）
        with cache._lock:
            for i in range(10):
                key = f"key_{i}"
                if key in cache._cache:
                    comments, _ = cache._cache[key]
                    expired_time = datetime.now().replace(year=2020)
                    cache._cache[key] = (comments, expired_time)
        
        def cleanup_worker():
            return cache.cleanup_expired()
        
        def access_worker():
            results = []
            for i in range(30):
                result = cache.get(f"key_{i % 20}")
                results.append(result)
            return results
        
        # クリーンアップと通常アクセスを並行実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            # クリーンアップを実行
            futures.append(executor.submit(cleanup_worker))
            # 通常のアクセスを実行
            futures.extend([executor.submit(access_worker) for _ in range(3)])
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # クリーンアップが正常に実行されたことを確認
        cleanup_count = [r for r in results if isinstance(r, int)][0]
        assert cleanup_count >= 0  # 正常に実行された
    
    def test_race_condition_move_to_end(self, cache, sample_comment):
        """move_to_end操作の競合状態テスト"""
        # 共通のキーを準備
        common_keys = [f"common_{i}" for i in range(5)]
        for key in common_keys:
            cache.set(key, [sample_comment])
        
        def access_keys():
            for _ in range(100):
                for key in common_keys:
                    cache.get(key)  # LRU順序を更新
        
        # 複数スレッドで同じキーに同時アクセス
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_keys)
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待つ
        for thread in threads:
            thread.join()
        
        # エラーなく完了し、データ整合性が保たれていることを確認
        stats = cache.get_stats()
        assert stats['size'] == len(common_keys)
        assert stats['hits'] > 0