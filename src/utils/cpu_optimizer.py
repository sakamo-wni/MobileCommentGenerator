"""CPU最適化ユーティリティ

並列処理のワーカー数を環境に応じて最適化する。
"""

from __future__ import annotations
import os
import logging

logger = logging.getLogger(__name__)


class CPUOptimizer:
    """CPU使用率を最適化するヘルパークラス"""
    
    # デフォルト設定
    DEFAULT_MIN_WORKERS = 1
    DEFAULT_MAX_WORKERS = 8
    DEFAULT_WORKERS_PER_CORE = 1.0  # CPUコアあたりのワーカー数
    
    @staticmethod
    def get_optimal_workers(
        task_count: int | None = None,
        min_workers: int = DEFAULT_MIN_WORKERS,
        max_workers: int = DEFAULT_MAX_WORKERS,
        workers_per_core: float = DEFAULT_WORKERS_PER_CORE
    ) -> int:
        """最適なワーカー数を計算
        
        Args:
            task_count: 処理するタスクの数（指定されている場合は考慮）
            min_workers: 最小ワーカー数
            max_workers: 最大ワーカー数
            workers_per_core: CPUコアあたりのワーカー数
            
        Returns:
            最適なワーカー数
        """
        # CPU数を取得
        cpu_count = os.cpu_count() or 4
        
        # 基本的なワーカー数を計算
        optimal_workers = int(cpu_count * workers_per_core)
        
        # タスク数が指定されている場合は、それ以上のワーカーは不要
        if task_count is not None:
            optimal_workers = min(optimal_workers, task_count)
        
        # 最小値と最大値の範囲内に収める
        optimal_workers = max(min_workers, min(optimal_workers, max_workers))
        
        logger.debug(
            f"Optimal workers calculated: {optimal_workers} "
            f"(CPU cores: {cpu_count}, task_count: {task_count})"
        )
        
        return optimal_workers
    
    @staticmethod
    def get_io_bound_workers(
        task_count: int | None = None,
        min_workers: int = DEFAULT_MIN_WORKERS,
        max_workers: int = 16
    ) -> int:
        """I/Oバウンドタスク用の最適なワーカー数を計算
        
        I/Oバウンドタスク（API呼び出し、ファイル読み込み等）では、
        CPUコア数より多くのワーカーを使用できる。
        
        Args:
            task_count: 処理するタスクの数
            min_workers: 最小ワーカー数
            max_workers: 最大ワーカー数
            
        Returns:
            最適なワーカー数
        """
        # I/Oバウンドタスクでは、CPUコア数の2-4倍程度が効率的
        cpu_count = os.cpu_count() or 4
        optimal_workers = cpu_count * 2
        
        # タスク数が指定されている場合は、それ以上のワーカーは不要
        if task_count is not None:
            optimal_workers = min(optimal_workers, task_count)
        
        # 最小値と最大値の範囲内に収める
        optimal_workers = max(min_workers, min(optimal_workers, max_workers))
        
        logger.debug(
            f"I/O bound workers calculated: {optimal_workers} "
            f"(CPU cores: {cpu_count}, task_count: {task_count})"
        )
        
        return optimal_workers
    
    @staticmethod
    def get_cpu_bound_workers(
        task_count: int | None = None,
        reserve_cores: int = 1
    ) -> int:
        """CPUバウンドタスク用の最適なワーカー数を計算
        
        CPUバウンドタスク（計算処理等）では、
        CPUコア数以下のワーカーを使用する。
        
        Args:
            task_count: 処理するタスクの数
            reserve_cores: システム用に予約するコア数
            
        Returns:
            最適なワーカー数
        """
        cpu_count = os.cpu_count() or 4
        
        # システム用にいくつかのコアを予約
        optimal_workers = max(1, cpu_count - reserve_cores)
        
        # タスク数が指定されている場合は、それ以上のワーカーは不要
        if task_count is not None:
            optimal_workers = min(optimal_workers, task_count)
        
        logger.debug(
            f"CPU bound workers calculated: {optimal_workers} "
            f"(CPU cores: {cpu_count}, reserved: {reserve_cores})"
        )
        
        return optimal_workers