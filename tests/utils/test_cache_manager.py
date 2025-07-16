"""
キャッシュマネージャーのテスト
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.utils.cache_manager import (
    CacheManager, CacheConfig, get_cache_manager, get_cache
)
from src.utils.cache import TTLCache


class TestCacheManager:
    """CacheManagerのテストクラス"""
    
    @pytest.fixture
    def cache_manager(self):
        """テスト用のキャッシュマネージャー"""
        # 新しいインスタンスを強制的に作成
        CacheManager._instance = None
        manager = CacheManager()
        yield manager
        # クリーンアップ
        manager.shutdown()
        CacheManager._instance = None
    
    @pytest.fixture
    def temp_stats_file(self):
        """一時的な統計ファイル"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # クリーンアップ
        if temp_path.exists():
            temp_path.unlink()
    
    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2
    
    def test_create_cache(self, cache_manager):
        """キャッシュ作成のテスト"""
        config = CacheConfig(
            default_ttl_seconds=100,
            max_size=50,
            max_memory_mb=10
        )
        
        cache = cache_manager.create_cache("test_cache", config)
        
        assert isinstance(cache, TTLCache)
        assert "test_cache" in cache_manager._caches
        assert cache_manager._configs["test_cache"] == config
    
    def test_get_cache_existing(self, cache_manager):
        """既存キャッシュ取得のテスト"""
        cache_manager.create_cache("existing_cache")
        cache = cache_manager.get_cache("existing_cache")
        
        assert cache is cache_manager._caches["existing_cache"]
    
    def test_get_cache_non_existing(self, cache_manager):
        """存在しないキャッシュ取得のテスト"""
        cache = cache_manager.get_cache("non_existing_cache")
        
        assert "non_existing_cache" in cache_manager._caches
        assert isinstance(cache, TTLCache)
    
    def test_cache_operations(self, cache_manager):
        """キャッシュ操作のテスト"""
        cache = cache_manager.get_cache("test_cache")
        
        # データの設定と取得
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 統計情報の確認
        stats = cache_manager.get_all_stats()["test_cache"]
        assert stats.basic_stats.hits == 1
        assert stats.basic_stats.size == 1
    
    def test_warm_cache(self, cache_manager):
        """キャッシュウォーミングのテスト"""
        test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        cache_manager.warm_cache("warmed_cache", test_data)
        
        cache = cache_manager.get_cache("warmed_cache")
        for key, value in test_data.items():
            assert cache.get(key) == value
    
    def test_clear_all_caches(self, cache_manager):
        """全キャッシュクリアのテスト"""
        # 複数のキャッシュにデータを設定
        cache1 = cache_manager.get_cache("cache1")
        cache2 = cache_manager.get_cache("cache2")
        
        cache1.set("key", "value")
        cache2.set("key", "value")
        
        # 全キャッシュをクリア
        cache_manager.clear_all_caches()
        
        assert cache1.get("key") is None
        assert cache2.get("key") is None
    
    def test_stats_calculation(self, cache_manager):
        """統計情報計算のテスト"""
        cache = cache_manager.get_cache("stats_test")
        
        # データ操作
        cache.set("key1", "value1")
        cache.get("key1")  # ヒット
        cache.get("key2")  # ミス
        
        stats = cache_manager.get_all_stats()["stats_test"]
        
        assert stats.basic_stats.hits == 1
        assert stats.basic_stats.misses == 1
        assert stats.basic_stats.hit_rate == 0.5
        assert stats.cache_efficiency_score > 0
    
    def test_stats_summary(self, cache_manager):
        """統計サマリーのテスト"""
        # 複数のキャッシュを作成
        cache1 = cache_manager.get_cache("cache1")
        cache2 = cache_manager.get_cache("cache2")
        
        cache1.set("key", "value")
        cache2.set("key", "value")
        
        summary = cache_manager.get_stats_summary()
        
        assert summary["total_caches"] >= 2
        assert "total_memory_usage_mb" in summary
        assert "overall_hit_rate" in summary
        assert "cache_details" in summary
    
    @patch('src.utils.cache_manager.HAS_PSUTIL', True)
    @patch('src.utils.cache_manager.psutil.virtual_memory')
    def test_memory_pressure_handling(self, mock_memory, cache_manager):
        """メモリプレッシャー処理のテスト"""
        # 高メモリ使用率をシミュレート
        mock_memory.return_value = MagicMock(percent=85.0)
        
        cache = cache_manager.get_cache("pressure_test")
        
        # データを追加
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        initial_size = cache.get_stats().size
        
        # メモリプレッシャー処理を実行
        cache_manager._handle_memory_pressure()
        
        # サイズが減少していることを確認
        final_size = cache.get_stats().size
        assert final_size < initial_size
    
    def test_stats_file_saving(self, cache_manager, temp_stats_file):
        """統計ファイル保存のテスト"""
        # 統計ファイルパスを設定
        cache_manager._global_config.stats_file_path = temp_stats_file
        cache_manager._global_config.enable_stats_tracking = True
        
        # キャッシュ操作
        cache = cache_manager.get_cache("save_test")
        cache.set("key", "value")
        
        # 統計を保存
        cache_manager._save_stats()
        
        # ファイルが作成されていることを確認
        assert temp_stats_file.exists()
        
        # 内容を確認
        with open(temp_stats_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) > 0
        assert "timestamp" in data[0]
        assert "total_caches" in data[0]
    
    def test_concurrent_access(self, cache_manager):
        """並行アクセスのテスト"""
        cache = cache_manager.get_cache("concurrent_test")
        results = []
        
        def worker(thread_id):
            for i in range(100):
                cache.set(f"thread{thread_id}_key{i}", f"value{i}")
                value = cache.get(f"thread{thread_id}_key{i}")
                results.append(value == f"value{i}")
        
        # 複数スレッドで実行
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # すべての操作が成功していることを確認
        assert all(results)
    
    def test_default_caches_creation(self):
        """デフォルトキャッシュの作成テスト"""
        manager = CacheManager()
        
        # デフォルトキャッシュが作成されていることを確認
        assert "api_responses" in manager._caches
        assert "comments" in manager._caches
        assert "weather_forecasts" in manager._caches
        
        # 設定が正しいことを確認
        api_config = manager._configs["api_responses"]
        assert api_config.default_ttl_seconds == 300
        assert api_config.max_size == 500
    
    def test_cache_efficiency_score(self, cache_manager):
        """キャッシュ効率スコアのテスト"""
        cache = cache_manager.get_cache("efficiency_test")
        
        # 高ヒット率のシナリオ
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # 多くのヒットを生成
        for _ in range(50):
            for i in range(10):
                cache.get(f"key{i}")
        
        stats = cache_manager.get_all_stats()["efficiency_test"]
        
        # 高い効率スコアを期待
        assert stats.cache_efficiency_score > 0.5
        assert stats.cache_efficiency_score <= 1.0
    
    def test_shutdown(self, cache_manager):
        """シャットダウン処理のテスト"""
        # キャッシュを作成
        cache = cache_manager.get_cache("shutdown_test")
        cache.set("key", "value")
        
        # シャットダウン
        cache_manager.shutdown()
        
        # メモリ監視スレッドが停止していることを確認
        assert cache_manager._stop_monitoring.is_set()


