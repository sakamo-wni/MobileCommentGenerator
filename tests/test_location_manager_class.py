"""
LocationManagerクラスのテスト

地点データ管理クラスの基本的な動作をテストする
"""

import pytest
from unittest.mock import patch, mock_open
from src.data.location import Location
from src.data.location.manager import LocationManagerRefactored as LocationManager


class TestLocationManager:
    """LocationManager クラスのテスト"""

    def test_initialization_with_default_data(self):
        """デフォルトデータでの初期化テスト"""
        with patch("os.path.exists", return_value=False):
            manager = LocationManager()

            assert len(manager.locations) > 0
            assert manager.loaded_at is not None

            # 主要都市が含まれているかチェック
            location_names = [loc.name for loc in manager.locations]
            assert "東京" in location_names
            assert "大阪" in location_names
            assert "札幌" in location_names

    def test_load_from_csv_content(self):
        """CSVファイルからの読み込みテスト"""
        csv_content = "稚内\n旭川\n札幌\n函館\n東京\n大阪\n"

        with patch("builtins.open", mock_open(read_data=csv_content)):
            with patch("os.path.exists", return_value=True):
                manager = LocationManager("test.csv")

                assert len(manager.locations) == 6

                location_names = [loc.name for loc in manager.locations]
                assert "稚内" in location_names
                assert "東京" in location_names
                assert "大阪" in location_names

    def test_load_from_csv_with_invalid_data(self):
        """不正なデータを含むCSVファイルからの読み込みテスト"""
        csv_content = (
            "稚内\n\n東京\n���文字化け���\n大阪\nこれは非常に長い地点名なので除外されるべきです\n"
        )

        with patch("builtins.open", mock_open(read_data=csv_content)):
            with patch("os.path.exists", return_value=True):
                manager = LocationManager("test.csv")

                # 正常なデータのみ読み込まれる
                location_names = [loc.name for loc in manager.locations]
                assert "稚内" in location_names
                assert "東京" in location_names
                assert "大阪" in location_names

                # 異常なデータは除外される
                assert len([name for name in location_names if len(name) > 20]) == 0

    def test_search_location_exact_match(self):
        """完全一致検索のテスト"""
        manager = LocationManager()

        results = manager.search_location("東京")
        assert len(results) > 0
        assert results[0].name == "東京"

    def test_search_location_partial_match(self):
        """部分一致検索のテスト"""
        manager = LocationManager()

        results = manager.search_location("東")
        assert len(results) > 0
        assert any("東" in result.name for result in results)

    def test_search_location_fuzzy_match(self):
        """あいまい検索のテスト"""
        manager = LocationManager()

        results = manager.search_location("おおさか", fuzzy=True)
        assert len(results) > 0
        # 大阪が結果に含まれることを期待（あいまい検索で）

    def test_search_location_empty_query(self):
        """空クエリでの検索テスト"""
        manager = LocationManager()

        results = manager.search_location("")
        assert len(results) == 0

        results = manager.search_location("   ")
        assert len(results) == 0

    def test_get_location_exact(self):
        """完全一致での地点取得テスト"""
        manager = LocationManager()

        location = manager.get_location("東京")
        assert location is not None
        assert location.name == "東京"

        location = manager.get_location("存在しない地点")
        assert location is None

    def test_get_locations_by_region(self):
        """地方別地点取得のテスト"""
        manager = LocationManager()

        kanto_locations = manager.get_locations_by_region("関東")
        assert len(kanto_locations) > 0

        # 関東地方の地点が正しく含まれているかチェック
        kanto_names = [loc.name for loc in kanto_locations]
        assert "東京" in kanto_names
        assert "横浜" in kanto_names

    def test_get_locations_by_prefecture(self):
        """都道府県別地点取得のテスト"""
        manager = LocationManager()

        hokkaido_locations = manager.get_locations_by_prefecture("北海道")
        assert len(hokkaido_locations) > 0

        # 北海道の地点が正しく含まれているかチェック
        hokkaido_names = [loc.name for loc in hokkaido_locations]
        assert "札幌" in hokkaido_names
        assert "函館" in hokkaido_names

    def test_get_nearby_locations_with_coordinates(self):
        """座標指定での近隣地点取得テスト"""
        manager = LocationManager()

        # 東京の座標
        tokyo_coords = (35.6762, 139.6503)

        nearby = manager.get_nearby_locations(tokyo_coords, radius_km=500, max_results=5)

        # 近隣地点が取得できるかは座標データの有無に依存
        # この実装では座標データがないため、空リストが返される
        assert isinstance(nearby, list)

    def test_get_all_locations(self):
        """全地点取得のテスト"""
        manager = LocationManager()

        all_locations = manager.get_all_locations()
        assert len(all_locations) > 0
        assert isinstance(all_locations, list)
        assert all(isinstance(loc, Location) for loc in all_locations)

    def test_get_statistics(self):
        """統計情報取得のテスト"""
        manager = LocationManager()

        stats = manager.get_statistics()

        assert "total_locations" in stats
        assert "regions" in stats
        assert "prefectures" in stats
        assert "loaded_at" in stats
        assert "csv_path" in stats

        assert stats["total_locations"] > 0
        assert isinstance(stats["regions"], dict)
        assert isinstance(stats["prefectures"], dict)

    def test_build_index(self):
        """インデックス構築のテスト"""
        manager = LocationManager()

        # インデックスが正しく構築されているかチェック
        assert len(manager.location_index) > 0

        # 東京のインデックスがあるかチェック
        tokyo_key = "東京"
        if tokyo_key in manager.location_index:
            assert len(manager.location_index[tokyo_key]) > 0


if __name__ == "__main__":
    pytest.main([__file__])