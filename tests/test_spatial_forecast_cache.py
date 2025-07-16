"""
Test module for SpatialForecastCache

空間予報キャッシュのテスト
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.data.forecast_cache.spatial_cache import SpatialForecastCache, LocationCoordinate
from src.data.forecast_cache.models import ForecastCacheEntry

JST = ZoneInfo("Asia/Tokyo")


class TestLocationCoordinate:
    """LocationCoordinateのテストクラス"""
    
    def test_distance_calculation(self):
        """距離計算のテスト"""
        # 東京駅
        tokyo = LocationCoordinate("東京", 35.6812, 139.7671)
        # 横浜駅（約27km）
        yokohama = LocationCoordinate("横浜", 35.4657, 139.6224)
        
        distance = tokyo.distance_to(yokohama)
        
        # 約27km（誤差1km以内）
        assert 26 < distance < 28
    
    def test_same_location_distance(self):
        """同一地点の距離は0"""
        tokyo = LocationCoordinate("東京", 35.6812, 139.7671)
        distance = tokyo.distance_to(tokyo)
        assert distance < 0.001  # ほぼ0


class TestSpatialForecastCache:
    """SpatialForecastCacheのテストクラス"""
    
    @pytest.fixture
    def cache(self):
        """テスト用のキャッシュインスタンス"""
        return SpatialForecastCache(max_distance_km=10.0, max_neighbors=3)
    
    @pytest.fixture
    def sample_entry(self):
        """サンプルのキャッシュエントリ"""
        def create_entry(location_name):
            return ForecastCacheEntry(
                location_name=location_name,
                forecast_datetime=datetime.now(JST),
                cached_at=datetime.now(JST),
                temperature=25.5,
                weather_condition="晴れ",
                precipitation=0.0
            )
        return create_entry
    
    def setup_tokyo_area_locations(self, cache):
        """東京近郊の地点を登録"""
        # 東京駅を中心とした地点
        locations = [
            ("東京", 35.6812, 139.7671),
            ("品川", 35.6284, 139.7387),  # 約6.7km
            ("新宿", 35.6896, 139.6922),  # 約6.0km
            ("渋谷", 35.6580, 139.7016),  # 約3.4km
            ("横浜", 35.4657, 139.6224),  # 約27km（範囲外）
        ]
        
        for name, lat, lon in locations:
            cache.register_location(name, lat, lon)
        
        return locations
    
    def test_register_location(self, cache):
        """位置登録のテスト"""
        cache.register_location("東京", 35.6812, 139.7671)
        
        assert "東京" in cache._location_coords
        coord = cache._location_coords["東京"]
        assert coord.latitude == 35.6812
        assert coord.longitude == 139.7671
    
    def test_direct_cache_hit(self, cache, sample_entry):
        """直接キャッシュヒットのテスト"""
        cache.register_location("東京", 35.6812, 139.7671)
        
        target_time = datetime.now(JST)
        entry = sample_entry("東京")
        
        # キャッシュに追加
        cache.put("東京", target_time, entry)
        
        # 直接取得
        result = cache.get("東京", target_time)
        
        assert result is not None
        assert result.location_name == "東京"
        
        # 統計確認
        stats = cache.get_stats()
        assert stats["direct_hits"] == 1
        assert stats["neighbor_hits"] == 0
    
    def test_neighbor_cache_hit(self, cache, sample_entry):
        """近隣キャッシュヒットのテスト"""
        self.setup_tokyo_area_locations(cache)
        
        target_time = datetime.now(JST)
        
        # 品川のデータをキャッシュ
        entry = sample_entry("品川")
        cache.put("品川", target_time, entry)
        
        # 東京で検索（品川のデータが使われるはず）
        result = cache.get("東京", target_time)
        
        assert result is not None
        assert result.location_name == "東京"  # 地点名は要求された東京に変更される
        assert result.temperature == 25.5  # データは品川のもの
        
        # 統計確認
        stats = cache.get_stats()
        assert stats["direct_hits"] == 0
        assert stats["neighbor_hits"] == 1
    
    def test_max_distance_limit(self, cache, sample_entry):
        """最大距離制限のテスト"""
        self.setup_tokyo_area_locations(cache)
        
        target_time = datetime.now(JST)
        
        # 横浜のデータをキャッシュ（東京から27km）
        entry = sample_entry("横浜")
        cache.put("横浜", target_time, entry)
        
        # 東京で検索（10km以内に該当なし）
        result = cache.get("東京", target_time)
        
        assert result is None
        
        # 統計確認
        stats = cache.get_stats()
        assert stats["misses"] == 1
    
    def test_max_neighbors_limit(self, cache, sample_entry):
        """最大近隣数制限のテスト"""
        cache.max_neighbors = 2  # 最大2つに制限
        self.setup_tokyo_area_locations(cache)
        
        # 近隣地点のリストを取得
        tokyo_coord = cache._location_coords["東京"]
        neighbors = cache._find_nearest_neighbors(tokyo_coord)
        
        # 最大2つまでしか返さない
        assert len(neighbors) <= 2
        
        # 距離順になっていることを確認
        if len(neighbors) >= 2:
            assert neighbors[0][1] <= neighbors[1][1]
    
    def test_tolerance_hours(self, cache, sample_entry):
        """時間許容差のテスト"""
        cache.register_location("東京", 35.6812, 139.7671)
        
        base_time = datetime.now(JST)
        entry = sample_entry("東京")
        
        # 基準時刻でキャッシュ
        cache.put("東京", base_time, entry)
        
        # 2時間後でも取得可能（tolerance_hours=3）
        result = cache.get("東京", base_time + timedelta(hours=2), tolerance_hours=3)
        assert result is not None
        
        # 4時間後は取得不可
        result = cache.get("東京", base_time + timedelta(hours=4), tolerance_hours=3)
        assert result is None
    
    def test_clear(self, cache, sample_entry):
        """キャッシュクリアのテスト"""
        self.setup_tokyo_area_locations(cache)
        
        # データを追加
        for location in ["東京", "品川", "新宿"]:
            entry = sample_entry(location)
            cache.put(location, datetime.now(JST), entry)
        
        # クリア前
        stats_before = cache.get_stats()
        assert stats_before["cached_locations"] == 3
        
        # クリア
        cache.clear()
        
        # クリア後
        stats_after = cache.get_stats()
        assert stats_after["cached_locations"] == 0
        assert stats_after["total_requests"] == 0
        
        # 位置情報は残っている
        assert len(cache._location_coords) == 5
    
    def test_statistics(self, cache, sample_entry):
        """統計情報のテスト"""
        self.setup_tokyo_area_locations(cache)
        
        target_time = datetime.now(JST)
        
        # データ追加
        cache.put("品川", target_time, sample_entry("品川"))
        cache.put("新宿", target_time, sample_entry("新宿"))
        
        # アクセステスト
        cache.get("品川", target_time)  # 直接ヒット
        cache.get("東京", target_time)  # 近隣ヒット（品川or新宿）
        cache.get("横浜", target_time)  # ミス
        
        stats = cache.get_stats()
        
        assert stats["total_requests"] == 3
        assert stats["direct_hits"] == 1
        assert stats["neighbor_hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2/3
        assert stats["total_locations"] == 5
        assert stats["cached_locations"] == 2
    
    def test_concurrent_access(self, cache, sample_entry):
        """並行アクセスのテスト"""
        import threading
        
        self.setup_tokyo_area_locations(cache)
        errors = []
        
        def access_cache(location):
            try:
                target_time = datetime.now(JST)
                entry = sample_entry(location)
                cache.put(location, target_time, entry)
                result = cache.get(location, target_time)
                assert result is not None
            except Exception as e:
                errors.append(e)
        
        # 複数スレッドで同時アクセス
        threads = []
        for location in ["東京", "品川", "新宿", "渋谷"]:
            t = threading.Thread(target=access_cache, args=(location,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # エラーがないことを確認
        assert len(errors) == 0