"""LocationSearchEngineのパフォーマンステスト"""

import pytest
import time

from src.data.location.models import Location
from src.data.location.search_engine import LocationSearchEngine


class TestLocationSearchEnginePerformance:
    """LocationSearchEngineのパフォーマンステスト"""
    
    @pytest.fixture
    def large_location_dataset(self) -> list[Location]:
        """大規模な地点データセットを生成"""
        locations = []
        prefectures = ["東京", "大阪", "愛知", "北海道", "福岡", "神奈川", "埼玉", "千葉"]
        
        # 1000件のテストデータを生成
        for i in range(1000):
            prefecture = prefectures[i % len(prefectures)]
            location = Location(
                name=f"テスト地点{i:04d}",
                normalized_name=f"テスト地点{i:04d}",
                prefecture=prefecture,
                latitude=35.0 + (i % 10) * 0.1,
                longitude=135.0 + (i % 10) * 0.1,
                region=self._get_region_for_prefecture(prefecture),
                location_type="市",
                population=10000 + i * 100
            )
            locations.append(location)
        
        return locations
    
    def _get_region_for_prefecture(self, prefecture: str) -> str:
        """都道府県から地方を取得"""
        region_map = {
            "東京": "関東",
            "大阪": "近畿",
            "愛知": "中部",
            "北海道": "北海道・東北",
            "福岡": "九州",
            "神奈川": "関東",
            "埼玉": "関東",
            "千葉": "関東"
        }
        return region_map.get(prefecture, "その他")
    
    def test_index_build_performance(self, large_location_dataset):
        """インデックス構築のパフォーマンステスト"""
        start_time = time.time()
        
        engine = LocationSearchEngine(large_location_dataset)
        
        build_time = time.time() - start_time
        
        # 1000件のデータで1秒以内にインデックス構築完了
        assert build_time < 1.0, f"インデックス構築に{build_time:.3f}秒かかりました"
        
        # インデックスが正しく構築されているか確認
        stats = engine.get_statistics()
        assert stats["total_locations"] == 1000
        assert stats["indexed_names"] == 1000
    
    def test_exact_match_search_performance(self, large_location_dataset):
        """完全一致検索のパフォーマンステスト"""
        engine = LocationSearchEngine(large_location_dataset)
        
        # ウォームアップ
        for i in range(10):
            engine.get_location(f"テスト地点{i:04d}")
        
        # 100回の検索時間を計測
        start_time = time.time()
        for i in range(100):
            result = engine.get_location(f"テスト地点{i:04d}")
            assert result is not None
            assert result.name == f"テスト地点{i:04d}"
        
        search_time = time.time() - start_time
        avg_time = search_time / 100
        
        # 平均検索時間が1ミリ秒以内
        assert avg_time < 0.001, f"平均検索時間: {avg_time*1000:.3f}ms"
    
    def test_prefix_search_performance(self, large_location_dataset):
        """前方一致検索のパフォーマンステスト"""
        engine = LocationSearchEngine(large_location_dataset)
        
        test_prefixes = ["テスト", "テスト地", "テスト地点0", "テスト地点00"]
        
        for prefix in test_prefixes:
            start_time = time.time()
            
            # プレフィックスインデックスから検索
            results = list(engine.prefix_index.get(prefix.lower(), []))
            
            search_time = time.time() - start_time
            
            # プレフィックス検索は10ミリ秒以内
            assert search_time < 0.01, f"プレフィックス '{prefix}' の検索に{search_time*1000:.3f}ms"
            assert len(results) > 0
    
    def test_region_filter_performance(self, large_location_dataset):
        """地方フィルタリングのパフォーマンステスト"""
        engine = LocationSearchEngine(large_location_dataset)
        
        regions = ["関東", "近畿", "中部", "北海道・東北", "九州"]
        
        for region in regions:
            start_time = time.time()
            
            results = engine.get_locations_by_region(region)
            
            filter_time = time.time() - start_time
            
            # 地方フィルタリングは1ミリ秒以内
            assert filter_time < 0.001, f"地方 '{region}' のフィルタリングに{filter_time*1000:.3f}ms"
            assert len(results) > 0
    
    def test_nearby_locations_performance(self, large_location_dataset):
        """近隣地点検索のパフォーマンステスト"""
        engine = LocationSearchEngine(large_location_dataset)
        
        # 基準地点
        base_location = large_location_dataset[500]
        
        # 異なる半径での検索
        radii = [10.0, 50.0, 100.0]
        
        for radius in radii:
            start_time = time.time()
            
            nearby = engine.get_nearby_locations(base_location, radius_km=radius, limit=20)
            
            search_time = time.time() - start_time
            
            # 1000件のデータセットで100ミリ秒以内
            assert search_time < 0.1, f"半径{radius}kmの検索に{search_time*1000:.3f}ms"
            assert isinstance(nearby, list)
    
    def test_fuzzy_search_performance(self, large_location_dataset):
        """曖昧検索のパフォーマンステスト"""
        engine = LocationSearchEngine(large_location_dataset)
        
        # タイポを含むクエリ
        test_queries = [
            ("テスト地点0001", "テスト地点0002"),  # 1文字違い
            ("テスト地点0100", "テスト地点0200"),  # 1文字違い
            ("テスト", "テスと"),  # ひらがな混在
        ]
        
        for correct, typo in test_queries:
            start_time = time.time()
            
            results = engine.search_locations(typo, fuzzy=True, limit=10)
            
            search_time = time.time() - start_time
            
            # 曖昧検索は50ミリ秒以内
            assert search_time < 0.05, f"曖昧検索 '{typo}' に{search_time*1000:.3f}ms"
            assert len(results) > 0
    
    def test_concurrent_search_simulation(self, large_location_dataset):
        """並行検索のシミュレーション"""
        engine = LocationSearchEngine(large_location_dataset)
        
        # 100回の異なる検索を連続実行
        start_time = time.time()
        
        for i in range(100):
            # 様々な検索パターンを実行
            if i % 4 == 0:
                # 完全一致検索
                engine.get_location(f"テスト地点{i:04d}")
            elif i % 4 == 1:
                # 地方検索
                engine.get_locations_by_region("関東")
            elif i % 4 == 2:
                # 都道府県検索
                engine.get_locations_by_prefecture("東京")
            else:
                # 一般検索
                engine.search_locations("テスト", limit=10)
        
        total_time = time.time() - start_time
        
        # 100回の検索が1秒以内
        assert total_time < 1.0, f"100回の検索に{total_time:.3f}秒"
        
        # 平均レスポンスタイム
        avg_response = total_time / 100
        assert avg_response < 0.01, f"平均レスポンス: {avg_response*1000:.3f}ms"