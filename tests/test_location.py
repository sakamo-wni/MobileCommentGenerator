"""
Locationデータクラスのテスト

地点データの基本的な動作をテストする
"""

import pytest
from src.data.location_manager import Location


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


if __name__ == "__main__":
    pytest.main([__file__])