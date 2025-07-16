"""
Test module for ParallelCommentGenerator

並列コメント生成器のテスト
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import TimeoutError
import threading

from src.controllers.parallel_comment_generator import ParallelCommentGenerator
from src.types import LocationResult, BatchGenerationResult


class TestParallelCommentGenerator:
    """ParallelCommentGeneratorのテストクラス"""
    
    @pytest.fixture
    def generator(self):
        """テスト用のParallelCommentGeneratorインスタンス"""
        return ParallelCommentGenerator(
            max_workers=2,
            timeout_per_location=5,
            max_parallel_locations=10
        )
    
    @pytest.fixture
    def mock_weather_data(self):
        """モックの天気データ"""
        return {
            "東京": {"forecast_collection": Mock(), "location": Mock()},
            "大阪": {"forecast_collection": Mock(), "location": Mock()},
            "名古屋": {"forecast_collection": Mock(), "location": Mock()},
        }
    
    def test_init_with_config(self):
        """設定値を使用した初期化のテスト"""
        with patch('src.controllers.parallel_comment_generator.get_config') as mock_config:
            mock_config.return_value.generation.max_parallel_workers = 8
            mock_config.return_value.generation.comment_timeout_seconds = 60
            mock_config.return_value.generation.max_parallel_locations = 50
            
            generator = ParallelCommentGenerator()
            
            assert generator.max_workers == 8
            assert generator.timeout_per_location == 60
            assert generator.max_parallel_locations == 50
    
    def test_init_with_custom_values(self):
        """カスタム値での初期化のテスト"""
        generator = ParallelCommentGenerator(
            max_workers=4,
            timeout_per_location=30,
            max_parallel_locations=20
        )
        
        assert generator.max_workers == 4
        assert generator.timeout_per_location == 30
        assert generator.max_parallel_locations == 20
    
    @patch('src.controllers.parallel_comment_generator.run_comment_generation')
    def test_parallel_generation_success(self, mock_run_generation, generator, mock_weather_data):
        """並列生成の成功ケースのテスト"""
        # モックの戻り値を設定
        mock_run_generation.return_value = {
            "final_comment": "テストコメント",
            "advice_comment": "アドバイス",
            "weather_summary": "天気概要",
            "generation_metadata": {"test": "data"}
        }
        
        # 並列生成を実行
        result = generator.generate_parallel(
            mock_weather_data,
            llm_provider="gemini"
        )
        
        # 結果を検証
        assert isinstance(result, BatchGenerationResult)
        assert result["total_count"] == 3
        assert result["success_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["results"]) == 3
        
        # 各結果の検証
        for location_result in result["results"]:
            assert location_result["success"] is True
            assert location_result["comment"] == "テストコメント"
            assert location_result["advice"] == "アドバイス"
    
    @patch('src.controllers.parallel_comment_generator.run_comment_generation')
    def test_serial_generation_for_small_batch(self, mock_run_generation, generator):
        """少数の地点でシリアル処理になることのテスト"""
        mock_run_generation.return_value = {
            "final_comment": "テストコメント",
            "advice_comment": "",
            "weather_summary": "",
            "generation_metadata": {}
        }
        
        # 1地点のみ（シリアル処理になるはず）
        single_location = {"東京": {"forecast_collection": Mock()}}
        
        result = generator.generate_parallel(single_location)
        
        assert result["total_count"] == 1
        assert result["success_count"] == 1
        
        # 統計情報を確認
        stats = generator.get_stats()
        assert stats["serial_processed"] == 1
        assert stats["parallel_processed"] == 0
    
    @patch('src.controllers.parallel_comment_generator.run_comment_generation')
    def test_serial_generation_for_large_batch(self, mock_run_generation, generator):
        """大量の地点でシリアル処理になることのテスト"""
        mock_run_generation.return_value = {"final_comment": "テスト"}
        
        # 21地点（max_parallel_locations=10を超える）
        large_batch = {f"地点{i}": {"data": i} for i in range(21)}
        
        result = generator.generate_parallel(large_batch)
        
        assert result["total_count"] == 21
        
        # 統計情報を確認
        stats = generator.get_stats()
        assert stats["serial_processed"] == 21
        assert stats["parallel_processed"] == 0
    
    @patch('src.controllers.parallel_comment_generator.run_comment_generation')
    def test_timeout_handling(self, mock_run_generation, generator, mock_weather_data):
        """タイムアウト処理のテスト"""
        def slow_generation(*args, **kwargs):
            time.sleep(10)  # タイムアウトを発生させる
            return {"final_comment": "遅いコメント"}
        
        mock_run_generation.side_effect = slow_generation
        
        # タイムアウトを短く設定
        generator.timeout_per_location = 0.1
        
        result = generator.generate_parallel(mock_weather_data)
        
        # タイムアウトエラーが記録されているか確認
        stats = generator.get_stats()
        assert stats["timeout_count"] > 0
    
    @patch('src.controllers.parallel_comment_generator.run_comment_generation')
    def test_error_handling(self, mock_run_generation, generator):
        """エラーハンドリングのテスト"""
        mock_run_generation.side_effect = Exception("生成エラー")
        
        error_data = {"エラー地点": {"data": "test"}}
        
        result = generator.generate_parallel(error_data)
        
        assert result["success_count"] == 0
        assert result["failed_count"] == 1
        assert result["results"][0]["success"] is False
        
        stats = generator.get_stats()
        assert stats["error_count"] == 1
    
    def test_thread_safety(self, generator):
        """スレッドセーフティのテスト"""
        # 複数スレッドから統計情報を更新
        def update_stats():
            with generator._lock:
                generator._stats["parallel_processed"] += 1
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=update_stats)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # RLockが正しく動作していることを確認
        assert generator._stats["parallel_processed"] == 10
    
    def test_progress_callback(self, generator):
        """進捗コールバックのテスト"""
        progress_calls = []
        
        def progress_callback(current, total, location):
            progress_calls.append((current, total, location))
        
        with patch('src.controllers.parallel_comment_generator.run_comment_generation') as mock_run:
            mock_run.return_value = {"final_comment": "テスト"}
            
            test_data = {"地点1": {"data": 1}, "地点2": {"data": 2}}
            
            generator.generate_parallel(
                test_data,
                progress_callback=progress_callback
            )
        
        # 進捗コールバックが呼ばれたことを確認
        assert len(progress_calls) == 2
        assert progress_calls[0][1] == 2  # total
        assert progress_calls[1][0] == 2  # current
    
    @pytest.mark.asyncio
    async def test_async_interface(self, generator):
        """非同期インターフェースのテスト"""
        with patch('src.controllers.parallel_comment_generator.run_comment_generation') as mock_run:
            mock_run.return_value = {"final_comment": "非同期テスト"}
            
            test_data = {"東京": {"data": "test"}}
            
            result = await generator.generate_parallel_async(test_data)
            
            assert isinstance(result, BatchGenerationResult)
            assert result["success_count"] == 1
    
    def test_empty_weather_data_handling(self, generator):
        """空の天気データの処理テスト"""
        empty_data = {
            "東京": None,
            "大阪": {"data": "valid"}
        }
        
        with patch('src.controllers.parallel_comment_generator.run_comment_generation') as mock_run:
            mock_run.return_value = {"final_comment": "テスト"}
            
            result = generator.generate_parallel(empty_data)
            
            assert result["total_count"] == 2
            assert result["success_count"] == 1
            assert result["failed_count"] == 1
            
            # 東京はエラー、大阪は成功
            tokyo_result = next(r for r in result["results"] if r["location"] == "東京")
            assert tokyo_result["success"] is False
            
            osaka_result = next(r for r in result["results"] if r["location"] == "大阪")
            assert osaka_result["success"] is True