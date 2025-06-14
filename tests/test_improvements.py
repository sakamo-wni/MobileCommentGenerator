"""改善項目のテスト

PR #58で実装された改善項目が正しく動作することを確認するテスト
"""

import pytest
import os
import tempfile
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# テスト対象のインポート
from src.utils.exceptions import (
    ConfigurationError, APIError, DataValidationError,
    FileOperationError, S3Error
)
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.config.config_loader import ConfigLoader
from src.nodes.comment_selector import CommentSelector
from src.utils.data_manager import DataManager
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType


class TestCustomExceptions:
    """カスタム例外クラスのテスト"""
    
    def test_exception_hierarchy(self):
        """例外の継承関係が正しいことを確認"""
        # 基底クラスでキャッチできることを確認
        with pytest.raises(Exception):
            raise ConfigurationError("test")
        
        # 具体的な例外タイプでキャッチできることを確認
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("test")
        
        # APIError系
        with pytest.raises(APIError):
            raise APIError("test")


class TestConfigurationExternalization:
    """設定の外部化テスト"""
    
    def test_config_loader(self):
        """ConfigLoaderが正しく動作することを確認"""
        # validation_rules.yamlが存在することを確認
        config = ConfigLoader.load_config("validation_rules.yaml")
        
        assert "weather_forbidden_words" in config
        assert "temperature_forbidden_words" in config
        assert "required_keywords" in config
        assert "thresholds" in config
    
    def test_weather_validator_uses_config(self):
        """WeatherCommentValidatorが設定ファイルを使用することを確認"""
        validator = WeatherCommentValidator()
        
        # 設定が読み込まれていることを確認
        assert validator.weather_forbidden_words is not None
        assert validator.temperature_forbidden_words is not None
        assert validator.thresholds is not None
        
        # 閾値が設定から読み込まれていることを確認
        assert validator.thresholds["temperature"]["hot"] == 30
        assert validator.thresholds["temperature"]["cold"] == 12


class TestLLMSelection:
    """LLM選択機能のテスト"""
    
    @patch('src.nodes.comment_selector.LLMManager')
    def test_llm_selection_implementation(self, mock_llm_manager):
        """LLM選択が実装されていることを確認"""
        # モックの設定
        mock_llm = Mock()
        mock_llm.generate.return_value = "2"  # 3番目の候補を選択
        
        validator = Mock()
        selector = CommentSelector(mock_llm, validator)
        
        # テスト用の候補
        candidates = [
            {'index': 0, 'comment': 'コメント1', 'usage_count': 10},
            {'index': 1, 'comment': 'コメント2', 'usage_count': 20},
            {'index': 2, 'comment': 'コメント3', 'usage_count': 15},
        ]
        
        # テスト用の天気データ
        weather_data = WeatherForecast(
            datetime=datetime.now(),
            weather_condition=WeatherCondition.RAINY,
            weather_description="雨",
            temperature=20.0,
            humidity=80,
            wind_speed=3.0,
            wind_direction="北",
            precipitation=5.0,
            location="東京"
        )
        
        # LLM選択メソッドを実行
        result = selector._llm_select_comment(
            candidates, weather_data, "東京", datetime.now(), 
            CommentType.WEATHER_COMMENT
        )
        
        # LLMが呼ばれたことを確認
        assert mock_llm.generate.called
        
        # 結果が返されることを確認
        assert result is not None
        assert isinstance(result, PastComment)
    
    def test_llm_prompt_building(self):
        """LLM用プロンプトが適切に構築されることを確認"""
        mock_llm = Mock()
        validator = Mock()
        selector = CommentSelector(mock_llm, validator)
        
        candidates = [
            {'index': 0, 'comment': 'テストコメント', 'usage_count': 10}
        ]
        
        weather_data = WeatherForecast(
            datetime=datetime.now(),
            weather_condition=WeatherCondition.RAINY,
            weather_description="雨",
            temperature=20.0,
            humidity=80,
            wind_speed=3.0,
            wind_direction="北",
            precipitation=5.0,
            location="東京"
        )
        
        prompt = selector._build_selection_prompt(
            candidates, weather_data, "東京", datetime.now(),
            CommentType.WEATHER_COMMENT
        )
        
        # プロンプトに必要な要素が含まれていることを確認
        assert "天気情報" in prompt
        assert "候補リスト" in prompt
        assert "選択基準" in prompt
        assert "降水量: 5.0mm" in prompt


