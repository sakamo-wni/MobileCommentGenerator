"""ConfigManagerのテスト"""

import pytest
from unittest.mock import patch, Mock, MagicMock

from src.controllers.config_manager import ConfigManager
from src.config.app_config import AppConfig


class TestConfigManager:
    """ConfigManagerのテストクラス"""
    
    @pytest.fixture
    def mock_config(self):
        """テスト用のモック設定"""
        config = Mock(spec=AppConfig)
        config.ui_settings = Mock()
        config.ui_settings.default_llm_provider = 'gemini'
        config.app = Mock()
        config.app.max_llm_workers = 3
        config.app.use_async_weather = True
        config.app.cache_ttl_minutes = 60
        config.api = Mock()
        config.api.timeout = 30
        config.to_dict = Mock(return_value={
            'api': {'timeout': 30},
            'app': {'max_llm_workers': 3},
            'ui_settings': {'default_llm_provider': 'gemini'}
        })
        return config
    
    @pytest.fixture
    def manager(self, mock_config):
        """テスト用のConfigManagerインスタンス"""
        with patch('src.config.app_config.get_config', return_value=mock_config):
            return ConfigManager()
    
    def test_initialization_with_config(self, mock_config):
        """設定を指定した初期化のテスト"""
        manager = ConfigManager(config=mock_config)
        assert manager.config == mock_config
    
    def test_initialization_without_config(self, mock_config):
        """設定を指定しない初期化のテスト"""
        with patch('src.config.app_config.get_config', return_value=mock_config):
            manager = ConfigManager()
            assert manager.config == mock_config
    
    def test_config_property(self, manager, mock_config):
        """configプロパティのテスト"""
        assert manager.config == mock_config
    
    def test_get_default_locations(self, manager):
        """デフォルト地点リスト取得のテスト"""
        sample_locations = ['東京', '大阪', '名古屋']
        with patch('src.ui.streamlit_utils.load_locations', return_value=sample_locations):
            locations = manager.get_default_locations()
            assert locations == sample_locations
    
    def test_get_default_llm_provider(self, manager):
        """デフォルトLLMプロバイダー取得のテスト"""
        provider = manager.get_default_llm_provider()
        assert provider == 'gemini'
    
    def test_get_config_dict(self, manager):
        """設定の辞書形式取得のテスト"""
        config_dict = manager.get_config_dict()
        assert config_dict == {
            'api': {'timeout': 30},
            'app': {'max_llm_workers': 3},
            'ui_settings': {'default_llm_provider': 'gemini'}
        }
    
    def test_get_max_llm_workers(self, manager):
        """最大LLMワーカー数取得のテスト"""
        workers = manager.get_max_llm_workers()
        assert workers == 3
    
    def test_is_async_weather_enabled(self, manager):
        """非同期天気予報取得の有効状態確認テスト"""
        enabled = manager.is_async_weather_enabled()
        assert enabled is True
    
    def test_get_api_timeout(self, manager):
        """APIタイムアウト取得のテスト"""
        timeout = manager.get_api_timeout()
        assert timeout == 30
    
    def test_get_cache_ttl(self, manager):
        """キャッシュTTL取得のテスト"""
        ttl = manager.get_cache_ttl()
        assert ttl == 60
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 設定値がNoneの場合
        config = Mock(spec=AppConfig)
        config.ui_settings = Mock()
        config.ui_settings.default_llm_provider = None
        config.app = Mock()
        config.app.max_llm_workers = None
        config.app.use_async_weather = None
        config.app.cache_ttl_minutes = None
        config.api = Mock()
        config.api.timeout = None
        
        manager = ConfigManager(config=config)
        
        # Noneが返される
        assert manager.get_default_llm_provider() is None
        assert manager.get_max_llm_workers() is None
        assert manager.is_async_weather_enabled() is None
        assert manager.get_api_timeout() is None
        assert manager.get_cache_ttl() is None
    
    @patch('src.ui.streamlit_utils.load_locations')
    def test_load_locations_error(self, mock_load_locations, manager):
        """地点リスト読み込みエラーのテスト"""
        # エラーが発生した場合
        mock_load_locations.side_effect = Exception("Failed to load")
        
        with pytest.raises(Exception) as exc_info:
            manager.get_default_locations()
        
        assert str(exc_info.value) == "Failed to load"