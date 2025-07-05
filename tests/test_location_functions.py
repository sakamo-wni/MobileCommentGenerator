"""
グローバル関数のテスト

地点データ管理システムのグローバル関数をテストする
"""

import pytest
from unittest.mock import patch, mock_open
from src.data.location_manager import (
    get_location_manager,
    load_locations_from_csv,
    search_location,
    get_location_by_name,
)


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


if __name__ == "__main__":
    pytest.main([__file__])