class TestDataManagement:
    """データ管理機能のテスト"""
    
    def test_data_manager_initialization(self):
        """DataManagerが正しく初期化されることを確認"""
        manager = DataManager()
        
        assert manager.forecast_retention_days > 0
        assert manager.history_max_size_mb > 0
        assert manager.history_archive_days > 0
    
    def test_forecast_cache_cleanup(self):
        """forecast_cacheのクリーンアップが動作することを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用のforecast_cacheディレクトリを作成
            cache_dir = Path(tmpdir) / "forecast_cache"
            cache_dir.mkdir()
            
            # 古いデータと新しいデータを含むCSVファイルを作成
            csv_file = cache_dir / "test_location.csv"
            old_date = (datetime.now() - timedelta(days=40)).isoformat()
            new_date = (datetime.now() - timedelta(days=5)).isoformat()
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['target_datetime', 'data'])
                writer.writeheader()
                writer.writerow({'target_datetime': old_date, 'data': 'old'})
                writer.writerow({'target_datetime': new_date, 'data': 'new'})
            
            # DataManagerをパッチして使用
            manager = DataManager()
            manager.forecast_cache_dir = cache_dir
            
            # クリーンアップを実行
            result = manager.clean_forecast_cache(retention_days=30)
            
            # 古いデータが削除されたことを確認
            assert result['deleted_rows'] == 1
            
            # 新しいデータが残っていることを確認
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['data'] == 'new'
    
    def test_generation_history_archive(self):
        """generation_historyのアーカイブが動作することを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用のファイルを作成
            history_file = Path(tmpdir) / "generation_history.json"
            archive_dir = Path(tmpdir) / "archive"
            archive_dir.mkdir()
            
            # 大きなダミーデータを作成
            old_date = (datetime.now() - timedelta(days=10)).isoformat()
            new_date = (datetime.now() - timedelta(days=2)).isoformat()
            
            data = [
                {"timestamp": old_date, "data": "old" * 1000},
                {"timestamp": new_date, "data": "new" * 1000},
            ]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            # DataManagerをパッチして使用
            manager = DataManager()
            manager.generation_history_file = history_file
            manager.archive_dir = archive_dir
            manager.history_max_size_mb = 0.001  # 小さい閾値に設定
            
            # アーカイブを実行
            result = manager.archive_generation_history()
            
            # アーカイブが作成されたことを確認
            assert result['status'] == 'archived'
            assert result['archived_entries'] == 1
            assert result['remaining_entries'] == 1
            
            # アーカイブファイルが存在することを確認
            archive_files = list(archive_dir.glob("*.json.gz"))
            assert len(archive_files) == 1


class TestImprovedErrorHandling:
    """改善されたエラーハンドリングのテスト"""
    
    def test_specific_exception_types(self):
        """具体的な例外タイプが使用されることを確認"""
        from src.repositories.local_comment_repository import LocalCommentRepository
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 存在しないディレクトリを指定
            with pytest.raises(FileNotFoundError):
                LocalCommentRepository(output_dir=tmpdir + "/nonexistent")


class TestS3ConfigSecurity:
    """S3設定のセキュリティテスト"""
    
    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'})
    def test_s3_config_from_env(self):
        """S3設定が環境変数から読み込まれることを確認"""
        # enhanced_comment_generator.pyのload_s3_config関数をインポート
        from enhanced_comment_generator import load_s3_config
        
        config = load_s3_config()
        assert config['bucket_name'] == 'test-bucket'
    
    def test_s3_config_requires_bucket_name(self):
        """S3バケット名が必須であることを確認"""
        from enhanced_comment_generator import load_s3_config
        
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            # 設定ファイルも存在しない想定
            with patch('os.path.exists', return_value=False):
                with pytest.raises(ValueError, match="S3_BUCKET_NAME"):
                    load_s3_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])