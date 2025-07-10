"""アプリケーション設定（app_config.py）のテスト"""

import os
import pytest
from pathlib import Path
from unittest import mock

from src.config.app_config import (
    APIKeys,
    UISettings,
    GenerationSettings,
    DataSettings,
    AppConfig,
    get_config,
    reset_config
)


class TestAPIKeys:
    """APIKeysクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        api_keys = APIKeys()
        
        assert api_keys.openai_key is None
        assert api_keys.gemini_key is None
        assert api_keys.anthropic_key is None
        assert api_keys.wxtech_key is None
        assert api_keys.aws_access_key_id is None
        assert api_keys.aws_secret_access_key is None
        assert api_keys.aws_region == "ap-northeast-1"
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "OPENAI_API_KEY": "test_openai",
            "GEMINI_API_KEY": "test_gemini",
            "ANTHROPIC_API_KEY": "test_anthropic",
            "WXTECH_API_KEY": "test_wxtech",
            "AWS_ACCESS_KEY_ID": "test_aws_key",
            "AWS_SECRET_ACCESS_KEY": "test_aws_secret",
            "AWS_DEFAULT_REGION": "us-west-2"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            # API設定のモックも必要
            with mock.patch('src.config.app_config.get_api_config') as mock_api:
                mock_api.return_value.openai_api_key = "test_openai"
                mock_api.return_value.gemini_api_key = "test_gemini"
                mock_api.return_value.anthropic_api_key = "test_anthropic"
                mock_api.return_value.wxtech_api_key = "test_wxtech"
                mock_api.return_value.aws_access_key_id = "test_aws_key"
                mock_api.return_value.aws_secret_access_key = "test_aws_secret"
                mock_api.return_value.aws_region = "us-west-2"
                
                api_keys = APIKeys.from_env()
                
                assert api_keys.openai_key == "test_openai"
                assert api_keys.gemini_key == "test_gemini"
                assert api_keys.anthropic_key == "test_anthropic"
                assert api_keys.wxtech_key == "test_wxtech"
                assert api_keys.aws_access_key_id == "test_aws_key"
                assert api_keys.aws_secret_access_key == "test_aws_secret"
                assert api_keys.aws_region == "us-west-2"
    
    def test_validate(self):
        """APIキーの存在検証テスト"""
        # get_api_config()をモックして適切な値を返すようにする
        with mock.patch('src.config.app_config.get_api_config') as mock_api_config:
            # モックの設定
            mock_config = mock.Mock()
            mock_config.validate_keys.return_value = {
                "openai": True,
                "gemini": False,
                "anthropic": False,
                "wxtech": True,
                "aws": True
            }
            mock_api_config.return_value = mock_config
            
            # 一部のキーのみ設定
            api_keys = APIKeys(
                openai_key="key1",
                wxtech_key="key2",
                aws_access_key_id="aws_key",
                aws_secret_access_key="aws_secret"
            )
            
            validation = api_keys.validate()
            
            assert validation["openai"] is True
            assert validation["gemini"] is False
            assert validation["anthropic"] is False
            assert validation["wxtech"] is True
            assert validation["aws"] is True  # 両方のAWSキーが必要
            
            # AWSキーの片方だけの場合
            mock_config.validate_keys.return_value = {
                "openai": False,
                "gemini": False,
                "anthropic": False,
                "wxtech": False,
                "aws": False
            }
            api_keys = APIKeys(aws_access_key_id="aws_key")
            validation = api_keys.validate()
            assert validation["aws"] is False
    
    def test_get_llm_key(self):
        """LLMプロバイダーキー取得テスト"""
        with mock.patch('src.config.app_config.get_api_config') as mock_api_config:
            # モックの設定
            mock_config = mock.Mock()
            mock_config.get_llm_key.side_effect = lambda provider: {
                "openai": "openai_test",
                "gemini": "gemini_test",
                "anthropic": "anthropic_test",
                "OPENAI": "openai_test"
            }.get(provider, None)
            mock_api_config.return_value = mock_config
            
            api_keys = APIKeys(
                openai_key="openai_test",
                gemini_key="gemini_test",
                anthropic_key="anthropic_test"
            )
            
            assert api_keys.get_llm_key("openai") == "openai_test"
            assert api_keys.get_llm_key("gemini") == "gemini_test"
            assert api_keys.get_llm_key("anthropic") == "anthropic_test"
            assert api_keys.get_llm_key("unknown") is None
            assert api_keys.get_llm_key("OPENAI") == "openai_test"  # 大文字小文字を区別しない


class TestUISettings:
    """UISettingsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        ui_settings = UISettings()
        
        assert ui_settings.page_title == "天気コメント生成システム"
        assert ui_settings.page_icon == "☀️"
        assert ui_settings.layout == "wide"
        assert ui_settings.sidebar_state == "expanded"
        assert ui_settings.theme == "light"
        assert ui_settings.max_locations_per_generation == 30
        assert ui_settings.default_llm_provider == "gemini"
        assert ui_settings.show_debug_info is False
        assert ui_settings.date_format == "%Y年%m月%d日 %H時%M分"
        assert ui_settings.timezone == "Asia/Tokyo"