class TestCacheDecorators:
    """キャッシュデコレーターのテスト"""
    
    @pytest.fixture(autouse=True)
    def setup_cache_manager(self):
        """各テストの前にキャッシュマネージャーをリセット"""
        CacheManager._instance = None
        yield
        if CacheManager._instance:
            CacheManager._instance.shutdown()
        CacheManager._instance = None
    
    def test_smart_cache_sync(self):
        """同期関数のスマートキャッシュテスト"""
        from src.utils.cache_decorators import smart_cache
        
        call_count = 0
        
        @smart_cache(cache_name="test_sync", ttl=60)
        def test_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 最初の呼び出し
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 2回目の呼び出し（キャッシュから）
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # 関数は呼ばれない
        
        # 異なる引数での呼び出し
        result3 = test_function(10)
        assert result3 == 20
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_smart_cache_async(self):
        """非同期関数のスマートキャッシュテスト"""
        from src.utils.cache_decorators import smart_cache
        
        call_count = 0
        
        @smart_cache(cache_name="test_async", ttl=60)
        async def test_async_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 最初の呼び出し
        result1 = await test_async_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 2回目の呼び出し（キャッシュから）
        result2 = await test_async_function(5)
        assert result2 == 10
        assert call_count == 1
    
    def test_cache_condition(self):
        """条件付きキャッシュのテスト"""
        from src.utils.cache_decorators import smart_cache
        
        @smart_cache(
            cache_name="test_condition",
            condition=lambda result: result > 0
        )
        def test_function(x: int) -> int:
            return x
        
        # 正の値はキャッシュされる
        result1 = test_function(5)
        result2 = test_function(5)
        
        cache = get_cache("test_condition")
        stats = cache.get_stats()
        assert stats.hits == 1
        
        # 負の値はキャッシュされない
        result3 = test_function(-5)
        result4 = test_function(-5)
        
        stats = cache.get_stats()
        assert stats.hits == 1  # ヒット数は増えない
    
    def test_cache_bypass(self):
        """キャッシュバイパスのテスト"""
        from src.utils.cache_decorators import smart_cache
        
        call_count = 0
        
        @smart_cache(cache_name="test_bypass")
        def test_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 通常の呼び出し
        result1 = test_function(5)
        assert call_count == 1
        
        # キャッシュから
        result2 = test_function(5)
        assert call_count == 1
        
        # バイパスあり
        result3 = test_function(5, _bypass_cache=True)
        assert call_count == 2
        assert result3 == 10