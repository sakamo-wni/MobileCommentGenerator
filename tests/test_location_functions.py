"""
グローバル関数のテスト

地点データ管理システムのグローバル関数をテストする
"""

import pytest
from unittest.mock import patch, mock_open
from src.data.location.manager import LocationManagerRefactored
from src.data.location import Location


class TestGlobalFunctions:
    """グローバル関数のテスト"""

    def test_location_manager_singleton(self):
        """シングルトンパターンのテスト"""
        manager1 = LocationManagerRefactored()
        manager2 = LocationManagerRefactored()

        assert manager1 is manager2  # 同一インスタンス

    def test_search_location_function(self):
        """検索関数のテスト"""
        manager = LocationManagerRefactored()
        results = manager.search_location("東京")
        assert len(results) > 0
        assert results[0].name == "東京"

    def test_get_location_by_name_function(self):
        """地点名取得関数のテスト"""
        manager = LocationManagerRefactored()
        location = manager.get_location_by_name("東京")
        assert location is not None
        assert location.name == "東京"

        location = manager.get_location_by_name("存在しない地点")
        assert location is None


if __name__ == "__main__":
    pytest.main([__file__])