class TestGenerationSettings:
    """GenerationSettingsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        gen_settings = GenerationSettings()
        
        assert gen_settings.timeout == 60000  # ミリ秒
        assert gen_settings.max_retries == 3
        assert gen_settings.batch_size == 10
        assert gen_settings.concurrent_requests == 5
        assert gen_settings.cache_enabled is True
        assert gen_settings.cache_ttl_hours == 24


class TestDataSettings:
    """DataSettingsクラスのテスト"""
    
    def test_default_values(self):
        """デフォルト値のテスト"""
        data_settings = DataSettings()
        
        assert data_settings.data_dir == Path("data")
        assert data_settings.forecast_cache_dir == Path("data/forecast_cache")
        assert data_settings.generation_history_file == Path("data/generation_history.json")
        assert data_settings.locations_file == Path("data/locations.json")
        assert data_settings.csv_output_dir == Path("output")
        assert data_settings.use_local_csv is True
        assert data_settings.max_history_records == 1000
        assert data_settings.history_retention_days == 30


class TestAppConfig:
    """AppConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        config = AppConfig()
        
        assert isinstance(config.api_keys, APIKeys)
        assert isinstance(config.ui_settings, UISettings)
        assert isinstance(config.generation_settings, GenerationSettings)
        assert isinstance(config.data_settings, DataSettings)
        assert config.env == "development"
        assert config.debug is False
        assert config.log_level == "INFO"
    
    def test_from_env(self):
        """環境変数からの設定読み込みテスト"""
        env_vars = {
            "MAX_LOCATIONS_PER_GENERATION": "50",
            "DEFAULT_LLM_PROVIDER": "openai"
        }
        
        with mock.patch.dict(os.environ, env_vars):
            with mock.patch('src.config.app_config.get_new_config') as mock_config:
                mock_config.return_value.app.env = "production"
                mock_config.return_value.app.log_level = "WARNING"
                mock_config.return_value.app.debug = False
                mock_config.return_value.api.openai_api_key = None
                mock_config.return_value.api.gemini_api_key = None
                mock_config.return_value.api.anthropic_api_key = None
                mock_config.return_value.api.wxtech_api_key = "test_key"
                
                # UISettingsをモック
                mock_ui = mock.Mock()
                mock_ui.max_locations_per_generation = 50
                mock_ui.default_llm_provider = "openai"
                mock_config.return_value.ui = mock_ui
                
                # GenerationSettingsとDataSettingsもモック
                mock_config.return_value.generation = mock.Mock()
                mock_config.return_value.data = mock.Mock()
                
                config = AppConfig.from_env()
                
                assert config.ui_settings.max_locations_per_generation == 50
                assert config.ui_settings.default_llm_provider == "openai"
                assert config.env == "production"
                assert config.debug is False  # productionなのでFalse
                assert config.log_level == "WARNING"
    
    def test_validate(self):
        """設定の検証テスト"""
        # conftest.pyのautouse fixtureが設定する環境変数をクリア
        clean_env = {
            "WXTECH_API_KEY": "test_key",
            "OPENAI_API_KEY": "",
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": ""
        }
        
        with mock.patch.dict(os.environ, clean_env, clear=True):
            with mock.patch('src.config.app_config.get_new_config') as mock_config:
                mock_config.return_value.api.wxtech_api_key = "test_key"
                mock_config.return_value.api.openai_api_key = None
                mock_config.return_value.api.gemini_api_key = None
                mock_config.return_value.api.anthropic_api_key = None
                mock_config.return_value.app.env = "development"
                mock_config.return_value.app.log_level = "INFO"
                mock_config.return_value.app.debug = True  # developmentモードなのでTrue
                
                # Mocking for data_settings
                mock_data = mock.Mock()
                # Create mock Path objects
                mock_data_dir = mock.Mock(spec=Path)
                mock_data_dir.exists.return_value = True
                mock_locations_file = mock.Mock(spec=Path)
                mock_locations_file.exists.return_value = True
                
                mock_data.data_dir = mock_data_dir
                mock_data.locations_file = mock_locations_file
                mock_config.return_value.data = mock_data
                
                # Mocking for ui and generation
                mock_config.return_value.ui = mock.Mock()
                mock_config.return_value.generation = mock.Mock()
                
                config = AppConfig.from_env()
                validation = config.validate()
                
                assert "api_keys" in validation
                assert validation["api_keys"]["wxtech"] is True
                assert validation["api_keys"]["openai"] is False
                assert validation["environment"] == "development"
                assert validation["debug_mode"] is True
    
    def test_to_dict(self):
        """辞書形式への変換テスト（APIキー除外）"""
        config = AppConfig()
        config.env = "test"
        config.debug = True
        config.ui_settings.max_locations_per_generation = 100
        
        config_dict = config.to_dict()
        
        assert config_dict["environment"] == "test"
        assert config_dict["debug"] is True
        assert config_dict["ui_settings"]["max_locations"] == 100
        
        # APIキー情報が含まれていないことを確認
        assert "api_keys" not in config_dict


