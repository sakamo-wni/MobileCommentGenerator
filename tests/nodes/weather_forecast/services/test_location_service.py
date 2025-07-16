"""LocationServiceの単体テスト"""

import pytest
from unittest.mock import Mock, patch
from src.nodes.weather_forecast.services.location_service import LocationService
from src.data.location.models import Location


class TestLocationService:
    """LocationServiceのテスト"""
    
    @pytest.fixture
    def location_service(self):
        """LocationServiceのインスタンスを作成"""
        return LocationService()
    
    def test_parse_location_string_simple(self, location_service):
        """シンプルな地点名の解析"""
        name, lat, lon = location_service.parse_location_string("東京")
        
        assert name == "東京"
        assert lat is None
        assert lon is None
    
    def test_parse_location_string_with_coordinates(self, location_service):
        """座標付き地点名の解析"""
        name, lat, lon = location_service.parse_location_string("東京,35.6762,139.6503")
        
        assert name == "東京"
        assert lat == 35.6762
        assert lon == 139.6503
    
    def test_parse_location_string_with_spaces(self, location_service):
        """空白を含む地点名の解析"""
        name, lat, lon = location_service.parse_location_string(" 大阪 , 34.6937 , 135.5023 ")
        
        assert name == "大阪"
        assert lat == 34.6937
        assert lon == 135.5023
    
    def test_parse_location_string_invalid_coordinates(self, location_service):
        """不正な座標の処理"""
        name, lat, lon = location_service.parse_location_string("名古屋,invalid,coordinate")
        
        assert name == "名古屋"
        assert lat is None
        assert lon is None
    
    def test_parse_location_string_partial_coordinates(self, location_service):
        """部分的な座標情報の処理"""
        name, lat, lon = location_service.parse_location_string("福岡,33.5904")
        
        assert name == "福岡"
        assert lat is None
        assert lon is None
    
    @patch('src.nodes.weather_forecast.services.location_service.LocationManagerRefactored')
    def test_get_location_with_coordinates_found(self, mock_manager_class, location_service):
        """LocationManagerで地点が見つかる場合"""
        # Mockの設定
        mock_location = Location(
            name="東京",
            prefecture="東京都",
            region="関東",
            latitude=35.6762,
            longitude=139.6503
        )
        
        mock_manager = Mock()
        mock_manager.get_location.return_value = mock_location
        mock_manager_class.return_value = mock_manager
        
        # 新しいインスタンスを作成（モックを使用するため）
        service = LocationService()
        location = service.get_location_with_coordinates("東京")
        
        assert location.name == "東京"
        assert location.latitude == 35.6762
        assert location.longitude == 139.6503
    
    @patch('src.nodes.weather_forecast.services.location_service.LocationManagerRefactored')
    def test_get_location_with_coordinates_not_found_with_coords(self, mock_manager_class, location_service):
        """LocationManagerで見つからないが座標が提供されている場合"""
        mock_manager = Mock()
        mock_manager.get_location.return_value = None
        mock_manager_class.return_value = mock_manager
        
        service = LocationService()
        location = service.get_location_with_coordinates("カスタム地点", 40.0, 140.0)
        
        assert location.name == "カスタム地点"
        assert location.prefecture == "不明"
        assert location.region == "不明"
        assert location.latitude == 40.0
        assert location.longitude == 140.0
    
    @patch('src.nodes.weather_forecast.services.location_service.LocationManagerRefactored')
    def test_get_location_with_coordinates_not_found_no_coords(self, mock_manager_class, location_service):
        """LocationManagerで見つからず座標も提供されていない場合"""
        mock_manager = Mock()
        mock_manager.get_location.return_value = None
        mock_manager_class.return_value = mock_manager
        
        service = LocationService()
        
        with pytest.raises(ValueError, match="地点 '不明な地点' が見つかりません"):
            service.get_location_with_coordinates("不明な地点")
    
    @patch('src.nodes.weather_forecast.services.location_service.LocationManagerRefactored')
    def test_get_location_with_coordinates_override(self, mock_manager_class, location_service):
        """LocationManagerの地点に提供された座標で上書き"""
        # LocationManagerから返される地点
        mock_location = Location(
            name="東京",
            prefecture="東京都",
            region="関東",
            latitude=35.6762,
            longitude=139.6503
        )
        
        mock_manager = Mock()
        mock_manager.get_location.return_value = mock_location
        mock_manager_class.return_value = mock_manager
        
        service = LocationService()
        # 異なる座標を提供
        location = service.get_location_with_coordinates("東京", 35.7000, 140.0000)
        
        assert location.name == "東京"
        assert location.prefecture == "東京都"
        assert location.region == "関東"
        # 提供された座標で上書きされている
        assert location.latitude == 35.7000
        assert location.longitude == 140.0000