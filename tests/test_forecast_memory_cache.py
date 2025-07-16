"""
Test module for ForecastMemoryCache

予報メモリキャッシュのテスト
"""

import pytest
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.data.forecast_cache.memory_cache import ForecastMemoryCache
from src.data.forecast_cache.models import ForecastCacheEntry

JST = ZoneInfo("Asia/Tokyo")


class TestForecastMemoryCache:
    """ForecastMemoryCacheのテストクラス"""
    
    @pytest.fixture
    def cache(self):
        """テスト用のキャッシュインスタンス"""
        return ForecastMemoryCache(max_size=3, ttl_seconds=2)
    
    @pytest.fixture
    def sample_entry(self):
        """サンプルのキャッシュエントリ"""
        return ForecastCacheEntry(
            location_name="東京",
            forecast_datetime=datetime.now(JST),
            cached_at=datetime.now(JST),
            temperature=25.5,
            max_temperature=28.0,
            min_temperature=22.0,
            weather_condition="晴れ",
            weather_description="快晴",
            precipitation=0.0,
            humidity=60,
            wind_speed=3.5,
            metadata={"source": "test"}
        )
    
    def test_put_and_get(self, cache, sample_entry):
        """put/get操作の基本テスト"""
        location = "東京"
        target_time = datetime.now(JST)
        
        # キャッシュに追加
        cache.put(location, target_time, sample_entry)
        
        # 取得
        retrieved = cache.get(location, target_time)
        
        assert retrieved is not None
        assert retrieved.location_name == "東京"
        assert retrieved.temperature == 25.5
    
    def test_lru_eviction(self, cache, sample_entry):
        """LRU方式でのエビクションテスト"""
        # max_size=3なので、4つ目を追加すると最も古いものが削除される
        locations = ["東京", "大阪", "名古屋", "福岡"]
        base_time = datetime.now(JST)
        
        for i, location in enumerate(locations):
            entry = ForecastCacheEntry(
                location_name=location,
                forecast_datetime=base_time + timedelta(hours=i),
                cached_at=datetime.now(JST),
                temperature=20.0 + i
            )
            cache.put(location, base_time + timedelta(hours=i), entry)
            time.sleep(0.01)  # 順序を保証
        
        # 東京（最初に追加）は削除されているはず
        assert cache.get("東京", base_time) is None
        
        # 他の3つは残っているはず
        assert cache.get("大阪", base_time + timedelta(hours=1)) is not None
        assert cache.get("名古屋", base_time + timedelta(hours=2)) is not None
        assert cache.get("福岡", base_time + timedelta(hours=3)) is not None
    
    def test_ttl_expiration(self, cache, sample_entry):
        """TTL期限切れのテスト"""
        location = "東京"
        target_time = datetime.now(JST)
        
        # キャッシュに追加（TTL=2秒）
        cache.put(location, target_time, sample_entry)
        
        # 直後は取得可能
        assert cache.get(location, target_time) is not None
        
        # 3秒待つ
        time.sleep(3)
        
        # TTLが切れているため取得不可
        assert cache.get(location, target_time) is None
    
    def test_tolerance_matching(self, cache, sample_entry):
        """許容時間差でのマッチングテスト"""
        location = "東京"
        base_time = datetime.now(JST)
        
        # 基準時刻でキャッシュ
        cache.put(location, base_time, sample_entry)
        
        # 2時間の差でも取得可能（tolerance_hours=3）
        result = cache.get(location, base_time + timedelta(hours=2), tolerance_hours=3)
        assert result is not None
        
        # 4時間の差では取得不可
        result = cache.get(location, base_time + timedelta(hours=4), tolerance_hours=3)
        assert result is None
    
    def test_clear(self, cache, sample_entry):
        """キャッシュクリアのテスト"""
        # データを追加
        cache.put("東京", datetime.now(JST), sample_entry)
        cache.put("大阪", datetime.now(JST), sample_entry)
        
        # クリア前は取得可能
        assert len(cache._cache) == 2
        
        # クリア
        cache.clear()
        
        # クリア後は空
        assert len(cache._cache) == 0
        assert cache.get("東京", datetime.now(JST)) is None
    
    def test_get_stats(self, cache, sample_entry):
        """統計情報取得のテスト"""
        # 初期状態
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        
        # データ追加とアクセス
        cache.put("東京", datetime.now(JST), sample_entry)
        
        # ヒット
        cache.get("東京", datetime.now(JST))
        
        # ミス
        cache.get("大阪", datetime.now(JST))
        
        # 統計確認
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5
    
    def test_concurrent_access(self, cache, sample_entry):
        """並行アクセスのテスト"""
        import threading
        
        results = []
        errors = []
        
        def add_and_get(location, index):
            try:
                # 追加
                entry = ForecastCacheEntry(
                    location_name=location,
                    forecast_datetime=datetime.now(JST),
                    temperature=20.0 + index
                )
                cache.put(location, datetime.now(JST), entry)
                
                # 取得
                result = cache.get(location, datetime.now(JST))
                results.append(result is not None)
            except Exception as e:
                errors.append(e)
        
        # 10スレッドで同時アクセス
        threads = []
        for i in range(10):
            t = threading.Thread(
                target=add_and_get,
                args=(f"地点{i}", i)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # エラーがないことを確認
        assert len(errors) == 0
        # 結果が正しく取得されていることを確認
        assert all(results)
    
    def test_memory_estimation(self, cache, sample_entry):
        """メモリ使用量推定のテスト"""
        # 複数エントリを追加
        for i in range(3):
            cache.put(
                f"地点{i}",
                datetime.now(JST) + timedelta(hours=i),
                sample_entry
            )
        
        stats = cache.get_stats()
        assert stats["size"] == 3
        assert stats["max_size"] == 3
        
        # メモリ使用量が計算されていることを確認
        assert "estimated_memory_mb" in stats
        assert stats["estimated_memory_mb"] > 0