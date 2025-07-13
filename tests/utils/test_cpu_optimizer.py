"""CPUOptimizerのテスト"""

import pytest
from unittest.mock import patch

from src.utils.cpu_optimizer import CPUOptimizer


class TestCPUOptimizer:
    """CPUOptimizerのテストクラス"""
    
    def test_get_optimal_workers_basic(self):
        """基本的な最適ワーカー数計算のテスト"""
        with patch('os.cpu_count', return_value=4):
            # デフォルト設定でCPU数と同じ
            assert CPUOptimizer.get_optimal_workers() == 4
            
            # タスク数が少ない場合
            assert CPUOptimizer.get_optimal_workers(task_count=2) == 2
            
            # 最小値の制約
            assert CPUOptimizer.get_optimal_workers(min_workers=6) == 6
            
            # 最大値の制約
            assert CPUOptimizer.get_optimal_workers(max_workers=2) == 2
    
    def test_get_optimal_workers_with_workers_per_core(self):
        """コアあたりワーカー数設定のテスト"""
        with patch('os.cpu_count', return_value=4):
            # 1.5倍のワーカー
            assert CPUOptimizer.get_optimal_workers(workers_per_core=1.5) == 6
            
            # 0.5倍のワーカー
            assert CPUOptimizer.get_optimal_workers(workers_per_core=0.5) == 2
    
    def test_get_optimal_workers_edge_cases(self):
        """エッジケースのテスト"""
        # CPU数が取得できない場合
        with patch('os.cpu_count', return_value=None):
            assert CPUOptimizer.get_optimal_workers() == 4  # デフォルト値
        
        # CPU数が0の場合（理論上ありえないが）
        # 実装では `os.cpu_count() or 4` なので、0でも4として扱われる
        with patch('os.cpu_count', return_value=0):
            assert CPUOptimizer.get_optimal_workers() == 4
    
    def test_get_io_bound_workers(self):
        """I/Oバウンドタスク用ワーカー数計算のテスト"""
        with patch('os.cpu_count', return_value=4):
            # デフォルトはCPU数の2倍
            assert CPUOptimizer.get_io_bound_workers() == 8
            
            # タスク数制約
            assert CPUOptimizer.get_io_bound_workers(task_count=5) == 5
            
            # 最大値制約（デフォルト16）
            with patch('os.cpu_count', return_value=10):
                assert CPUOptimizer.get_io_bound_workers() == 16
    
    def test_get_cpu_bound_workers(self):
        """CPUバウンドタスク用ワーカー数計算のテスト"""
        with patch('os.cpu_count', return_value=4):
            # デフォルトは(CPU数 - 予約コア数)
            assert CPUOptimizer.get_cpu_bound_workers() == 3
            
            # 予約コア数の変更
            assert CPUOptimizer.get_cpu_bound_workers(reserve_cores=2) == 2
            
            # 最小値は1
            assert CPUOptimizer.get_cpu_bound_workers(reserve_cores=10) == 1
    
    def test_task_count_constraint(self):
        """タスク数制約のテスト"""
        with patch('os.cpu_count', return_value=8):
            # 通常の計算
            assert CPUOptimizer.get_optimal_workers() == 8
            assert CPUOptimizer.get_io_bound_workers() == 16
            assert CPUOptimizer.get_cpu_bound_workers() == 7
            
            # タスク数が少ない場合、それ以上のワーカーは不要
            task_count = 3
            assert CPUOptimizer.get_optimal_workers(task_count=task_count) == 3
            assert CPUOptimizer.get_io_bound_workers(task_count=task_count) == 3
            assert CPUOptimizer.get_cpu_bound_workers(task_count=task_count) == 3
    
    def test_min_max_constraints(self):
        """最小値・最大値制約のテスト"""
        with patch('os.cpu_count', return_value=4):
            # 最小値制約
            assert CPUOptimizer.get_optimal_workers(min_workers=10) == 10
            assert CPUOptimizer.get_io_bound_workers(min_workers=10) == 10
            
            # 最大値制約
            assert CPUOptimizer.get_optimal_workers(max_workers=2) == 2
            assert CPUOptimizer.get_io_bound_workers(max_workers=5) == 5
            
            # 両方の制約（最小値が優先）
            assert CPUOptimizer.get_optimal_workers(
                min_workers=5, max_workers=3
            ) == 5
    
    @patch('src.utils.cpu_optimizer.logger')
    def test_logging(self, mock_logger):
        """ログ出力のテスト"""
        with patch('os.cpu_count', return_value=4):
            # 各メソッドでdebugログが出力される
            CPUOptimizer.get_optimal_workers(task_count=10)
            assert mock_logger.debug.called
            
            CPUOptimizer.get_io_bound_workers(task_count=5)
            assert mock_logger.debug.call_count >= 2
            
            CPUOptimizer.get_cpu_bound_workers()
            assert mock_logger.debug.call_count >= 3