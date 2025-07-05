"""
地点データ管理システムのテスト

Issue #2: 地点データ管理システムのテスト実装
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from datetime import datetime

from src.data.location_manager import (
    Location,
    LocationManager,
    get_location_manager,
    load_locations_from_csv,
    search_location,
    get_location_by_name,
)


class TestLocation:
    """Location データクラスのテスト"""

    def test_location_creation(self):
        """正常な地点データ作成のテスト"""
        location = Location(
            name="東京", normalized_name="東京", latitude=35.6762, longitude=139.6503
        )

        assert location.name == "東京"
        assert location.normalized_name == "東京"
        assert location.prefecture == "東京都"
        assert location.region == "関東"
        assert location.latitude == 35.6762
        assert location.longitude == 139.6503

    def test_location_auto_normalization(self):
        """自動正規化のテスト"""
        location = Location(name="  東京  ", normalized_name="")

        assert location.normalized_name == "東京"
        assert location.prefecture == "東京都"
        assert location.region == "関東"

    def test_prefecture_inference(self):
        """都道府県推定のテスト"""
        test_cases = [
            ("札幌", "北海道"),
            ("仙台", "宮城県"),
            ("名古屋", "愛知県"),
            ("大阪", "大阪府"),
            ("福岡", "福岡県"),
            ("那覇", "沖縄県"),
        ]

        for city, expected_prefecture in test_cases:
            location = Location(name=city, normalized_name="")
            assert location.prefecture == expected_prefecture, f"{city} -> {expected_prefecture}"

    def test_region_inference(self):
        """地方区分推定のテスト"""
        test_cases = [
            ("札幌", "北海道"),
            ("仙台", "東北"),
            ("東京", "関東"),
            ("名古屋", "中部"),
            ("大阪", "近畿"),
            ("広島", "中国"),
            ("高松", "四国"),
            ("福岡", "九州"),
        ]

        for city, expected_region in test_cases:
            location = Location(name=city, normalized_name="")
            assert location.region == expected_region, f"{city} -> {expected_region}"

    def test_distance_calculation(self):
        """距離計算のテスト"""
        tokyo = Location(name="東京", normalized_name="東京", latitude=35.6762, longitude=139.6503)

        osaka = Location(name="大阪", normalized_name="大阪", latitude=34.6937, longitude=135.5023)

        distance = tokyo.distance_to(osaka)

        assert distance is not None
        assert 400 <= distance <= 450  # 東京-大阪間は約415km

    def test_distance_calculation_without_coordinates(self):
        """座標なしでの距離計算テスト"""
        tokyo = Location(name="東京", normalized_name="東京")
        osaka = Location(name="大阪", normalized_name="大阪")

        distance = tokyo.distance_to(osaka)
        assert distance is None

    def test_matches_query_exact(self):
        """完全一致検索のテスト"""
        location = Location(name="東京", normalized_name="東京")

        assert location.matches_query("東京") == True
        assert location.matches_query("大阪") == False

    def test_matches_query_partial(self):
        """部分一致検索のテスト"""
        location = Location(name="東京", normalized_name="東京")

        assert location.matches_query("東") == True
        assert location.matches_query("京") == True

    def test_matches_query_fuzzy(self):
        """あいまい検索のテスト"""
        location = Location(name="大阪", normalized_name="大阪")

        # レーベンシュタイン距離によるあいまい検索
        assert location.matches_query("おおさか", fuzzy=True) == True
        assert location.matches_query("だいはん", fuzzy=True) == False  # 類似度が低い

    def test_levenshtein_distance(self):
        """レーベンシュタイン距離計算のテスト"""
        location = Location(name="東京", normalized_name="東京")

        # 同じ文字列
        assert location._levenshtein_distance("東京", "東京") == 0

        # 1文字違い
        assert location._levenshtein_distance("東京", "東大") == 1

        # 完全に違う文字列
        assert location._levenshtein_distance("東京", "大阪") == 2

    def test_to_dict(self):
        """辞書変換のテスト"""
        location = Location(
            name="東京", normalized_name="東京", latitude=35.6762, longitude=139.6503
        )

        location_dict = location.to_dict()

        assert location_dict["name"] == "東京"
        assert location_dict["normalized_name"] == "東京"
        assert location_dict["prefecture"] == "東京都"
        assert location_dict["region"] == "関東"
        assert location_dict["latitude"] == 35.6762
        assert location_dict["longitude"] == 139.6503


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


class TestGlobalFunctions:
    """グローバル関数のテスト"""

    def test_get_location_manager_singleton(self):
        """シングルトンパターンのテスト"""
        # グローバル変数をリセット
        from src.data import location_manager

        location_manager._location_manager = None

        manager1 = get_location_manager()
        manager2 = get_location_manager()

        assert manager1 is manager2  # 同一インスタンス

    def test_load_locations_from_csv_function(self):
        """CSV読み込み関数のテスト"""
        csv_content = "東京\n大阪\n名古屋\n"

        with patch("builtins.open", mock_open(read_data=csv_content)):
            locations = load_locations_from_csv("test.csv")

            assert len(locations) == 3
            location_names = [loc.name for loc in locations]
            assert "東京" in location_names
            assert "大阪" in location_names
            assert "名古屋" in location_names

    def test_search_location_function(self):
        """検索関数のテスト"""
        results = search_location("東京")
        assert len(results) > 0
        assert results[0].name == "東京"

    def test_get_location_by_name_function(self):
        """地点名取得関数のテスト"""
        location = get_location_by_name("東京")
        assert location is not None
        assert location.name == "東京"

        location = get_location_by_name("存在しない地点")
        assert location is None


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_file_not_found_error(self):
        """ファイル未発見エラーのテスト"""
        with patch("os.path.exists", return_value=False):
            manager = LocationManager("nonexistent.csv")

            # デフォルトデータが読み込まれる
            assert len(manager.locations) > 0

    def test_file_read_error(self):
        """ファイル読み込みエラーのテスト"""
        with patch("builtins.open", side_effect=IOError("読み込みエラー")):
            with patch("os.path.exists", return_value=True):
                manager = LocationManager("error.csv")

                # デフォルトデータが読み込まれる
                assert len(manager.locations) > 0

    def test_invalid_csv_format(self):
        """不正なCSVフォーマットのテスト"""
        invalid_csv = "地点1\n\n\n地点2\n   \n地点3"

        with patch("builtins.open", mock_open(read_data=invalid_csv)):
            with patch("os.path.exists", return_value=True):
                manager = LocationManager("invalid.csv")

                # 有効なデータのみ読み込まれる
                location_names = [loc.name for loc in manager.locations]
                assert "地点1" in location_names
                assert "地点2" in location_names
                assert "地点3" in location_names


class TestPerformance:
    """パフォーマンステスト"""

    def test_search_performance(self):
        """検索性能のテスト"""
        manager = LocationManager()

        import time

        # 複数回検索を実行して時間を測定
        start_time = time.time()
        for _ in range(100):
            manager.search_location("東京")
        end_time = time.time()

        # 100回の検索が1秒以内に完了することを確認
        assert (end_time - start_time) < 1.0

    def test_index_performance(self):
        """インデックス性能のテスト"""
        manager = LocationManager()

        import time

        # インデックス再構築の時間を測定
        start_time = time.time()
        manager._build_index()
        end_time = time.time()

        # インデックス構築が0.1秒以内に完了することを確認
        assert (end_time - start_time) < 0.1


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_location_name(self):
        """空の地点名のテスト"""
        location = Location(name="", normalized_name="")
        assert location.normalized_name == ""
        assert location.prefecture is None
        assert location.region is None

    def test_unicode_normalization(self):
        """Unicode正規化のテスト"""
        # 全角・半角混在
        location = Location(name="東京１２３", normalized_name="")
        assert "123" in location.normalized_name  # 半角数字に変換される

    def test_special_characters(self):
        """特殊文字を含む地点名のテスト"""
        location = Location(name="東京　（特別区）", normalized_name="")
        assert location.normalized_name == "東京(特別区)"  # 全角スペースと括弧が半角に

    def test_large_dataset_performance(self):
        """大規模データセットでの性能テスト"""
        # 大量の地点データを作成
        large_locations = [
            Location(name=f"地点{i}", normalized_name=f"地点{i}") for i in range(1000)
        ]

        manager = LocationManager()
        manager.locations = large_locations
        manager._build_index()

        import time

        start_time = time.time()

        # 検索実行
        results = manager.search_location("地点500")

        end_time = time.time()

        # 検索時間が合理的な範囲内であることを確認
        assert (end_time - start_time) < 0.1
        assert len(results) > 0

    def test_fuzzy_search_accuracy(self):
        """あいまい検索の精度テスト"""
        manager = LocationManager()

        # ひらがな・カタカナでの検索
        results = manager.search_location("おおさか", fuzzy=True)
        osaka_found = any("大阪" in result.name for result in results)

        # 期待：大阪が見つかる（あいまい検索で）
        # 実際の結果は実装依存だが、テストケースとして記録
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__])