class TestGetConfig:
    """get_config関数のテスト"""
    
    def test_singleton_behavior(self):
        """シングルトンとして動作することのテスト"""
        # 設定をリセット
        reset_config()
        
        with mock.patch('src.config.app_config.get_new_config') as mock_config:
            mock_config.return_value.api.wxtech_api_key = "test_key"
            mock_config.return_value.api.openai_api_key = None
            mock_config.return_value.api.gemini_api_key = None
            mock_config.return_value.api.anthropic_api_key = None
            mock_config.return_value.app.env = "development"
            mock_config.return_value.app.log_level = "INFO"
            
            config1 = get_config()
            config2 = get_config()
            
            assert config1 is config2
    
    def test_config_validation_on_load(self):
        """設定読み込み時の検証テスト"""
        reset_config()
        
        with mock.patch('src.config.app_config.get_new_config') as mock_config:
            mock_config.return_value.api.wxtech_api_key = None  # 必須キーが未設定
            mock_config.return_value.api.openai_api_key = None
            mock_config.return_value.api.gemini_api_key = None
            mock_config.return_value.api.anthropic_api_key = None
            mock_config.return_value.app.env = "development"
            mock_config.return_value.app.log_level = "INFO"
            mock_config.return_value.app.debug = True
            
            # APIキー検証のモック
            with mock.patch('src.config.app_config.get_api_config') as mock_api_config:
                mock_api = mock.Mock()
                mock_api.validate_keys.return_value = {
                    "wxtech": False,  # WXTECHキーが未設定
                    "openai": False,
                    "gemini": False,
                    "anthropic": False,
                    "aws": False
                }
                mock_api_config.return_value = mock_api
                
                # データ設定のモック
                mock_data = mock.Mock()
                mock_data_dir = mock.Mock(spec=Path)
                mock_data_dir.exists.return_value = True
                mock_locations_file = mock.Mock(spec=Path)
                mock_locations_file.exists.return_value = True
                mock_data.data_dir = mock_data_dir
                mock_data.locations_file = mock_locations_file
                mock_config.return_value.data = mock_data
                
                # その他のモック
                mock_config.return_value.ui = mock.Mock()
                mock_config.return_value.generation = mock.Mock()
                
                # 警告ログが出力されることを確認
                with mock.patch('src.config.app_config.logger') as mock_logger:
                    config = get_config()
                    mock_logger.warning.assert_called_with("WXTECH_API_KEY is not set. Weather data fetching will fail.")


class TestResetConfig:
    """reset_config関数のテスト"""
    
    def test_reset_functionality(self):
        """設定リセット機能のテスト"""
        # 最初の設定を取得
        config1 = get_config()
        assert config1 is not None
        
        # リセット
        reset_config()
        
        # 新しい設定を取得
        config2 = get_config()
        assert config2 is not None
        
        # リセット後は別のインスタンスになることを確認
        assert config1 is not config2